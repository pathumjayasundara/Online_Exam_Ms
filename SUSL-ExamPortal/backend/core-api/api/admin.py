from datetime import datetime
from functools import wraps

from flask import Blueprint, g, jsonify, request
from werkzeug.security import generate_password_hash

from database import get_db
from auth_utils import require_auth

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def require_admin(func):
    @wraps(func)
    @require_auth
    def wrapper(*args, **kwargs):
        if g.current_user.get("role") != "admin":
            return jsonify(success=False, message="Administrator access required."), 403
        return func(*args, **kwargs)
    return wrapper


def log(db, category, title, text):
    db.execute("INSERT INTO activity_log (category, title, text) VALUES (?, ?, ?)",
               (category, title, text))


# ============================================================
# DASHBOARD
# ============================================================
@admin_bp.get("/dashboard")
@require_admin
def dashboard():
    db = get_db()
    total_exams = db.execute("SELECT COUNT(*) AS n FROM admin_exams").fetchone()["n"]
    total_students = db.execute("SELECT COUNT(*) AS n FROM users WHERE role='student'").fetchone()["n"]
    completed = db.execute("SELECT COUNT(*) AS n FROM admin_exams WHERE status='Completed'").fetchone()["n"]
    pending = db.execute(
        "SELECT COUNT(*) AS n FROM admin_exams WHERE status IN ('Scheduled','Live')"
    ).fetchone()["n"]
    total_q = db.execute("SELECT COUNT(*) AS n FROM admin_questions").fetchone()["n"]
    mcq = db.execute("SELECT COUNT(*) AS n FROM admin_questions WHERE type='Multiple Choice'").fetchone()["n"]
    return jsonify({
        "exams": total_exams, "students": total_students, "completed": completed,
        "pending": pending, "questions": total_q, "mcq": mcq, "written": total_q - mcq,
    })


@admin_bp.get("/activity")
@require_admin
def activity():
    db = get_db()
    rows = db.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 8").fetchall()
    return jsonify([
        {"c": r["category"], "title": r["title"], "text": r["text"],
         "ts": int(datetime.fromisoformat(r["created_at"]).timestamp() * 1000)}
        for r in rows
    ])


# ============================================================
# EXAMS
# ============================================================
def _exam_json(e):
    return {"id": e["id"], "name": e["name"], "course": e["course"], "date": e["date"],
            "duration": e["duration"], "students": e["students"], "status": e["status"]}


@admin_bp.get("/exams")
@require_admin
def list_exams():
    db = get_db()
    rows = db.execute("SELECT * FROM admin_exams ORDER BY id DESC").fetchall()
    return jsonify([_exam_json(e) for e in rows])


@admin_bp.post("/exams")
@require_admin
def create_exam():
    db = get_db()
    d = request.get_json(force=True, silent=True) or {}
    name, course = (d.get("name") or "").strip(), (d.get("course") or "").strip().upper()
    date, duration = d.get("date"), d.get("duration")
    if not all([name, course, date, duration]):
        return jsonify(error="name, course, date and duration are required."), 400
    cur = db.execute(
        "INSERT INTO admin_exams (name, course, date, duration, students, status) VALUES (?,?,?,?,?,?)",
        (name, course, date, duration, int(d.get("students") or 0), d.get("status") or "Scheduled"),
    )
    log(db, "blue", "New exam created", name)
    db.commit()
    row = db.execute("SELECT * FROM admin_exams WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_exam_json(row)), 201


@admin_bp.put("/exams/<int:exam_id>")
@require_admin
def update_exam(exam_id):
    db = get_db()
    e = db.execute("SELECT * FROM admin_exams WHERE id = ?", (exam_id,)).fetchone()
    if not e:
        return jsonify(error="Exam not found."), 404
    d = request.get_json(force=True, silent=True) or {}
    fields, values = [], []
    for field in ("name", "date", "duration", "status"):
        if d.get(field) is not None:
            fields.append(f"{field} = ?")
            values.append(d[field])
    if d.get("course") is not None:
        fields.append("course = ?")
        values.append(d["course"].strip().upper())
    if d.get("students") is not None:
        fields.append("students = ?")
        values.append(int(d["students"]))
    if fields:
        values.append(exam_id)
        db.execute(f"UPDATE admin_exams SET {', '.join(fields)} WHERE id = ?", values)
        log(db, "blue", "Exam updated", d.get("name") or e["name"])
        db.commit()
    row = db.execute("SELECT * FROM admin_exams WHERE id = ?", (exam_id,)).fetchone()
    return jsonify(_exam_json(row))


@admin_bp.delete("/exams/<int:exam_id>")
@require_admin
def delete_exam(exam_id):
    db = get_db()
    e = db.execute("SELECT * FROM admin_exams WHERE id = ?", (exam_id,)).fetchone()
    if not e:
        return jsonify(error="Exam not found."), 404
    db.execute("DELETE FROM admin_exams WHERE id = ?", (exam_id,))
    log(db, "orange", "Exam deleted", e["name"])
    db.commit()
    return jsonify(message="Deleted.")


# ============================================================
# STUDENTS  (real `users` rows — role="student")
# ============================================================
def _student_json(u):
    return {"id": u["id"], "name": u["full_name"], "reg": u["registration_no"], "email": u["email"],
            "program": u["degree_programme"], "year": u["year_level"] or "1", "status": u["status"]}


@admin_bp.get("/students")
@require_admin
def list_students():
    db = get_db()
    rows = db.execute("SELECT * FROM users WHERE role='student' ORDER BY id DESC").fetchall()
    return jsonify([_student_json(u) for u in rows])


@admin_bp.post("/students")
@require_admin
def create_student():
    db = get_db()
    d = request.get_json(force=True, silent=True) or {}
    name = (d.get("name") or "").strip()
    reg = (d.get("reg") or "").strip().upper()
    email = (d.get("email") or "").strip().lower()
    program, year = d.get("program"), d.get("year")
    if not all([name, reg, email, program, year]):
        return jsonify(error="All fields are required."), 400
    if db.execute("SELECT id FROM users WHERE email = ? OR registration_no = ?", (email, reg)).fetchone():
        return jsonify(error="This registration number or email already exists."), 409

    cur = db.execute(
        """
        INSERT INTO users (role, full_name, email, registration_no, degree_programme, year_level,
                            password_hash, status, is_active)
        VALUES ('student', ?, ?, ?, ?, ?, ?, 'Active', 1)
        """,
        (name, email, reg, program, str(year), generate_password_hash("Student@123")),
    )
    log(db, "cyan", "Student account added", f"Registration: {reg}")
    db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_student_json(row)), 201


