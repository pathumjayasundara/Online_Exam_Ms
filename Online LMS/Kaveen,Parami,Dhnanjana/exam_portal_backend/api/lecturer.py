from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import require_role

lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/api/lecturer")


def grade_for(pct):
    if pct >= 75: return "A"
    if pct >= 65: return "B+"
    if pct >= 55: return "B"
    if pct >= 45: return "C"
    if pct >= 35: return "D"
    return "F"


def question_to_dict(row):
    return {
        "id": row["id"],
        "subject_id": row["subject_id"],
        "subject": row["subject_name"],
        "question_text": row["question_text"],
        "options": {
            "A": row["option_a"], "B": row["option_b"],
            "C": row["option_c"], "D": row["option_d"],
        },
        "correct_option": row["correct_option"],
        "difficulty": row["difficulty"],
        "marks": row["marks"],
    }


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------
@lecturer_bp.route("/dashboard", methods=["GET"])
@require_role("lecturer")
def dashboard():
    lecturer_id = request.user["sub"]
    conn = get_db()

    total_subjects = conn.execute(
        "SELECT COUNT(*) c FROM subjects WHERE lecturer_id = ?", (lecturer_id,)
    ).fetchone()["c"]

    total_questions = conn.execute(
        "SELECT COUNT(*) c FROM questions WHERE created_by = ?", (lecturer_id,)
    ).fetchone()["c"]

    active_exams = conn.execute(
        "SELECT COUNT(*) c FROM exams WHERE created_by = ? AND status = 'Active'", (lecturer_id,)
    ).fetchone()["c"]

    # Average score % across all attempts (score / total marks of that exam's questions)
    pct_rows = conn.execute(
        """
        SELECT a.score, (
            SELECT SUM(q.marks) FROM exam_questions eq
            JOIN questions q ON q.id = eq.question_id
            WHERE eq.exam_id = a.exam_id
        ) AS total_marks
        FROM attempts a
        JOIN exams e ON a.exam_id = e.id
        WHERE e.created_by = ?
        """,
        (lecturer_id,),
    ).fetchall()
    pcts = [ (r["score"] / r["total_marks"] * 100) for r in pct_rows if r["total_marks"] ]
    avg_score = round(sum(pcts) / len(pcts), 1) if pcts else 0.0

    recent_questions = conn.execute(
        """SELECT q.id, q.question_text, s.name subject_name
           FROM questions q JOIN subjects s ON q.subject_id = s.id
           WHERE q.created_by = ? ORDER BY q.id DESC LIMIT 5""",
        (lecturer_id,),
    ).fetchall()

    conn.close()
    return jsonify({
        "total_subjects": total_subjects,
        "total_questions": total_questions,
        "active_exams": active_exams,
        "average_score_pct": avg_score,
        "recent_questions": [
            {"id": r["id"], "text": r["question_text"], "subject": r["subject_name"]}
            for r in recent_questions
        ],
    })


