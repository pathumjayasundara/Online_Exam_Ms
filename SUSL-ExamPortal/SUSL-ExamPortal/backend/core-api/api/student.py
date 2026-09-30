from datetime import datetime

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

import gpa
from database import get_db, grade_for_percentage
from auth_utils import require_auth
from lecturer_bridge import ensure_subject, push_result, sync_exams

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


def require_student(func):
    from functools import wraps

    @wraps(func)
    @require_auth
    def wrapper(*args, **kwargs):
        if g.current_user.get("role") != "student":
            return jsonify(success=False, message="Students only."), 403
        return func(*args, **kwargs)
    return wrapper


# ============================================================
# PROFILE
# ============================================================
@student_bp.get("/profile")
@require_student
def get_profile():
    u = g.current_user
    return jsonify({
        "name": u["full_name"], "studentId": u["student_id"], "registrationNo": u["registration_no"],
        "dob": u["date_of_birth"], "email": u["email"], "phone": u["phone"], "address": u["address"],
        "photoUrl": u["photo_url"],
        "degree": u["degree_programme"], "faculty": u["faculty"], "department": u["department"],
        "academicAdvisor": u["academic_advisor"], "yearLevel": u["year_level"],
    })


@student_bp.put("/profile")
@require_student
def update_profile():
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    fields, values = [], []
    for field in ("phone", "address", "email"):
        if data.get(field):
            fields.append(f"{field} = ?")
            values.append(data[field].strip())
    if fields:
        values.append(g.current_user["id"])
        db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
    return jsonify(message="Profile updated.")


@student_bp.post("/change-password")
@require_student
def change_password():
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    current_pw, new_pw = data.get("currentPassword", ""), data.get("newPassword", "")
    if not check_password_hash(g.current_user["password_hash"], current_pw):
        return jsonify(error="Current password is incorrect."), 400
    if len(new_pw) < 8:
        return jsonify(error="New password must be at least 8 characters."), 400
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
               (generate_password_hash(new_pw), g.current_user["id"]))
    db.commit()
    return jsonify(message="Password updated.")


# ============================================================
# SUBJECTS — enroll / unenroll
# ============================================================
@student_bp.get("/subjects")
@require_student
def list_subjects():
    db = get_db()
    semester = request.args.get("semester")
    query = "SELECT * FROM subjects"
    params = []
    if semester:
        query += " WHERE semester = ?"
        params.append(semester)
    rows = db.execute(query, params).fetchall()
    enrolled = {r["subject_code"] for r in db.execute(
        "SELECT subject_code FROM enrollments WHERE user_id = ?", (g.current_user["id"],)
    ).fetchall()}
    return jsonify([
        {"code": r["code"], "name": r["name"], "credits": r["credits"], "kind": r["kind"],
         "semester": r["semester"], "enrolled": r["code"] in enrolled}
        for r in rows
    ])


@student_bp.post("/subjects/<code>/enroll")
@require_student
def enroll_subject(code):
    db = get_db()
    subject = db.execute("SELECT * FROM subjects WHERE code = ?", (code,)).fetchone()
    if not subject:
        return jsonify(error="Subject not found."), 404
    if db.execute("SELECT id FROM enrollments WHERE user_id = ? AND subject_code = ?",
                  (g.current_user["id"], code)).fetchone():
        return jsonify(error="Already enrolled in this subject."), 409
    db.execute("INSERT INTO enrollments (user_id, subject_code) VALUES (?, ?)",
               (g.current_user["id"], code))
    db.commit()
    return jsonify(message=f"Successfully enrolled in {subject['name']}.")


@student_bp.delete("/subjects/<code>/enroll")
@require_student
def unenroll_subject(code):
    db = get_db()
    subject = db.execute("SELECT * FROM subjects WHERE code = ?", (code,)).fetchone()
    if not subject:
        return jsonify(error="Subject not found."), 404
    if str(subject["kind"]).startswith("Compulsory"):
        return jsonify(error="Compulsory subjects cannot be unenrolled."), 400
    row = db.execute("SELECT id FROM enrollments WHERE user_id = ? AND subject_code = ?",
                      (g.current_user["id"], code)).fetchone()
    if not row:
        return jsonify(error="You are not enrolled in this subject."), 404
    db.execute("DELETE FROM enrollments WHERE id = ?", (row["id"],))
    db.commit()
    return jsonify(message=f"Successfully unenrolled from {subject['name']}.")


