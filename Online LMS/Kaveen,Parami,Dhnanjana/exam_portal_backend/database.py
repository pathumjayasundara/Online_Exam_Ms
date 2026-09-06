"""
database.py
-----------
Thin SQLite helper for the ExamPortal backend.

Note: the project guide names Flask-SQLAlchemy as the ORM, but that package
(and Flask-JWT-Extended / Flask-Cors) requires internet access to install and
was not available in this sandbox. This module implements the same schema
and behaviour using Python's built-in `sqlite3` module instead, so the app
runs standalone. requirements.txt still lists the "real" packages for when
you run this on a machine with internet access — swapping this file for a
SQLAlchemy models.py later is a drop-in change; the API layer doesn't need
to know the difference.
"""
import sqlite3
import os
import hashlib
import hmac

DB_PATH = os.path.join(os.path.dirname(__file__), "exam_portal.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','lecturer','student')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    year INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    lecturer_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK(correct_option IN ('A','B','C','D')),
    difficulty TEXT NOT NULL CHECK(difficulty IN ('Easy','Medium','Hard')),
    marks INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    title TEXT NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    created_by INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS exam_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL REFERENCES exams(id),
    question_id INTEGER NOT NULL REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL REFERENCES exams(id),
    student_id INTEGER NOT NULL REFERENCES users(id),
    start_time TEXT,
    submit_time TEXT,
    score INTEGER,
    grade TEXT
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    selected_option TEXT
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """Simple salted hash (stdlib only). Use werkzeug.security or bcrypt in production."""
    salt = "susl-exam-portal"
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def init_db(reset=False):
    """Create tables (and seed sample data) if the database doesn't exist yet."""
    fresh = reset or not os.path.exists(DB_PATH)
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()

    if fresh:
        _seed(conn)
    conn.close()


def _seed(conn):
    from datetime import datetime, timedelta, timezone

    cur = conn.cursor()

    # --- Users ---
    cur.execute(
        "INSERT INTO users (full_name, email, password_hash, role) VALUES (?,?,?,?)",
        ("Dr. A. Davis", "davis@susl.ac.lk", hash_password("password123"), "lecturer"),
    )
    lecturer_id = cur.lastrowid

    student_names = [
        "Saman Perera", "Nimali Fernando", "Kasun Madushanka", "Tharindu Jayawardena",
        "Dinithi Weerasinghe", "Chamindu Silva", "Rashmi Gunasekara",
        "Amaya Rathnayake", "Ishan Wickramasinghe", "Ravindu Bandara",
        "Nadeesha Kumari", "Yohan Peiris",
    ]
    student_ids = []
    for name in student_names:
        email = name.lower().replace(" ", ".") + "@susl.ac.lk"
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?,?,?,?)",
            (name, email, hash_password("password123"), "student"),
        )
        student_ids.append(cur.lastrowid)

    # --- Subjects (all taught by our one lecturer for this demo) ---
    subjects = [
        ("CS201", "Data Structures", 2, 1),
        ("CS202", "Algorithms", 2, 2),
        ("CS301", "Database Systems", 2, 2),
        ("CS302", "Operating Systems", 3, 1),
        ("CS303", "Computer Networks", 3, 1),
    ]
    subject_ids = {}
    for code, name, year, sem in subjects:
        cur.execute(
            "INSERT INTO subjects (code, name, year, semester, lecturer_id) VALUES (?,?,?,?,?)",
            (code, name, year, sem, lecturer_id),
        )
        subject_ids[name] = cur.lastrowid

    # --- Questions ---
    questions = [
        ("Computer Networks", "Explain TCP three-way handshake.",
         "Establishes a connection using SYN, SYN-ACK, ACK", "Closes a connection gracefully",
         "Encrypts data in transit", "Routes packets between subnets", "A", "Medium", 3),
        ("Algorithms", "What is time complexity? Explain Big O notation.",
         "A measure of how runtime grows with input size", "The amount of memory a program uses",
         "The number of lines of code", "A sorting technique", "A", "Easy", 2),
        ("Operating Systems", "Explain the concept of Deadlock with example.",
         "Two or more processes waiting on each other indefinitely", "A process that never terminates",
         "A memory leak in the kernel", "A CPU scheduling algorithm", "A", "Hard", 5),
        ("Database Systems", "Normalize the following relation up to 3NF.",
         "Remove transitive dependencies on the primary key", "Add more foreign keys",
         "Merge all tables into one", "Remove all indexes", "A", "Medium", 5),
        ("Data Structures", "What is a linked list? Explain with an example.",
         "A sequence of nodes where each node points to the next", "A fixed-size array of elements",
         "A key-value data structure", "A tree with two children per node", "A", "Easy", 2),
        ("Data Structures", "What is a Binary Search Tree?",
         "A tree where left subtree < node < right subtree", "A tree where every node has 4 children",
         "A tree with no root", "A hashing-based structure", "A", "Medium", 3),
        ("Algorithms", "Describe the working of Merge Sort.",
         "Divide the array, sort recursively, then merge", "Swap adjacent elements repeatedly",
         "Pick a pivot and partition around it", "Insert elements one by one into a sorted section",
         "A", "Medium", 4),
    ]
    question_ids = []
    for subj_name, text, a, b, c, d, correct, diff, marks in questions:
        cur.execute(
            """INSERT INTO questions
               (subject_id, question_text, option_a, option_b, option_c, option_d,
                correct_option, difficulty, marks, created_by)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (subject_ids[subj_name], text, a, b, c, d, correct, diff, marks, lecturer_id),
        )
        question_ids.append((cur.lastrowid, subj_name, marks))

    # --- Exams ---
    now = datetime.now(timezone.utc)
    exams_def = [
        ("Data Structures Midterm Exam", "Data Structures", 60),
        ("Database Systems Quiz", "Database Systems", 30),
        ("Algorithms Final Exam", "Algorithms", 90),
    ]
    exam_ids = {}
    exam_total_marks = {}
    for title, subj_name, duration in exams_def:
        start = now - timedelta(days=20)
        end = start + timedelta(hours=2)
        cur.execute(
            """INSERT INTO exams (subject_id, title, description, duration_minutes,
               start_time, end_time, status, created_by)
               VALUES (?,?,?,?,?,?,?,?)""",
            (subject_ids[subj_name], title, "", duration,
             start.isoformat(), end.isoformat(), "Active", lecturer_id),
        )
        exam_id = cur.lastrowid
        exam_ids[title] = exam_id
        total_marks = 0
        for q_id, q_subj, q_marks in question_ids:
            if q_subj == subj_name:
                cur.execute(
                    "INSERT INTO exam_questions (exam_id, question_id) VALUES (?,?)",
                    (exam_id, q_id),
                )
                total_marks += q_marks
        exam_total_marks[title] = total_marks

    # --- Attempts + Answers (seeded scores, matching the frontend mock) ---
    def grade_for(pct):
        if pct >= 75: return "A"
        if pct >= 65: return "B+"
        if pct >= 55: return "B"
        if pct >= 45: return "C"
        if pct >= 35: return "D"
        return "F"

    # Percentages used to derive each student's score from the exam's real total marks
    # (computed above from the actual questions attached to each exam).
    results_seed_pct = {
        "Data Structures Midterm Exam": [84, 76, 70, 62, 56, 48, 40],
        "Database Systems Quiz": [90, 73, 60],
        "Algorithms Final Exam": [92, 65],
    }

    sid_iter = iter(student_ids)
    for exam_title, pcts in results_seed_pct.items():
        exam_id = exam_ids[exam_title]
        total = exam_total_marks[exam_title]
        for pct in pcts:
            student_id = next(sid_iter)
            score = round(pct / 100 * total)
            actual_pct = round(score / total * 100, 1) if total else 0
            submit_time = (now - timedelta(days=5)).isoformat()
            cur.execute(
                """INSERT INTO attempts (exam_id, student_id, start_time, submit_time, score, grade)
                   VALUES (?,?,?,?,?,?)""",
                (exam_id, student_id, submit_time, submit_time, score, grade_for(actual_pct)),
            )

    conn.commit()


if __name__ == "__main__":
    init_db(reset=True)
    print(f"Database initialised at {DB_PATH}")