@admin_bp.put("/students/<int:user_id>")
@require_admin
def update_student(user_id):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id = ? AND role='student'", (user_id,)).fetchone()
    if not u:
        return jsonify(error="Student not found."), 404
    d = request.get_json(force=True, silent=True) or {}
    fields, values = [], []
    if d.get("name"):
        fields.append("full_name = ?"); values.append(d["name"].strip())
    if d.get("reg"):
        fields.append("registration_no = ?"); values.append(d["reg"].strip().upper())
    if d.get("email"):
        fields.append("email = ?"); values.append(d["email"].strip().lower())
    if d.get("program"):
        fields.append("degree_programme = ?"); values.append(d["program"])
    if d.get("year"):
        fields.append("year_level = ?"); values.append(str(d["year"]))
    if fields:
        values.append(user_id)
        db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        log(db, "blue", "Student updated", d.get("name") or u["full_name"])
        db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return jsonify(_student_json(row))


@admin_bp.post("/students/<int:user_id>/toggle-status")
@require_admin
def toggle_student_status(user_id):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id = ? AND role='student'", (user_id,)).fetchone()
    if not u:
        return jsonify(error="Student not found."), 404
    new_status = "Suspended" if u["status"] == "Active" else "Active"
    db.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    log(db, "orange", "Account " + new_status.lower(), u["full_name"])
    db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return jsonify(_student_json(row))


@admin_bp.delete("/students/<int:user_id>")
@require_admin
def delete_student(user_id):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id = ? AND role='student'", (user_id,)).fetchone()
    if not u:
        return jsonify(error="Student not found."), 404
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    log(db, "orange", "Student deleted", u["full_name"])
    db.commit()
    return jsonify(message="Deleted.")


# ============================================================
# LECTURERS  (admin-facing roster — role="lecturer" rows in THIS database;
# distinct from the separate credentials in backend/lecturer-api, see README)
# ============================================================
def _lecturer_json(u):
    return {"id": u["id"], "name": u["full_name"], "email": u["email"], "dept": u["department"],
            "courses": str(u["courses_count"] or 0), "status": u["status"]}


@admin_bp.get("/lecturers")
@require_admin
def list_lecturers():
    db = get_db()
    rows = db.execute("SELECT * FROM users WHERE role='lecturer' ORDER BY id DESC").fetchall()
    return jsonify([_lecturer_json(u) for u in rows])