# ============================================================
# ENROLMENTS — the Student portal pushes the subjects the student is taking
# ============================================================
@student_bp.put("/enrollments")
@require_student
def replace_enrollments():
    """Replace this student's enrolments with the given subject codes.
    Exams and quizzes are shown only for enrolled subjects."""
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    codes = data.get("codes")
    if not isinstance(codes, list) or len(codes) > 300:
        return jsonify(error="codes must be a list of subject codes."), 400
    wanted = {str(c).strip() for c in codes if str(c).strip()}
    valid = {c for c in wanted if ensure_subject(db, c)}
    uid = g.current_user["id"]
    have = {r["subject_code"] for r in db.execute(
        "SELECT subject_code FROM enrollments WHERE user_id = ?", (uid,)).fetchall()}
    for code in have - valid:
        db.execute("DELETE FROM enrollments WHERE user_id = ? AND subject_code = ?", (uid, code))
    for code in valid - have:
        db.execute("INSERT INTO enrollments (user_id, subject_code) VALUES (?, ?)", (uid, code))
    db.commit()
    return jsonify(enrolled=len(valid))


# ============================================================
# EXAMS / QUIZZES
# These come only from exams the lecturer has PUBLISHED in the Lecturer
# portal (see lecturer_bridge.py).  Nothing is seeded or made up here.
# ============================================================
def _has_submitted(db, user_id, exam_id):
    return db.execute(
        "SELECT 1 FROM attempts WHERE user_id = ? AND exam_id = ? AND submitted_at IS NOT NULL",
        (user_id, exam_id)).fetchone() is not None


def _exam_status(exam, completed=False):
    if completed:
        return "completed"
    # Lecturers enter times in local (server) time, so compare in local time.
    now = datetime.now()
    start, end = datetime.fromisoformat(exam["start_time"]), datetime.fromisoformat(exam["end_time"])
    if now < start:
        return "upcoming"
    if now > end:
        return "expired"
    return "available"


def _exam_json(db, exam, user_id):
    subject = db.execute("SELECT name FROM subjects WHERE code = ?", (exam["subject_code"],)).fetchone()
    total_questions = db.execute(
        "SELECT COUNT(*) AS n FROM questions WHERE exam_id = ?", (exam["id"],)
    ).fetchone()["n"]
    return {
        "id": exam["id"], "type": exam["exam_type"], "title": exam["title"],
        "subject": subject["name"] if subject else exam["subject_code"], "code": exam["subject_code"],
        "duration": exam["duration_minutes"], "totalQuestions": total_questions,
        "totalMarks": exam["total_marks"], "start": exam["start_time"],
        "end": exam["end_time"],
        "status": _exam_status(exam, _has_submitted(db, user_id, exam["id"])),
    }


def _student_exam(db, exam_id):
    """The exam, if it is published and the student is enrolled in its subject."""
    exam = db.execute("SELECT * FROM exams WHERE id = ? AND active = 1", (exam_id,)).fetchone()
    if not exam:
        return None
    if not db.execute("SELECT 1 FROM enrollments WHERE user_id = ? AND subject_code = ?",
                      (g.current_user["id"], exam["subject_code"])).fetchone():
        return None
    return exam


def _open_attempt(db, user_id, exam_id):
    return db.execute(
        "SELECT * FROM attempts WHERE user_id = ? AND exam_id = ? AND submitted_at IS NULL",
        (user_id, exam_id)).fetchone()


def _seconds_left(exam, attempt):
    started = datetime.fromisoformat(attempt["started_at"].replace(" ", "T"))
    return exam["duration_minutes"] * 60 - (datetime.utcnow() - started).total_seconds()


@student_bp.get("/exams")
@require_student
def list_exams():
    db = get_db()
    sync_exams(db)
    exams = db.execute(
        """
        SELECT e.* FROM exams e
        WHERE e.active = 1
          AND e.subject_code IN (SELECT subject_code FROM enrollments WHERE user_id = ?)
        ORDER BY e.start_time
        """, (g.current_user["id"],)).fetchall()
    return jsonify([_exam_json(db, e, g.current_user["id"]) for e in exams])


