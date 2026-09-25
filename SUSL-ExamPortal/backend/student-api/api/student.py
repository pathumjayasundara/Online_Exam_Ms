"""
Team 02 — Student Module API. Every route is JWT-protected and resolves
"the current student" from the token identity (get_jwt_identity()) — never
from a client-supplied id. This is what makes every response dynamic per
logged-in student instead of one hard-coded profile for everyone.
"""
import os
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import gpa
from extensions import db
from models import Attempt, Answer, CourseResult, Enrollment, Exam, Option, Question, Subject, User

student_bp = Blueprint("student", __name__, url_prefix="/api/student")

ALLOWED_PHOTO_EXT = {"png", "jpg", "jpeg", "webp"}


def current_user():
    return User.query.get_or_404(get_jwt_identity())


# ============================================================
# PROFILE  (dashboard req. #7, #8, #9 — dynamic, authenticated, no hard-coding)
# ============================================================
@student_bp.get("/profile")
@jwt_required()
def get_profile():
    u = current_user()
    return jsonify({
        "name": u.full_name, "studentId": u.student_id, "registrationNo": u.registration_no,
        "dob": u.date_of_birth.isoformat() if u.date_of_birth else None,
        "email": u.email, "phone": u.phone, "address": u.address,
        "photoUrl": u.photo_url,  # null -> frontend shows an initials placeholder, never a random photo
        "degree": u.degree_programme, "faculty": u.faculty, "department": u.department,
        "academicAdvisor": u.academic_advisor,
    })


@student_bp.put("/profile")
@jwt_required()
def update_profile():
    u = current_user()
    data = request.get_json(force=True) or {}
    for field, attr in (("phone", "phone"), ("address", "address"), ("email", "email")):
        if data.get(field):
            setattr(u, attr, data[field].strip())
    db.session.commit()
    return jsonify(message="Profile updated.")


@student_bp.post("/profile/photo")
@jwt_required()
def upload_profile_photo():
    u = current_user()
    file = request.files.get("photo")
    if not file or "." not in file.filename:
        return jsonify(error="No photo file provided."), 400
    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_PHOTO_EXT:
        return jsonify(error="Unsupported image type."), 400

    filename = secure_filename(f"{u.student_id}_{uuid.uuid4().hex[:8]}.{ext}")
    upload_dir = os.path.join(current_app.static_folder, "uploads", "profile_photos")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    u.photo_url = f"/static/uploads/profile_photos/{filename}"
    db.session.commit()
    return jsonify(photoUrl=u.photo_url)


@student_bp.post("/change-password")
@jwt_required()
def change_password():
    u = current_user()
    data = request.get_json(force=True) or {}
    current_pw, new_pw = data.get("currentPassword", ""), data.get("newPassword", "")
    if not check_password_hash(u.password_hash, current_pw):
        return jsonify(error="Current password is incorrect."), 400
    if len(new_pw) < 8:
        return jsonify(error="New password must be at least 8 characters."), 400
    u.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify(message="Password updated.")


# ============================================================
# SUBJECTS — enroll / unenroll (req. #5, #6)
# ============================================================
@student_bp.get("/subjects")
@jwt_required()
def list_subjects():
    semester = request.args.get("semester")
    q = Subject.query
    if semester:
        q = q.filter_by(semester=semester)
    enrolled_codes = {e.subject_code for e in Enrollment.query.filter_by(user_id=get_jwt_identity())}
    return jsonify([
        {"code": s.code, "name": s.name, "credits": s.credits, "kind": s.kind,
         "semester": s.semester, "enrolled": s.code in enrolled_codes}
        for s in q.all()
    ])


@student_bp.post("/subjects/<code>/enroll")
@jwt_required()
def enroll_subject(code):
    subject = Subject.query.get_or_404(code)
    user_id = get_jwt_identity()
    if Enrollment.query.filter_by(user_id=user_id, subject_code=code).first():
        return jsonify(error="Already enrolled in this subject."), 409  # no duplicate enrollments
    db.session.add(Enrollment(user_id=user_id, subject_code=code))
    db.session.commit()
    return jsonify(message=f"Successfully enrolled in {subject.name}.")


@student_bp.delete("/subjects/<code>/enroll")
@jwt_required()
def unenroll_subject(code):
    subject = Subject.query.get_or_404(code)
    if subject.kind.startswith("Compulsory"):
        return jsonify(error="Compulsory subjects cannot be unenrolled."), 400
    enrollment = Enrollment.query.filter_by(user_id=get_jwt_identity(), subject_code=code).first()
    if not enrollment:
        return jsonify(error="You are not enrolled in this subject."), 404
    db.session.delete(enrollment)
    db.session.commit()
    return jsonify(message=f"Successfully unenrolled from {subject.name}.")


# ============================================================
# EXAMS / QUIZZES
# ============================================================
def _exam_status(exam):
    now = datetime.utcnow()
    if now < exam.start_time:
        return "upcoming"
    if now > exam.end_time:
        return "expired"
    return "available"


def _exam_json(exam):
    return {
        "id": exam.id, "type": exam.exam_type, "title": exam.title,
        "subject": exam.subject.name, "code": exam.subject_code,
        "duration": exam.duration_minutes, "totalQuestions": len(exam.questions),
        "totalMarks": exam.total_marks, "start": exam.start_time.isoformat(),
        "end": exam.end_time.isoformat(), "status": _exam_status(exam),
    }


@student_bp.get("/exams")
@jwt_required()
def list_exams():
    enrolled_codes = {e.subject_code for e in Enrollment.query.filter_by(user_id=get_jwt_identity())}
    exams = Exam.query.filter(Exam.subject_code.in_(enrolled_codes)).all() if enrolled_codes else []
    return jsonify([_exam_json(e) for e in exams])


