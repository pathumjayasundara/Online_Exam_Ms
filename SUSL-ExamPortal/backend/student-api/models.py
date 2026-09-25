"""
Database models — Team 02 Student Module.

These are scoped to what the Student Module needs. `users` and `subjects`
are shared tables (Team 01 / Team 03 also read/write them) — if those teams
already have migrations for `users` / `subjects`, reconcile field names
with theirs rather than creating a second copy of either table.
"""
from datetime import datetime
from extensions import db


class User(db.Model):
    """Shared `users` table — admin / lecturer / student all live here."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, default="student")  # admin | lecturer | student
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=False)  # False until email token confirmed

    # --- student-specific fields (null for admin/lecturer rows) ---
    student_id = db.Column(db.String(20), unique=True, nullable=True)   # e.g. 22APP5678
    registration_no = db.Column(db.String(30), nullable=True)           # e.g. 2022/CST/078
    date_of_birth = db.Column(db.Date, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)                # null -> frontend shows initials
    degree_programme = db.Column(db.String(150), nullable=True)
    faculty = db.Column(db.String(150), nullable=True)
    department = db.Column(db.String(150), nullable=True)
    academic_advisor = db.Column(db.String(120), nullable=True)
    intake_year = db.Column(db.String(4), nullable=True)
    programme_code = db.Column(db.String(10), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollments = db.relationship("Enrollment", backref="student", lazy=True, cascade="all, delete-orphan")
    attempts = db.relationship("Attempt", backref="student", lazy=True, cascade="all, delete-orphan")
    course_results = db.relationship("CourseResult", backref="student", lazy=True, cascade="all, delete-orphan")


class EmailVerification(db.Model):
    """Registration email-confirmation tokens (POST /api/auth/register / /verify)."""
    __tablename__ = "email_verifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    consumed = db.Column(db.Boolean, default=False)


class Subject(db.Model):
    """Course catalogue — seeded from the official curriculum handbook (see seed_subjects.py)."""
    __tablename__ = "subjects"

    code = db.Column(db.String(20), primary_key=True)  # e.g. "PST 31224"
    name = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(40), nullable=False)     # "Compulsory" | "Elective" | "Compulsory (Non-GPA)"
    semester = db.Column(db.String(10), nullable=False)  # "y1s1".."y4s2"

    @property
    def is_gpa_counted(self):
        return "Non-GPA" not in self.kind


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (db.UniqueConstraint("user_id", "subject_code", name="uq_enrollment"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_code = db.Column(db.String(20), db.ForeignKey("subjects.code"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship("Subject")


class Exam(db.Model):
    """A formal exam or quiz (`exam_type` distinguishes them; both share the same engine)."""
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    exam_type = db.Column(db.String(10), nullable=False, default="exam")  # "exam" | "quiz"
    subject_code = db.Column(db.String(20), db.ForeignKey("subjects.code"), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    subject = db.relationship("Subject")
    questions = db.relationship("Question", backref="exam", lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Float, nullable=False, default=1.0)

    options = db.relationship("Option", backref="question", lazy=True, cascade="all, delete-orphan")


class Option(db.Model):
    __tablename__ = "options"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    option_key = db.Column(db.String(1), nullable=False)  # "A".."D"
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    # `is_correct` is NEVER serialised to the student — see api/student.py
    # get_questions_public(). Marking reads it directly from the DB on submit.


class Attempt(db.Model):
    """One exam/quiz attempt by a student — feeds 'My Exams' history, NOT the official transcript."""
    __tablename__ = "attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, nullable=True)
    total = db.Column(db.Float, nullable=True)
    correct_count = db.Column(db.Integer, nullable=True)
    incorrect_count = db.Column(db.Integer, nullable=True)
    unanswered_count = db.Column(db.Integer, nullable=True)
    grade = db.Column(db.String(2), nullable=True)
    status = db.Column(db.String(10), nullable=True)  # "Passed" | "Failed"

    exam = db.relationship("Exam")
    answers = db.relationship("Answer", backref="attempt", lazy=True, cascade="all, delete-orphan")


class Answer(db.Model):
    __tablename__ = "answers"
    __table_args__ = (db.UniqueConstraint("attempt_id", "question_id", name="uq_answer"),)

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    selected_key = db.Column(db.String(1), nullable=False)


class CourseResult(db.Model):
    """
    The OFFICIAL per-course result for a semester — this is what powers the
    result sheet and GPA, and is entirely separate from `Attempt` (which is
    just exam-taking history). Written by the lecturer/admin module, only
    ever READ here. `published=False` rows must never be returned to the
    student (see api/student.py get_results_sheet).
    """
    __tablename__ = "course_results"
    __table_args__ = (db.UniqueConstraint("user_id", "subject_code", "semester", name="uq_course_result"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_code = db.Column(db.String(20), db.ForeignKey("subjects.code"), nullable=False)
    semester = db.Column(db.String(10), nullable=False)  # "y1s1".."y4s2"
    grade = db.Column(db.String(2), nullable=False)       # "A+".."E"
    grade_point = db.Column(db.Float, nullable=False)
    published = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)

    subject = db.relationship("Subject")