@student_bp.get("/exams/<int:exam_id>")
@require_student
def exam_details(exam_id):
    db = get_db()
    sync_exams(db)
    exam = _student_exam(db, exam_id)
    if not exam:
        return jsonify(error="Exam not found."), 404
    return jsonify(_exam_json(db, exam, g.current_user["id"]))


@student_bp.post("/exams/<int:exam_id>/start")
@require_student
def start_exam(exam_id):
    """Begin (or resume) the attempt. The clock starts here, on the server, and
    the questions are only ever sent from this endpoint - never the answers."""
    db = get_db()
    sync_exams(db)
    user_id = g.current_user["id"]
    exam = _student_exam(db, exam_id)
    if not exam:
        return jsonify(error="Exam not found."), 404
    if _has_submitted(db, user_id, exam_id):
        return jsonify(error="You have already submitted this."), 409

    attempt = _open_attempt(db, user_id, exam_id)
    if attempt is None:
        if _exam_status(exam) != "available":
            return jsonify(error="This is not currently open."), 403
        cur = db.execute("INSERT INTO attempts (user_id, exam_id, started_at) VALUES (?, ?, ?)",
                         (user_id, exam_id, datetime.utcnow().isoformat(sep=" ", timespec="seconds")))
        attempt = db.execute("SELECT * FROM attempts WHERE id = ?", (cur.lastrowid,)).fetchone()
        db.commit()

    left = _seconds_left(exam, attempt)
    if left <= 0:
        result = _mark_attempt(db, exam, attempt, g.current_user)
        return jsonify(error="Time is up - your answers were submitted automatically.",
                       result=result), 410

    questions = []
    for q in db.execute("SELECT * FROM questions WHERE exam_id = ? ORDER BY id", (exam_id,)).fetchall():
        options = db.execute("SELECT option_key, text FROM options WHERE question_id = ? ORDER BY option_key",
                             (q["id"],)).fetchall()
        questions.append({"id": q["id"], "text": q["text"],
                          "options": [{"key": o["option_key"], "text": o["text"]} for o in options]})
    saved = {a["question_id"]: a["selected_key"] for a in db.execute(
        "SELECT question_id, selected_key FROM answers WHERE attempt_id = ?", (attempt["id"],)).fetchall()}
    payload = _exam_json(db, exam, user_id)
    payload.update(questions=questions, savedAnswers=saved, secondsLeft=int(left))
    return jsonify(payload)


@student_bp.post("/exams/<int:exam_id>/answers")
@require_student
def save_answer(exam_id):
    """Autosave one answer during the attempt (Save & Next)."""
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    exam = _student_exam(db, exam_id)
    if not exam:
        return jsonify(error="Exam not found."), 404
    attempt = _open_attempt(db, g.current_user["id"], exam_id)
    if attempt is None:
        return jsonify(error="Start the exam first."), 400
    if _seconds_left(exam, attempt) < -30:  # small grace for network delay
        return jsonify(error="Time is up."), 403

    question_id, key = data.get("questionId"), data.get("optionKey")
    if not db.execute(
            "SELECT 1 FROM questions q JOIN options o ON o.question_id = q.id "
            "WHERE q.id = ? AND q.exam_id = ? AND o.option_key = ?",
            (question_id, exam_id, key)).fetchone():
        return jsonify(error="Invalid question or option."), 400

    existing = db.execute("SELECT id FROM answers WHERE attempt_id = ? AND question_id = ?",
                          (attempt["id"], question_id)).fetchone()
    if existing:
        db.execute("UPDATE answers SET selected_key = ? WHERE id = ?", (key, existing["id"]))
    else:
        db.execute("INSERT INTO answers (attempt_id, question_id, selected_key) VALUES (?, ?, ?)",
                   (attempt["id"], question_id, key))
    db.commit()
    return jsonify(saved=True)