@admin_bp.post("/lecturers")
@require_admin
def create_lecturer():
    db = get_db()
    d = request.get_json(force=True, silent=True) or {}
    name, email, dept = (d.get("name") or "").strip(), (d.get("email") or "").strip().lower(), d.get("dept")
    if not all([name, email, dept]):
        return jsonify(error="All fields are required."), 400
    if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
        return jsonify(error="This email already exists."), 409
    cur = db.execute(
        """
        INSERT INTO users (role, full_name, email, department, courses_count, password_hash,
                            status, is_active)
        VALUES ('lecturer', ?, ?, ?, ?, ?, 'Active', 1)
        """,
        (name, email, dept, int(d.get("courses") or 0), generate_password_hash("Lecturer@123")),
    )
    log(db, "purple", "Lecturer account added", name)
    db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_lecturer_json(row)), 201


@admin_bp.put("/lecturers/<int:user_id>")
@require_admin
def update_lecturer(user_id):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id = ? AND role='lecturer'", (user_id,)).fetchone()
    if not u:
        return jsonify(error="Lecturer not found."), 404
    d = request.get_json(force=True, silent=True) or {}
    fields, values = [], []
    if d.get("name"):
        fields.append("full_name = ?"); values.append(d["name"].strip())
    if d.get("email"):
        fields.append("email = ?"); values.append(d["email"].strip().lower())
    if d.get("dept"):
        fields.append("department = ?"); values.append(d["dept"])
    if d.get("courses") is not None:
        fields.append("courses_count = ?"); values.append(int(d["courses"]))
    if fields:
        values.append(user_id)
        db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        log(db, "blue", "Lecturer updated", d.get("name") or u["full_name"])
        db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return jsonify(_lecturer_json(row))


@admin_bp.post("/lecturers/<int:user_id>/toggle-status")
@require_admin
def toggle_lecturer_status(user_id):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id = ? AND role='lecturer'", (user_id,)).fetchone()
    if not u:
        return jsonify(error="Lecturer not found."), 404
    new_status = "Suspended" if u["status"] == "Active" else "Active"
    db.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    log(db, "orange", "Account " + new_status.lower(), u["full_name"])
    db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return jsonify(_lecturer_json(row))


@admin_bp.delete("/lecturers/<int:user_id>")
@require_admin
def delete_lecturer(user_id):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id = ? AND role='lecturer'", (user_id,)).fetchone()
    if not u:
        return jsonify(error="Lecturer not found."), 404
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    log(db, "orange", "Lecturer deleted", u["full_name"])
    db.commit()
    return jsonify(message="Deleted.")


# ============================================================
# QUESTION BANK
# ============================================================
def _question_json(q):
    return {"id": q["display_id"], "text": q["text"], "course": q["course"],
            "type": q["type"], "marks": q["marks"]}


@admin_bp.get("/questions")
@require_admin
def list_questions():
    db = get_db()
    rows = db.execute("SELECT * FROM admin_questions ORDER BY id DESC").fetchall()
    return jsonify([_question_json(q) for q in rows])


def _next_question_display_id(db):
    last = db.execute("SELECT display_id FROM admin_questions ORDER BY id DESC LIMIT 1").fetchone()
    n = int(last["display_id"][1:]) + 1 if last else 187
    return f"Q{n:05d}"


@admin_bp.post("/questions")
@require_admin
def create_question():
    db = get_db()
    d = request.get_json(force=True, silent=True) or {}
    text, course = (d.get("text") or "").strip(), (d.get("course") or "").strip()
    if not text or not course:
        return jsonify(error="text and course are required."), 400
    display_id = _next_question_display_id(db)
    db.execute(
        "INSERT INTO admin_questions (display_id, text, course, type, marks) VALUES (?,?,?,?,?)",
        (display_id, text, course, d.get("type") or "Multiple Choice", int(d.get("marks") or 1)),
    )
    log(db, "orange", "Question added", text[:50])
    db.commit()
    row = db.execute("SELECT * FROM admin_questions WHERE display_id = ?", (display_id,)).fetchone()
    return jsonify(_question_json(row)), 201


@admin_bp.put("/questions/<display_id>")
@require_admin
def update_question(display_id):
    db = get_db()
    q = db.execute("SELECT * FROM admin_questions WHERE display_id = ?", (display_id,)).fetchone()
    if not q:
        return jsonify(error="Question not found."), 404
    d = request.get_json(force=True, silent=True) or {}
    fields, values = [], []
    for field in ("text", "course", "type"):
        if d.get(field):
            fields.append(f"{field} = ?")
            values.append(d[field])
    if d.get("marks") is not None:
        fields.append("marks = ?")
        values.append(int(d["marks"]))
    if fields:
        values.append(display_id)
        db.execute(f"UPDATE admin_questions SET {', '.join(fields)} WHERE display_id = ?", values)
        log(db, "blue", "Question updated", (d.get("text") or q["text"])[:50])
        db.commit()
    row = db.execute("SELECT * FROM admin_questions WHERE display_id = ?", (display_id,)).fetchone()
    return jsonify(_question_json(row))