@student_bp.get("/exams/<int:exam_id>")
@jwt_required()
def exam_details(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    payload = _exam_json(exam)
    # Only include questions/options once the exam is actually available —
    # and NEVER include is_correct here.
    if payload["status"] == "available":
        payload["questions"] = [
            {"id": q.id, "text": q.text,
             "options": [{"key": o.option_key, "text": o.text} for o in q.options]}
            for q in exam.questions
        ]
    return jsonify(payload)


@student_bp.post("/exams/<int:exam_id>/answers")
@jwt_required()
def save_answer(exam_id):
    """Autosave one answer during the attempt (Save & Next)."""
    data = request.get_json(force=True) or {}
    user_id = get_jwt_identity()
    attempt = Attempt.query.filter_by(user_id=user_id, exam_id=exam_id, submitted_at=None).first()
    if not attempt:
        attempt = Attempt(user_id=user_id, exam_id=exam_id)
        db.session.add(attempt)
        db.session.flush()

    answer = Answer.query.filter_by(attempt_id=attempt.id, question_id=data["questionId"]).first()
    if answer:
        answer.selected_key = data["optionKey"]
    else:
        db.session.add(Answer(attempt_id=attempt.id, question_id=data["questionId"], selected_key=data["optionKey"]))
    db.session.commit()
    return jsonify(saved=True)


@student_bp.post("/exams/<int:exam_id>/submit")
@jwt_required()
def submit_exam(exam_id):
    """
    Server-side marking — the ONLY place correct answers are ever read.
    Never trust a score computed on the client.
    """
    user_id = get_jwt_identity()
    exam = Exam.query.get_or_404(exam_id)
    attempt = Attempt.query.filter_by(user_id=user_id, exam_id=exam_id, submitted_at=None).first()
    if not attempt:
        return jsonify(error="No active attempt to submit."), 400

    questions = exam.questions
    marks_per_q = exam.total_marks / len(questions) if questions else 0
    correct = incorrect = 0
    given = {a.question_id: a.selected_key for a in attempt.answers}

    for q in questions:
        if q.id not in given:
            continue
        correct_option = next((o for o in q.options if o.is_correct), None)
        if correct_option and given[q.id] == correct_option.option_key:
            correct += 1
        else:
            incorrect += 1

    unanswered = len(questions) - correct - incorrect
    score = round(correct * marks_per_q, 2)
    percentage = round((score / exam.total_marks) * 100) if exam.total_marks else 0
    g = gpa_scale_lookup(percentage)

    attempt.submitted_at = datetime.utcnow()
    attempt.score, attempt.total = score, exam.total_marks
    attempt.correct_count, attempt.incorrect_count, attempt.unanswered_count = correct, incorrect, unanswered
    attempt.grade = g["grade"]
    attempt.status = "Passed" if g["grade"] != "E" else "Failed"
    db.session.commit()

    return jsonify(score=score, total=exam.total_marks, percentage=percentage, grade=g["grade"],
                    correct=correct, incorrect=incorrect, unanswered=unanswered, status=attempt.status)


GRADE_SCALE = [
    {"min": 90, "grade": "A+"}, {"min": 80, "grade": "A"}, {"min": 75, "grade": "A-"},
    {"min": 70, "grade": "B+"}, {"min": 65, "grade": "B"}, {"min": 60, "grade": "B-"},
    {"min": 55, "grade": "C+"}, {"min": 50, "grade": "C"}, {"min": 45, "grade": "C-"},
    {"min": 40, "grade": "D+"}, {"min": 30, "grade": "D"}, {"min": 0, "grade": "E"},
]


def gpa_scale_lookup(percentage):
    return next(g for g in GRADE_SCALE if percentage >= g["min"])


@student_bp.get("/results")
@jwt_required()
def exam_attempt_history():
    """'My Exams' — attempt history, distinct from the official result sheet below."""
    attempts = Attempt.query.filter_by(user_id=get_jwt_identity()).filter(Attempt.submitted_at.isnot(None)).all()
    return jsonify([{
        "id": a.id, "title": a.exam.title, "type": a.exam.exam_type, "subject": a.exam.subject.name,
        "date": a.submitted_at.date().isoformat(), "score": a.score, "total": a.total,
        "percentage": round((a.score / a.total) * 100) if a.total else 0,
        "grade": a.grade, "status": a.status,
    } for a in attempts])


# ============================================================
# MY RESULTS — official result sheet + GPA (req. #1, #2, #3)
# ============================================================
@student_bp.get("/results/sheet")
@jwt_required()
def results_sheet():
    """
    Only PUBLISHED CourseResult rows are ever returned — an admin/lecturer
    must publish a semester's results before the student can see them.
    """
    user_id = get_jwt_identity()
    semester = request.args.get("semester")
    if not semester:
        return jsonify(error="semester query param is required."), 400

    rows = (
        CourseResult.query.filter_by(user_id=user_id, semester=semester, published=True).all()
    )
    if not rows:
        return jsonify(published=False, rows=[], semesterGpa=None,
                        message="No results have been published yet.")

    return jsonify(published=True, semesterGpa=gpa.get_semester_gpa(user_id, semester), rows=[
        {"subjectCode": r.subject_code, "subjectName": r.subject.name, "credits": r.subject.credits,
         "kind": r.subject.kind, "grade": r.grade, "gradePoint": r.grade_point}
        for r in rows
    ])


@student_bp.get("/results/summary")
@jwt_required()
def results_summary():
    """Overall GPA for the dashboard card and the top of My Results."""
    return jsonify(gpa.get_overall_gpa(get_jwt_identity()))