def _mark_attempt(db, exam, attempt, user):
    """Server-side marking - the ONLY place correct answers are ever read."""
    questions = db.execute("SELECT * FROM questions WHERE exam_id = ?", (exam["id"],)).fetchall()
    given = {a["question_id"]: a["selected_key"] for a in db.execute(
        "SELECT question_id, selected_key FROM answers WHERE attempt_id = ?", (attempt["id"],)
    ).fetchall()}

    correct = incorrect = 0
    score = 0.0
    for q in questions:
        if q["id"] not in given:
            continue
        correct_option = db.execute(
            "SELECT option_key FROM options WHERE question_id = ? AND is_correct = 1", (q["id"],)
        ).fetchone()
        if correct_option and given[q["id"]] == correct_option["option_key"]:
            correct += 1
            score += q["marks"]
        else:
            incorrect += 1

    unanswered = len(questions) - correct - incorrect
    total = exam["total_marks"]
    score = round(score, 2)
    percentage = round((score / total) * 100) if total else 0
    g_ = grade_for_percentage(percentage)
    status = "Passed" if g_["grade"] != "E" else "Failed"

    db.execute(
        """
        UPDATE attempts SET submitted_at = ?, score = ?, total = ?, correct_count = ?,
            incorrect_count = ?, unanswered_count = ?, grade = ?, status = ?
        WHERE id = ?
        """,
        (datetime.utcnow().isoformat(), score, total, correct, incorrect,
         unanswered, g_["grade"], status, attempt["id"]),
    )
    db.commit()
    # let the lecturer see it on their Results page
    push_result(exam["source_id"], user["id"], user["full_name"], score, total)

    return dict(score=score, total=total, percentage=percentage, grade=g_["grade"],
                gradePoint=g_["point"], correct=correct, incorrect=incorrect,
                unanswered=unanswered, status=status)


@student_bp.post("/exams/<int:exam_id>/submit")
@require_student
def submit_exam(exam_id):
    db = get_db()
    exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if not exam:
        return jsonify(error="Exam not found."), 404
    attempt = _open_attempt(db, g.current_user["id"], exam_id)
    if not attempt:
        return jsonify(error="No active attempt to submit."), 400
    return jsonify(_mark_attempt(db, exam, attempt, g.current_user))


@student_bp.get("/results")
@require_student
def exam_attempt_history():
    """'My Exams' — attempt history, distinct from the official result sheet below."""
    db = get_db()
    rows = db.execute(
        """
        SELECT a.*, e.title AS exam_title, e.exam_type AS exam_type, s.name AS subject_name
        FROM attempts a
        JOIN exams e ON e.id = a.exam_id
        JOIN subjects s ON s.code = e.subject_code
        WHERE a.user_id = ? AND a.submitted_at IS NOT NULL
        ORDER BY a.submitted_at DESC
        """,
        (g.current_user["id"],),
    ).fetchall()
    return jsonify([{
        "id": r["id"], "title": r["exam_title"], "type": r["exam_type"], "subject": r["subject_name"],
        "date": r["submitted_at"][:10] if r["submitted_at"] else None,
        "score": r["score"], "total": r["total"],
        "percentage": round((r["score"] / r["total"]) * 100) if r["total"] else 0,
        "grade": r["grade"], "status": r["status"],
        "correct": r["correct_count"] or 0, "incorrect": r["incorrect_count"] or 0,
        "unanswered": r["unanswered_count"] or 0,
    } for r in rows])


# ============================================================
# MY RESULTS — official result sheet + GPA
# ============================================================
@student_bp.get("/results/sheet")
@require_student
def results_sheet():
    """Only PUBLISHED course_results rows are ever returned — an admin must
    publish a semester's results before the student can see them."""
    db = get_db()
    user_id = g.current_user["id"]
    semester = request.args.get("semester")
    if not semester:
        return jsonify(error="semester query param is required."), 400

    rows = db.execute(
        """
        SELECT cr.*, s.name AS subject_name, s.credits AS credits, s.kind AS kind
        FROM course_results cr
        JOIN subjects s ON s.code = cr.subject_code
        WHERE cr.user_id = ? AND cr.semester = ? AND cr.published = 1
        """,
        (user_id, semester),
    ).fetchall()

    if not rows:
        return jsonify(published=False, rows=[], semesterGpa=None,
                        message="No results have been published yet.")

    return jsonify(published=True, semesterGpa=gpa.get_semester_gpa(db, user_id, semester), rows=[
        {"subjectCode": r["subject_code"], "subjectName": r["subject_name"], "credits": r["credits"],
         "kind": r["kind"], "grade": r["grade"], "gradePoint": r["grade_point"]}
        for r in rows
    ])


@student_bp.get("/results/summary")
@require_student
def results_summary():
    """Overall GPA for the dashboard card and the top of My Results."""
    db = get_db()
    return jsonify(gpa.get_overall_gpa(db, g.current_user["id"]))
