import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from flask import g
from werkzeug.security import generate_password_hash, check_password_hash

from subjects_catalog import SUBJECTS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "exam_portal.db"

ADMIN_EMAIL = "admin@sab.ac.lk"
ADMIN_PASSWORD = "Admin@SUSL2026"

DEMO_STUDENT = {
    "email": "nimasha.perera@std.sab.ac.lk",
    "password": "Student@2026",
    "name": "W.A. Nimasha Perera",
    "student_id": "22APP5678",
}

DEMO_LECTURERS = [
    ("Dr. A. Perera", "aperera@sab.ac.lk", "Computing", 4),
    ("Ms. N. Fernando", "nfernando@sab.ac.lk", "Computing", 3),
    ("Mr. K. Jayasinghe", "kjayasinghe@sab.ac.lk", "Information Systems", 5),
    ("Dr. S. Bandara", "sbandara@sab.ac.lk", "Computing", 4),
]

DEMO_STUDENTS = [
    ("Kavindu Silva", "SUSL/CS/24/018", "kavindu@std.sab.ac.lk", "Computer Science", "2"),
    ("Tharushi Fernando", "SUSL/IT/23/042", "tharushi@std.sab.ac.lk", "Information Technology", "3"),
    ("Sahan Wijesinghe", "SUSL/CS/25/081", "sahan@std.sab.ac.lk", "Computer Science", "1"),
    ("Dilki Senanayake", "SUSL/IT/24/055", "dilki@std.sab.ac.lk", "Information Technology", "2"),
]

ADMIN_EXAMS = [
    ("Software Engineering - Mid Term", "PST 22208", "2026-09-25", "90 minutes", 124, "Scheduled"),
    ("Database Management Systems", "PST 31229", "2026-09-28", "120 minutes", 118, "Live"),
    ("Operating Systems - Final", "PST 22211", "2026-10-02", "120 minutes", 125, "Completed"),
    ("Computer Networks", "PST 41229", "2026-10-07", "90 minutes", 106, "Scheduled"),
    ("Information Systems", "PST 22218", "2026-10-10", "60 minutes", 94, "Scheduled"),
]

ADMIN_QUESTIONS = [
    ("Q00186", "What is the primary purpose of an operating system?", "Operating Systems", "Multiple Choice", 2),
    ("Q00185", "Explain the difference between primary and foreign keys.", "Database Systems", "Short Answer", 5),
    ("Q00184", "Which software development model uses iterative development?", "Software Engineering", "Multiple Choice", 2),
]

ADMIN_RESULTS = [
    ("Database Systems - Mid Term", "PST 31229", 112, 112, "Published"),
    ("Software Engineering - Quiz 02", "PST 22208", 98, 86, "Pending"),
    ("Operating Systems - Final", "PST 22211", 125, 125, "Published"),
]

# One real, gradable exam — matches the "AI & Expert Systems" entry already
# hard-coded in the student portal's front-end (student/index.html), so the
# demo student can take exam id 1 and exercise the real submit/grade pipeline.
DEMO_EXAM_QUESTIONS = [
    ("Which search strategy is guaranteed to find the shallowest goal node first?",
     [("A", "Breadth-first search", 1), ("B", "Depth-first search", 0),
      ("C", "Greedy best-first search", 0), ("D", "Simulated annealing", 0)]),
    ("In a rule-based expert system, the component that applies rules to the knowledge base is called the:",
     [("A", "Working memory", 0), ("B", "Inference engine", 1),
      ("C", "User interface", 0), ("D", "Fact base", 0)]),
    ("Which of the following best describes a heuristic function in informed search?",
     [("A", "Exact cost to the goal", 0), ("B", "Random tie-breaker", 0),
      ("C", "Estimated cost to the goal", 1), ("D", "Total nodes expanded", 0)]),
    ("A production system in AI primarily consists of rules, working memory and:",
     [("A", "A recognize-act cycle", 1), ("B", "A compiler", 0),
      ("C", "A relational schema", 0), ("D", "A neural layer", 0)]),
    ("Which uncertainty-handling technique represents belief as a degree between 0 and 1?",
     [("A", "Boolean logic", 0), ("B", "Certainty factors / probability", 1),
      ("C", "First-order logic", 0), ("D", "Deterministic rules", 0)]),
]

GRADE_SCALE = [
    {"min": 90, "grade": "A+", "point": 4.00}, {"min": 80, "grade": "A", "point": 4.00},
    {"min": 75, "grade": "A-", "point": 3.70}, {"min": 70, "grade": "B+", "point": 3.30},
    {"min": 65, "grade": "B", "point": 3.00}, {"min": 60, "grade": "B-", "point": 2.70},
    {"min": 55, "grade": "C+", "point": 2.30}, {"min": 50, "grade": "C", "point": 2.00},
    {"min": 45, "grade": "C-", "point": 1.70}, {"min": 40, "grade": "D+", "point": 1.30},
    {"min": 30, "grade": "D", "point": 1.00}, {"min": 0, "grade": "E", "point": 0.00},
]