@admin_bp.delete("/questions/<display_id>")
@require_admin
def delete_question(display_id):
    db = get_db()
    q = db.execute("SELECT * FROM admin_questions WHERE display_id = ?", (display_id,)).fetchone()
    if not q:
        return jsonify(error="Question not found."), 404
    db.execute("DELETE FROM admin_questions WHERE display_id = ?", (display_id,))
    log(db, "orange", "Question deleted", q["text"][:50])
    db.commit()
    return jsonify(message="Deleted.")


# ============================================================
# RESULTS  (publish -> also publishes matching course_results rows,
# which is what the Student portal's "My Results" / GPA reads)
# ============================================================
def _result_json(r):
    return {"id": r["id"], "exam": r["exam"], "course": r["course"], "submitted": r["submitted"],
            "graded": r["graded"], "status": r["status"]}


@admin_bp.get("/results")
@require_admin
def list_results():
    db = get_db()
    rows = db.execute("SELECT * FROM admin_results ORDER BY id DESC").fetchall()
    return jsonify([_result_json(r) for r in rows])


def _sync_course_results(db, course_code, publish):
    """Publish/withdraw every course_results row for a subject whose code
    matches `course_code` (substring match against the subject catalogue) —
    the integration point between the Admin portal's simple result sets and
    the Student portal's real GPA engine."""
    subjects = db.execute(
        "SELECT code FROM subjects WHERE code LIKE ?", (f"%{course_code}%",)
    ).fetchall()
    codes = [s["code"] for s in subjects]
    if not codes:
        return 0
    placeholders = ",".join("?" for _ in codes)
    rows = db.execute(
        f"SELECT id FROM course_results WHERE subject_code IN ({placeholders})", codes
    ).fetchall()
    if not rows:
        return 0
    ids = [r["id"] for r in rows]
    id_placeholders = ",".join("?" for _ in ids)
    if publish:
        db.execute(
            f"UPDATE course_results SET published = 1, published_at = ? WHERE id IN ({id_placeholders})",
            [datetime.utcnow().isoformat(), *ids],
        )
    else:
        db.execute(
            f"UPDATE course_results SET published = 0, published_at = NULL WHERE id IN ({id_placeholders})",
            ids,
        )
    return len(ids)


@admin_bp.post("/results/<int:result_id>/publish")
@require_admin
def toggle_publish(result_id):
    db = get_db()
    r = db.execute("SELECT * FROM admin_results WHERE id = ?", (result_id,)).fetchone()
    if not r:
        return jsonify(error="Result set not found."), 404

    new_status = "Published" if r["status"] == "Pending" else "Pending"
    graded = r["submitted"] if new_status == "Published" else r["graded"]
    db.execute("UPDATE admin_results SET status = ?, graded = ? WHERE id = ?",
               (new_status, graded, result_id))

    if new_status == "Published":
        n = _sync_course_results(db, r["course"], publish=True)
        log(db, "purple", "Results published", f"{r['exam']} ({n} student result rows published)")
    else:
        _sync_course_results(db, r["course"], publish=False)
        log(db, "purple", "Results withdrawn", r["exam"])

    db.commit()
    row = db.execute("SELECT * FROM admin_results WHERE id = ?", (result_id,)).fetchone()
    return jsonify(_result_json(row))


# ============================================================
# SETTINGS
# ============================================================
def _settings_json(s):
    return {"uni": s["university"], "sys": s["system_name"], "mail": s["support_email"],
            "duration": s["default_duration"], "auto": bool(s["auto_grade"]),
            "approve": bool(s["require_approval"])}


@admin_bp.get("/settings")
@require_admin
def get_settings():
    db = get_db()
    s = db.execute("SELECT * FROM admin_settings WHERE id = 1").fetchone()
    return jsonify(_settings_json(s))


@admin_bp.put("/settings")
@require_admin
def update_settings():
    db = get_db()
    d = request.get_json(force=True, silent=True) or {}
    fields, values = [], []
    mapping = {"uni": "university", "sys": "system_name", "mail": "support_email", "duration": "default_duration"}
    for key, col in mapping.items():
        if d.get(key):
            fields.append(f"{col} = ?")
            values.append(d[key])
    if "auto" in d:
        fields.append("auto_grade = ?"); values.append(1 if d["auto"] else 0)
    if "approve" in d:
        fields.append("require_approval = ?"); values.append(1 if d["approve"] else 0)
    if fields:
        db.execute(f"UPDATE admin_settings SET {', '.join(fields)} WHERE id = 1", values)
        db.commit()
    row = db.execute("SELECT * FROM admin_settings WHERE id = 1").fetchone()
    return jsonify(_settings_json(row))
