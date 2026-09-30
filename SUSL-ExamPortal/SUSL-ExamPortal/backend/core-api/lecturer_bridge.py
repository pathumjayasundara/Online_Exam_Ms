"""
Bridge between the Core API (students) and the Lecturer API's database.

Lecturers create exams and quizzes in backend/lecturer-api (its own SQLite
file).  Students sit them through this service.  Rather than duplicate the
data by hand, the student endpoints call sync_exams() which mirrors every
*Published* lecturer exam into this service's own tables (exams / questions /
options), where the existing attempt + server-side marking pipeline runs.
Finished attempts are written back to the lecturer's `results` table so the
Lecturer portal's Results page fills in.

Only Multiple Choice and True/False questions can be delivered and auto-marked.
Other question types are skipped.

Set LECTURER_DB_PATH if the lecturer database lives somewhere else.
"""
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LECTURER_DB_PATH = Path(os.environ.get(
    "LECTURER_DB_PATH", BASE_DIR.parent / "lecturer-api" / "exam_portal.db"))

# A lecturer exam only has a start date/time, so it stays open for this many
# hours after it (students may still start it until then).
EXAM_WINDOW_HOURS = int(os.environ.get("EXAM_WINDOW_HOURS", "24"))
OPEN_START = "2000-01-01T00:00:00"
OPEN_END = "2999-12-31T23:59:59"