# ------------------------------------------------------------------
# My Subjects
# ------------------------------------------------------------------
@lecturer_bp.route("/subjects", methods=["GET"])
@require_role("lecturer")
def list_subjects():
    lecturer_id = request.user["sub"]
    conn = get_db()
    rows = conn.execute(
        """SELECT s.*, (SELECT COUNT(*) FROM questions q WHERE q.subject_id = s.id) AS question_count
           FROM subjects s WHERE s.lecturer_id = ? ORDER BY s.name""",
        (lecturer_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ------------------------------------------------------------------
# Question Bank: list (with filters), create, update, delete
# ------------------------------------------------------------------
@lecturer_bp.route("/questions", methods=["GET"])
@require_role("lecturer")
def list_questions():
    lecturer_id = request.user["sub"]
    subject_id = request.args.get("subject_id")
    difficulty = request.args.get("difficulty")
    search = request.args.get("search", "").strip()

    query = """
        SELECT q.*, s.name AS subject_name
        FROM questions q JOIN subjects s ON q.subject_id = s.id
        WHERE q.created_by = ?
    """
    params = [lecturer_id]

    if subject_id:
        query += " AND q.subject_id = ?"
        params.append(subject_id)
    if difficulty:
        query += " AND q.difficulty = ?"
        params.append(difficulty)
    if search:
        query += " AND LOWER(q.question_text) LIKE ?"
        params.append(f"%{search.lower()}%")
    query += " ORDER BY q.id DESC"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([question_to_dict(r) for r in rows])


@lecturer_bp.route("/questions", methods=["POST"])
@require_role("lecturer")
def create_question():
    lecturer_id = request.user["sub"]
    data = request.get_json(silent=True) or {}

    required = ["subject_id", "question_text", "option_a", "option_b",
                "option_c", "option_d", "correct_option", "difficulty", "marks"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if data["correct_option"] not in ("A", "B", "C", "D"):
        return jsonify({"error": "correct_option must be A, B, C, or D"}), 400
    if data["difficulty"] not in ("Easy", "Medium", "Hard"):
        return jsonify({"error": "difficulty must be Easy, Medium, or Hard"}), 400

    conn = get_db()
    # Make sure the subject belongs to this lecturer
    subject = conn.execute(
        "SELECT * FROM subjects WHERE id = ? AND lecturer_id = ?",
        (data["subject_id"], lecturer_id),
    ).fetchone()
    if not subject:
        conn.close()
        return jsonify({"error": "Subject not found or not assigned to you"}), 404

    cur = conn.execute(
        """INSERT INTO questions
           (subject_id, question_text, option_a, option_b, option_c, option_d,
            correct_option, difficulty, marks, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (data["subject_id"], data["question_text"], data["option_a"], data["option_b"],
         data["option_c"], data["option_d"], data["correct_option"], data["difficulty"],
         int(data["marks"]), lecturer_id),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute(
        """SELECT q.*, s.name AS subject_name FROM questions q
           JOIN subjects s ON q.subject_id = s.id WHERE q.id = ?""",
        (new_id,),
    ).fetchone()
    conn.close()
    return jsonify(question_to_dict(row)), 201


@lecturer_bp.route("/questions/<int:question_id>", methods=["PUT"])
@require_role("lecturer")
def update_question(question_id):
    lecturer_id = request.user["sub"]
    data = request.get_json(silent=True) or {}

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM questions WHERE id = ? AND created_by = ?",
        (question_id, lecturer_id),
    ).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Question not found"}), 404

    fields = ["subject_id", "question_text", "option_a", "option_b", "option_c",
              "option_d", "correct_option", "difficulty", "marks"]
    updates = {f: data[f] for f in fields if f in data}
    if not updates:
        conn.close()
        return jsonify({"error": "No fields to update"}), 400

    set_clause = ", ".join(f"{f} = ?" for f in updates)
    conn.execute(
        f"UPDATE questions SET {set_clause} WHERE id = ?",
        (*updates.values(), question_id),
    )
    conn.commit()
    row = conn.execute(
        """SELECT q.*, s.name AS subject_name FROM questions q
           JOIN subjects s ON q.subject_id = s.id WHERE q.id = ?""",
        (question_id,),
    ).fetchone()
    conn.close()
    return jsonify(question_to_dict(row))


@lecturer_bp.route("/questions/<int:question_id>", methods=["DELETE"])
@require_role("lecturer")
def delete_question(question_id):
    lecturer_id = request.user["sub"]
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM questions WHERE id = ? AND created_by = ?",
        (question_id, lecturer_id),
    ).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Question not found"}), 404

    conn.execute("DELETE FROM exam_questions WHERE question_id = ?", (question_id,))
    conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": question_id})


# ------------------------------------------------------------------
# Create Exam
# ------------------------------------------------------------------
@lecturer_bp.route("/exams", methods=["GET"])
@require_role("lecturer")
def list_exams():
    lecturer_id = request.user["sub"]
    conn = get_db()
    rows = conn.execute(
        """SELECT e.*, s.name AS subject_name,
                  (SELECT COUNT(*) FROM attempts a WHERE a.exam_id = e.id) AS attempt_count
           FROM exams e JOIN subjects s ON e.subject_id = s.id
           WHERE e.created_by = ? ORDER BY e.id DESC""",
        (lecturer_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@lecturer_bp.route("/exams", methods=["POST"])
@require_role("lecturer")
def create_exam():
    lecturer_id = request.user["sub"]
    data = request.get_json(silent=True) or {}

    required = ["title", "subject_id", "duration_minutes", "start_time", "end_time", "question_ids"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if not isinstance(data["question_ids"], list) or len(data["question_ids"]) == 0:
        return jsonify({"error": "question_ids must be a non-empty list"}), 400

    conn = get_db()
    subject = conn.execute(
        "SELECT * FROM subjects WHERE id = ? AND lecturer_id = ?",
        (data["subject_id"], lecturer_id),
    ).fetchone()
    if not subject:
        conn.close()
        return jsonify({"error": "Subject not found or not assigned to you"}), 404

    cur = conn.execute(
        """INSERT INTO exams (subject_id, title, description, duration_minutes,
           start_time, end_time, status, created_by)
           VALUES (?,?,?,?,?,?,?,?)""",
        (data["subject_id"], data["title"], data.get("description", ""),
         int(data["duration_minutes"]), data["start_time"], data["end_time"],
         "Active", lecturer_id),
    )
    exam_id = cur.lastrowid

    total_marks = 0
    for q_id in data["question_ids"]:
        q = conn.execute("SELECT * FROM questions WHERE id = ? AND created_by = ?",
                          (q_id, lecturer_id)).fetchone()
        if not q:
            continue
        conn.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (?,?)",
                     (exam_id, q_id))
        total_marks += q["marks"]

    conn.commit()
    conn.close()
    return jsonify({
        "id": exam_id,
        "title": data["title"],
        "subject_id": data["subject_id"],
        "duration_minutes": data["duration_minutes"],
        "question_count": len(data["question_ids"]),
        "total_marks": total_marks,
        "status": "Active",
    }), 201


# ------------------------------------------------------------------
# View Results
# ------------------------------------------------------------------
@lecturer_bp.route("/exams/<int:exam_id>/results", methods=["GET"])
@require_role("lecturer")
def exam_results(exam_id):
    lecturer_id = request.user["sub"]
    conn = get_db()
    exam = conn.execute(
        "SELECT * FROM exams WHERE id = ? AND created_by = ?", (exam_id, lecturer_id)
    ).fetchone()
    if not exam:
        conn.close()
        return jsonify({"error": "Exam not found"}), 404

    total_marks = conn.execute(
        """SELECT SUM(q.marks) total FROM exam_questions eq
           JOIN questions q ON q.id = eq.question_id WHERE eq.exam_id = ?""",
        (exam_id,),
    ).fetchone()["total"] or 0

    attempts = conn.execute(
        """SELECT a.*, u.full_name FROM attempts a
           JOIN users u ON a.student_id = u.id
           WHERE a.exam_id = ? ORDER BY a.score DESC""",
        (exam_id,),
    ).fetchall()
    conn.close()

    results = []
    for a in attempts:
        pct = round(a["score"] / total_marks * 100, 1) if total_marks else 0
        results.append({
            "student_name": a["full_name"],
            "score": a["score"],
            "total_marks": total_marks,
            "percentage": pct,
            "grade": a["grade"] or grade_for(pct),
            "submitted_at": a["submit_time"],
        })

    avg = round(sum(r["percentage"] for r in results) / len(results), 1) if results else 0
    return jsonify({
        "exam": {"id": exam["id"], "title": exam["title"], "total_marks": total_marks},
        "results": results,
        "class_average_pct": avg,
    })