def grade_for_percentage(pct):
    return next(g_ for g_ in GRADE_SCALE if pct >= g_["min"])


# =========================================================
# CONNECTION
# =========================================================

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def verify_password(entered_password, stored_password):
    return check_password_hash(stored_password, entered_password)


# =========================================================
# SCHEMA
# =========================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,                    -- admin | lecturer | student
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0,  -- email confirmed
    status TEXT NOT NULL DEFAULT 'Active', -- Active | Suspended
    student_id TEXT UNIQUE,
    registration_no TEXT,
    date_of_birth TEXT,
    phone TEXT,
    address TEXT,
    photo_url TEXT,
    degree_programme TEXT,
    faculty TEXT,
    department TEXT,
    academic_advisor TEXT,
    intake_year TEXT,
    programme_code TEXT,
    year_level TEXT,
    courses_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    otp TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    verified INTEGER NOT NULL DEFAULT 0,
    reset_token TEXT,
    consumed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    credits INTEGER NOT NULL,
    kind TEXT NOT NULL,
    semester TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_code TEXT NOT NULL REFERENCES subjects(code) ON DELETE CASCADE,
    enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, subject_code)
);

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    exam_type TEXT NOT NULL DEFAULT 'exam',
    subject_code TEXT NOT NULL REFERENCES subjects(code) ON DELETE CASCADE,
    duration_minutes INTEGER NOT NULL,
    total_marks REAL NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    marks REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_key TEXT NOT NULL,
    text TEXT NOT NULL,
    is_correct INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    submitted_at TEXT,
    score REAL,
    total REAL,
    correct_count INTEGER,
    incorrect_count INTEGER,
    unanswered_count INTEGER,
    grade TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_key TEXT NOT NULL,
    UNIQUE(attempt_id, question_id)
);

CREATE TABLE IF NOT EXISTS course_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_code TEXT NOT NULL REFERENCES subjects(code) ON DELETE CASCADE,
    semester TEXT NOT NULL,
    grade TEXT NOT NULL,
    grade_point REAL NOT NULL,
    published INTEGER NOT NULL DEFAULT 0,
    published_at TEXT,
    UNIQUE(user_id, subject_code, semester)
);

