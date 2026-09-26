from datetime import datetime

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

import gpa
from database import get_db, grade_for_percentage
from auth_utils import require_auth

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
# EXAMS / QUIZZES
# ============================================================
def _exam_status(exam):
    now = datetime.utcnow()
    start, end = datetime.fromisoformat(exam["start_time"]), datetime.fromisoformat(exam["end_time"])
    if now < start:
        return "upcoming"
    if now > end:
        return "expired"
    return "available"


def _exam_json(db, exam):
    subject = db.execute("SELECT name FROM subjects WHERE code = ?", (exam["subject_code"],)).fetchone()
    total_questions = db.execute(
        "SELECT COUNT(*) AS n FROM questions WHERE exam_id = ?", (exam["id"],)
    ).fetchone()["n"]
    return {
        "id": exam["id"], "type": exam["exam_type"], "title": exam["title"],
        "subject": subject["name"] if subject else exam["subject_code"], "code": exam["subject_code"],
        "duration": exam["duration_minutes"], "totalQuestions": total_questions,
        "totalMarks": exam["total_marks"], "start": exam["start_time"],
        "end": exam["end_time"], "status": _exam_status(exam),
    }


@student_bp.get("/exams")
@require_student
def list_exams():
    db = get_db()
    codes = [r["subject_code"] for r in db.execute(
        "SELECT subject_code FROM enrollments WHERE user_id = ?", (g.current_user["id"],)
    ).fetchall()]
    if not codes:
        return jsonify([])
    placeholders = ",".join("?" for _ in codes)
    exams = db.execute(f"SELECT * FROM exams WHERE subject_code IN ({placeholders})", codes).fetchall()
    return jsonify([_exam_json(db, e) for e in exams])


@student_bp.get("/exams/<int:exam_id>")
@require_student
def exam_details(exam_id):
    db = get_db()
    exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if not exam:
        return jsonify(error="Exam not found."), 404
    payload = _exam_json(db, exam)
    if payload["status"] == "available":
        questions = db.execute("SELECT * FROM questions WHERE exam_id = ?", (exam_id,)).fetchall()
        payload["questions"] = []
        for q in questions:
            options = db.execute(
                "SELECT option_key, text FROM options WHERE question_id = ?", (q["id"],)
            ).fetchall()
            payload["questions"].append({
                "id": q["id"], "text": q["text"],
                "options": [{"key": o["option_key"], "text": o["text"]} for o in options],
            })
    return jsonify(payload)


@student_bp.post("/exams/<int:exam_id>/answers")
@require_student
def save_answer(exam_id):
    """Autosave one answer during the attempt (Save & Next)."""
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    user_id = g.current_user["id"]

    attempt = db.execute(
        "SELECT * FROM attempts WHERE user_id = ? AND exam_id = ? AND submitted_at IS NULL",
        (user_id, exam_id),
    ).fetchone()
    if not attempt:
        cur = db.execute("INSERT INTO attempts (user_id, exam_id) VALUES (?, ?)", (user_id, exam_id))
        attempt_id = cur.lastrowid
    else:
        attempt_id = attempt["id"]

    existing = db.execute(
        "SELECT id FROM answers WHERE attempt_id = ? AND question_id = ?",
        (attempt_id, data.get("questionId")),
    ).fetchone()
    if existing:
        db.execute("UPDATE answers SET selected_key = ? WHERE id = ?",
                   (data.get("optionKey"), existing["id"]))
    else:
        db.execute("INSERT INTO answers (attempt_id, question_id, selected_key) VALUES (?, ?, ?)",
                   (attempt_id, data.get("questionId"), data.get("optionKey")))
    db.commit()
    return jsonify(saved=True)


@student_bp.post("/exams/<int:exam_id>/submit")
@require_student
def submit_exam(exam_id):
    """Server-side marking — the ONLY place correct answers are ever read."""
    db = get_db()
    user_id = g.current_user["id"]

    exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if not exam:
        return jsonify(error="Exam not found."), 404
    attempt = db.execute(
        "SELECT * FROM attempts WHERE user_id = ? AND exam_id = ? AND submitted_at IS NULL",
        (user_id, exam_id),
    ).fetchone()
    if not attempt:
        return jsonify(error="No active attempt to submit."), 400

    questions = db.execute("SELECT * FROM questions WHERE exam_id = ?", (exam_id,)).fetchall()
    given = {a["question_id"]: a["selected_key"] for a in db.execute(
        "SELECT question_id, selected_key FROM answers WHERE attempt_id = ?", (attempt["id"],)
    ).fetchall()}

    marks_per_q = exam["total_marks"] / len(questions) if questions else 0
    correct = incorrect = 0
    for q in questions:
        if q["id"] not in given:
            continue
        correct_option = db.execute(
            "SELECT option_key FROM options WHERE question_id = ? AND is_correct = 1", (q["id"],)
        ).fetchone()
        if correct_option and given[q["id"]] == correct_option["option_key"]:
            correct += 1
        else:
            incorrect += 1

    unanswered = len(questions) - correct - incorrect
    score = round(correct * marks_per_q, 2)
    percentage = round((score / exam["total_marks"]) * 100) if exam["total_marks"] else 0
    g_ = grade_for_percentage(percentage)
    status = "Passed" if g_["grade"] != "E" else "Failed"

    db.execute(
        """
        UPDATE attempts SET submitted_at = ?, score = ?, total = ?, correct_count = ?,
            incorrect_count = ?, unanswered_count = ?, grade = ?, status = ?
        WHERE id = ?
        """,
        (datetime.utcnow().isoformat(), score, exam["total_marks"], correct, incorrect,
         unanswered, g_["grade"], status, attempt["id"]),
    )
    db.commit()

    return jsonify(score=score, total=exam["total_marks"], percentage=percentage, grade=g_["grade"],
                    correct=correct, incorrect=incorrect, unanswered=unanswered, status=status)


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