def _connect(readonly=True):
    if not LECTURER_DB_PATH.exists():
        return None
    if readonly:
        uri = LECTURER_DB_PATH.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=10)
    else:
        conn = sqlite3.connect(str(LECTURER_DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _window(exam_date):
    """(start, end) ISO strings, in server-local time like the datetime-local
    value the lecturer typed.  No date set = open until unpublished."""
    if not exam_date:
        return OPEN_START, OPEN_END
    try:
        start = datetime.fromisoformat(str(exam_date).strip())
    except ValueError:
        return OPEN_START, OPEN_END
    start = start.replace(tzinfo=None)
    return start.isoformat(), (start + timedelta(hours=EXAM_WINDOW_HOURS)).isoformat()


def _question_payload(q):
    """-> ([(key, text)], correct_key) or None if the student engine can't run it."""
    qtype = (q["question_type"] or "Multiple Choice").strip().lower()
    if qtype == "multiple choice":
        opts = [(k, (q["option_" + k.lower()] or "").strip()) for k in "ABCD"]
        opts = [(k, t) for k, t in opts if t]
        correct = (q["correct_answer"] or "").strip().upper()
        if len(opts) < 2 or correct not in {k for k, _ in opts}:
            return None
        return opts, correct
    if qtype == "true/false":
        answer = (q["correct_answer"] or "").strip().lower()
        if answer not in ("true", "false"):
            return None
        return [("A", "True"), ("B", "False")], "A" if answer == "true" else "B"
    return None


def ensure_subject(db, code, lconn=None):
    """Make sure `code` exists in this service's subjects table, copying it
    from the lecturer catalogue if needed.  Returns True if it now exists."""
    if db.execute("SELECT 1 FROM subjects WHERE code = ?", (code,)).fetchone():
        return True
    own = lconn is None
    lconn = lconn or _connect()
    if lconn is None:
        return False
    try:
        s = lconn.execute(
            "SELECT code, title, credits, subject_type, year, semester "
            "FROM subjects WHERE code = ? LIMIT 1", (code,)).fetchone()
    finally:
        if own:
            lconn.close()
    if not s:
        return False
    db.execute(
        "INSERT INTO subjects (code, name, credits, kind, semester) VALUES (?,?,?,?,?)",
        (s["code"], s["title"], int(s["credits"] or 0), s["subject_type"] or "Compulsory",
         "y%ss%s" % (s["year"] or 1, s["semester"] or 1)))
    return True


def sync_exams(db):
    """Mirror Published lecturer exams into the core tables (idempotent)."""
    conn = _connect()
    if conn is None:
        return
    try:
        exams = conn.execute(
            """
            SELECT e.id, e.title, e.duration, e.exam_date, e.exam_type, s.code AS code
            FROM exams e
            INNER JOIN subjects s ON s.id = e.subject_id
            WHERE e.status = 'Published'
            """).fetchall()

        live_ids = []
        for e in exams:
            if not ensure_subject(db, e["code"], conn):
                continue
            built = []
            for q in conn.execute(
                    """
                    SELECT q.* FROM exam_questions eq
                    INNER JOIN questions q ON q.id = eq.question_id
                    WHERE eq.exam_id = ? ORDER BY eq.id
                    """, (e["id"],)).fetchall():
                payload = _question_payload(q)
                if payload:
                    built.append((q, payload))
            if not built:
                continue

            live_ids.append(e["id"])
            start, end = _window(e["exam_date"])
            etype = "quiz" if (e["exam_type"] or "").strip().lower() == "quiz" else "exam"
            total = float(sum(q["marks"] or 1 for q, _ in built))
            duration = int(e["duration"] or 60)

            row = db.execute("SELECT id FROM exams WHERE source_id = ?", (e["id"],)).fetchone()
            if row:
                exam_id = row["id"]
                db.execute(
                    "UPDATE exams SET title=?, exam_type=?, subject_code=?, duration_minutes=?, "
                    "start_time=?, end_time=?, active=1 WHERE id=?",
                    (e["title"], etype, e["code"], duration, start, end, exam_id))
                if db.execute("SELECT 1 FROM attempts WHERE exam_id = ? LIMIT 1",
                              (exam_id,)).fetchone():
                    continue  # already sat by someone: keep the questions they saw
                db.execute("DELETE FROM questions WHERE exam_id = ?", (exam_id,))
                db.execute("UPDATE exams SET total_marks = ? WHERE id = ?", (total, exam_id))
            else:
                exam_id = db.execute(
                    "INSERT INTO exams (title, exam_type, subject_code, duration_minutes, "
                    "total_marks, start_time, end_time, source_id, active) VALUES (?,?,?,?,?,?,?,?,1)",
                    (e["title"], etype, e["code"], duration, total, start, end, e["id"])).lastrowid

            for q, (opts, correct) in built:
                qid = db.execute(
                    "INSERT INTO questions (exam_id, text, marks, source_id) VALUES (?,?,?,?)",
                    (exam_id, q["question_text"], float(q["marks"] or 1), q["id"])).lastrowid
                db.executemany(
                    "INSERT INTO options (question_id, option_key, text, is_correct) VALUES (?,?,?,?)",
                    [(qid, k, t, 1 if k == correct else 0) for k, t in opts])

        # Unpublished / deleted / no-longer-gradable lecturer exams disappear
        # from the student portal (kept, hidden, if a student already sat them).
        if live_ids:
            marks = ",".join("?" for _ in live_ids)
            db.execute("UPDATE exams SET active = 0 WHERE source_id IS NOT NULL "
                       "AND source_id NOT IN (%s)" % marks, live_ids)
        else:
            db.execute("UPDATE exams SET active = 0 WHERE source_id IS NOT NULL")
        db.execute("DELETE FROM exams WHERE active = 0 "
                   "AND id NOT IN (SELECT exam_id FROM attempts)")
        db.commit()
    finally:
        conn.close()


def push_result(source_exam_id, student_id, student_name, score, total):
    """Record a finished attempt in the lecturer's results table (best effort)."""
    if not source_exam_id:
        return False
    conn = _connect(readonly=False)
    if conn is None:
        return False
    try:
        conn.execute("DELETE FROM results WHERE exam_id = ? AND student_id = ?",
                     (source_exam_id, student_id))
        conn.execute(
            "INSERT INTO results (exam_id, student_id, student_name, score, total_marks, submitted_at) "
            "VALUES (?,?,?,?,?,?)",
            (source_exam_id, student_id, student_name, score, total,
             datetime.now().isoformat(timespec="seconds")))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()