CREATE TABLE IF NOT EXISTS admin_exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    course TEXT NOT NULL,
    date TEXT NOT NULL,
    duration TEXT NOT NULL,
    students INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Scheduled',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_id TEXT UNIQUE NOT NULL,
    text TEXT NOT NULL,
    course TEXT NOT NULL,
    type TEXT DEFAULT 'Multiple Choice',
    marks INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam TEXT NOT NULL,
    course TEXT NOT NULL,
    submitted INTEGER DEFAULT 0,
    graded INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    university TEXT DEFAULT 'Sabaragamuwa University of Sri Lanka',
    system_name TEXT DEFAULT 'ExamPortal',
    support_email TEXT DEFAULT 'support@sab.ac.lk',
    default_duration TEXT DEFAULT '60 minutes',
    auto_grade INTEGER DEFAULT 1,
    require_approval INTEGER DEFAULT 1
);
"""


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
    seed(db)


# =========================================================
# SEED (idempotent — safe to call on every startup)
# =========================================================

def _row_count(db, table):
    return db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _create_user(db, **f):
    cols = ", ".join(f.keys())
    placeholders = ", ".join("?" for _ in f)
    cur = db.execute(f"INSERT INTO users ({cols}) VALUES ({placeholders})", tuple(f.values()))
    return cur.lastrowid


def seed(db):
    # ---- subject catalogue -------------------------------------------------
    if _row_count(db, "subjects") == 0:
        db.executemany(
            "INSERT INTO subjects (code, name, credits, kind, semester) VALUES (?, ?, ?, ?, ?)",
            SUBJECTS,
        )

    # ---- admin account -------------------------------------------------
    if db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone() is None:
        _create_user(db, role="admin", full_name="Administrator", email=ADMIN_EMAIL,
                     password_hash=generate_password_hash(ADMIN_PASSWORD),
                     is_active=1, status="Active")

    # ---- demo lecturers (admin roster) ---------------------------------
    if _row_count(db, "users") == 0 or db.execute(
            "SELECT COUNT(*) FROM users WHERE role='lecturer'").fetchone()[0] == 0:
        for name, email, dept, courses in DEMO_LECTURERS:
            if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
                continue
            _create_user(db, role="lecturer", full_name=name, email=email, department=dept,
                         courses_count=courses, password_hash=generate_password_hash("Lecturer@123"),
                         is_active=1, status="Active")

    # ---- demo student (fully working login) -----------------------------
    demo_row = db.execute("SELECT id FROM users WHERE email = ?", (DEMO_STUDENT["email"],)).fetchone()
    if demo_row is None:
        demo_id = _create_user(
            db, role="student", full_name=DEMO_STUDENT["name"], email=DEMO_STUDENT["email"],
            password_hash=generate_password_hash(DEMO_STUDENT["password"]),
            student_id=DEMO_STUDENT["student_id"], is_active=1, status="Active",
            intake_year="2022", programme_code="APP", registration_no="2022/CST/078",
            degree_programme="BSc (Hons) in Computer Science & Technology",
            faculty="Faculty of Applied Sciences",
            department="Dept. of Physical Sciences & Technology",
            academic_advisor="Dr. R. Perera", year_level="3",
            phone="+94 77 123 4567", address="No. 45, Temple Road, Ratnapura",
        )
    else:
        demo_id = demo_row["id"]

    # ---- other demo students (admin roster) ------------------------------
    if db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0] <= 1:
        for name, reg, email, program, year in DEMO_STUDENTS:
            if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
                continue
            _create_user(db, role="student", full_name=name, email=email, registration_no=reg,
                         degree_programme=program, year_level=year,
                         password_hash=generate_password_hash("Student@123"),
                         is_active=1, status="Active")

    # ---- demo student enrolled in y1-y3s1 CST subjects -------------------
    if db.execute("SELECT COUNT(*) FROM enrollments WHERE user_id=?", (demo_id,)).fetchone()[0] == 0:
        codes = db.execute(
            "SELECT code FROM subjects WHERE semester IN ('y1s1','y1s2','y2s1','y2s2','y3s1')"
        ).fetchall()
        db.executemany(
            "INSERT OR IGNORE INTO enrollments (user_id, subject_code) VALUES (?, ?)",
            [(demo_id, r["code"]) for r in codes],
        )

    # ---- one real, gradable exam -----------------------------------------
    if _row_count(db, "exams") == 0:
        subject = db.execute("SELECT code FROM subjects WHERE code = 'PST 31224'").fetchone()
        if subject:
            now = datetime.utcnow()
            cur = db.execute(
                "INSERT INTO exams (title, exam_type, subject_code, duration_minutes, total_marks, "
                "start_time, end_time) VALUES (?,?,?,?,?,?,?)",
                ("Mid-Semester Examination", "exam", subject["code"], 20, 50,
                 (now - timedelta(days=1)).isoformat(), (now + timedelta(days=7)).isoformat()),
            )
            exam_id = cur.lastrowid
            for text, options in DEMO_EXAM_QUESTIONS:
                qcur = db.execute(
                    "INSERT INTO questions (exam_id, text, marks) VALUES (?, ?, ?)",
                    (exam_id, text, 10),
                )
                qid = qcur.lastrowid
                db.executemany(
                    "INSERT INTO options (question_id, option_key, text, is_correct) VALUES (?,?,?,?)",
                    [(qid, k, t, c) for k, t, c in options],
                )

    # ---- published course results for the demo student (y1/y2 complete) ---
    if db.execute("SELECT COUNT(*) FROM course_results WHERE user_id=?", (demo_id,)).fetchone()[0] == 0:
        scale = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D"]
        points = {"A+": 4.0, "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
                  "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0}
        rows = []
        for sem in ["y1s1", "y1s2", "y2s1", "y2s2"]:
            for r in db.execute("SELECT code FROM subjects WHERE semester=?", (sem,)).fetchall():
                h = sum(ord(c) for c in r["code"]) % len(scale)
                grade = scale[h]
                rows.append((demo_id, r["code"], sem, grade, points[grade], 1, datetime.utcnow().isoformat()))
        db.executemany(
            "INSERT INTO course_results (user_id, subject_code, semester, grade, grade_point, "
            "published, published_at) VALUES (?,?,?,?,?,?,?)",
            rows,
        )

    # ---- admin sample data --------------------------------------------
    if _row_count(db, "admin_exams") == 0:
        db.executemany(
            "INSERT INTO admin_exams (name, course, date, duration, students, status) VALUES (?,?,?,?,?,?)",
            ADMIN_EXAMS,
        )

    if _row_count(db, "admin_questions") == 0:
        db.executemany(
            "INSERT INTO admin_questions (display_id, text, course, type, marks) VALUES (?,?,?,?,?)",
            ADMIN_QUESTIONS,
        )

    if _row_count(db, "admin_results") == 0:
        db.executemany(
            "INSERT INTO admin_results (exam, course, submitted, graded, status) VALUES (?,?,?,?,?)",
            ADMIN_RESULTS,
        )

    if _row_count(db, "admin_settings") == 0:
        db.execute("INSERT INTO admin_settings (id) VALUES (1)")

    db.commit()
