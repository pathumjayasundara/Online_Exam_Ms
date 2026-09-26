from flask import Blueprint, request, jsonify, g

from database import get_db
from auth_utils import require_auth, require_role


lecturer_bp = Blueprint(
    "lecturer",
    __name__,
    url_prefix="/api/lecturer"
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def lecturer_id():
    return g.current_user["id"]


def row_to_dict(row):
    if row is None:
        return None

    return dict(row)


def get_owned_subject(db, subject_id):

    return db.execute(
        """
        SELECT s.*
        FROM subjects s
        INNER JOIN lecturer_subjects ls
            ON ls.subject_id = s.id
        WHERE ls.lecturer_id = ?
        AND s.id = ?
        """,
        (
            lecturer_id(),
            subject_id
        )
    ).fetchone()


def get_owned_question(db, question_id):

    return db.execute(
        """
        SELECT q.*
        FROM questions q
        INNER JOIN lecturer_subjects ls
            ON ls.subject_id = q.subject_id
        WHERE q.id = ?
        AND ls.lecturer_id = ?
        """,
        (
            question_id,
            lecturer_id()
        )
    ).fetchone()


# =========================================================
# DASHBOARD
# =========================================================

@lecturer_bp.route("/dashboard", methods=["GET"])
@require_auth
@require_role("lecturer")
def dashboard():

    db = get_db()

    lid = lecturer_id()

    subject_count = db.execute(
        """
        SELECT COUNT(*)
        FROM lecturer_subjects
        WHERE lecturer_id = ?
        """,
        (lid,)
    ).fetchone()[0]

    question_count = db.execute(
        """
        SELECT COUNT(*)
        FROM questions q
        INNER JOIN lecturer_subjects ls
            ON ls.subject_id = q.subject_id
        WHERE ls.lecturer_id = ?
        """,
        (lid,)
    ).fetchone()[0]

    active_exams = db.execute(
        """
        SELECT COUNT(*)
        FROM exams
        WHERE lecturer_id = ?
        AND LOWER(status) = 'active'
        """,
        (lid,)
    ).fetchone()[0]

    result_row = db.execute(
        """
        SELECT AVG(
            CASE
                WHEN r.total_marks > 0
                THEN
                    r.score * 100.0 / r.total_marks
                ELSE NULL
            END
        ) AS average_score

        FROM results r

        INNER JOIN exams e
            ON e.id = r.exam_id

        WHERE e.lecturer_id = ?
        """,
        (lid,)
    ).fetchone()

    average_score = 0

    if result_row:
        average_score = result_row["average_score"] or 0

    return jsonify({
        "success": True,
        "data": {
            "my_subjects": subject_count,
            "total_questions": question_count,
            "active_exams": active_exams,
            "average_score": round(
                float(average_score),
                1
            )
        }
    })


# =========================================================
# MY SUBJECTS
# =========================================================

@lecturer_bp.route("/subjects", methods=["GET"])
@require_auth
@require_role("lecturer")
def subjects():

    db = get_db()

    rows = db.execute(
        """
        SELECT
            s.id,
            s.code,
            s.title,
            s.credits,
            s.subject_type,
            s.programme,
            s.stream,
            s.year,
            s.semester,
            s.department,

            (
                SELECT COUNT(*)
                FROM questions q
                WHERE q.subject_id = s.id
            ) AS question_count

        FROM subjects s

        INNER JOIN lecturer_subjects ls
            ON ls.subject_id = s.id

        WHERE ls.lecturer_id = ?

        ORDER BY
            s.programme,
            s.year,
            s.semester,
            s.code
        """,
        (lecturer_id(),)
    ).fetchall()

    return jsonify({
        "success": True,
        "subjects": [
            dict(row)
            for row in rows
        ]
    })


# =========================================================
# PROGRAMMES
# =========================================================

@lecturer_bp.route("/programmes", methods=["GET"])
@require_auth
@require_role("lecturer")
def programmes():

    db = get_db()

    rows = db.execute(
        """
        SELECT DISTINCT programme
        FROM subjects
        WHERE programme IS NOT NULL
        AND TRIM(programme) <> ''
        ORDER BY programme
        """
    ).fetchall()

    return jsonify({
        "success": True,
        "programmes": [
            row["programme"]
            for row in rows
        ]
    })


# =========================================================
# STREAMS
# =========================================================

@lecturer_bp.route("/streams", methods=["GET"])
@require_auth
@require_role("lecturer")
def streams():

    db = get_db()

    programme = request.args.get(
        "programme",
        ""
    ).strip()

    year = request.args.get(
        "year",
        ""
    ).strip()

    params = []

    sql = """
        SELECT DISTINCT stream
        FROM subjects
        WHERE stream IS NOT NULL
        AND TRIM(stream) <> ''
    """

    if programme:

        sql += " AND programme = ?"
        params.append(programme)

    if year:

        sql += " AND year = ?"
        params.append(year)

    sql += " ORDER BY stream"

    rows = db.execute(
        sql,
        params
    ).fetchall()

    return jsonify({
        "success": True,
        "streams": [
            row["stream"]
            for row in rows
        ]
    })


# =========================================================
# YEARS
# =========================================================

@lecturer_bp.route("/years", methods=["GET"])
@require_auth
@require_role("lecturer")
def years():

    db = get_db()

    programme = request.args.get(
        "programme",
        ""
    ).strip()

    stream = request.args.get(
        "stream",
        ""
    ).strip()

    params = []

    sql = """
        SELECT DISTINCT year
        FROM subjects
        WHERE year IS NOT NULL
    """

    if programme:

        sql += " AND programme = ?"
        params.append(programme)

    if stream:

        sql += " AND stream = ?"
        params.append(stream)

    sql += " ORDER BY year"

    rows = db.execute(
        sql,
        params
    ).fetchall()

    return jsonify({
        "success": True,
        "years": [
            row["year"]
            for row in rows
        ]
    })


# =========================================================
# SEMESTERS
# =========================================================

@lecturer_bp.route("/semesters", methods=["GET"])
@require_auth
@require_role("lecturer")
def semesters():

    db = get_db()

    programme = request.args.get(
        "programme",
        ""
    ).strip()

    stream = request.args.get(
        "stream",
        ""
    ).strip()

    year = request.args.get(
        "year",
        ""
    ).strip()

    params = []

    sql = """
        SELECT DISTINCT semester
        FROM subjects
        WHERE semester IS NOT NULL
    """

    if programme:

        sql += " AND programme = ?"
        params.append(programme)

    if stream:

        sql += " AND stream = ?"
        params.append(stream)

    if year:

        sql += " AND year = ?"
        params.append(year)

    sql += " ORDER BY semester"

    rows = db.execute(
        sql,
        params
    ).fetchall()

    return jsonify({
        "success": True,
        "semesters": [
            row["semester"]
            for row in rows
        ]
    })


# =========================================================
# AVAILABLE SUBJECTS
#
# IMPORTANT:
# Returns ALL handbook subjects.
# Lecturer can choose their own subjects.
# =========================================================

@lecturer_bp.route(
    "/available-subjects",
    methods=["GET"]
)
@require_auth
@require_role("lecturer")
def available_subjects():

    db = get_db()

    programme = request.args.get(
        "programme",
        ""
    ).strip()

    stream = request.args.get(
        "stream",
        ""
    ).strip()

    year = request.args.get(
        "year",
        ""
    ).strip()

    semester = request.args.get(
        "semester",
        ""
    ).strip()

    lid = lecturer_id()

    params = [lid]

    sql = """
        SELECT
            s.id,
            s.code,
            s.title,
            s.credits,
            s.subject_type,
            s.programme,
            s.stream,
            s.year,
            s.semester,
            s.department,

            CASE
                WHEN ls.id IS NOT NULL
                THEN 1
                ELSE 0
            END AS already_added

        FROM subjects s

        LEFT JOIN lecturer_subjects ls
            ON ls.subject_id = s.id
            AND ls.lecturer_id = ?

        WHERE 1 = 1
    """

    if programme:

        sql += " AND s.programme = ?"
        params.append(programme)

    if stream:

        sql += " AND s.stream = ?"
        params.append(stream)

    if year:

        sql += " AND s.year = ?"
        params.append(year)

    if semester:

        sql += " AND s.semester = ?"
        params.append(semester)

    sql += """
        ORDER BY
            s.programme,
            s.year,
            s.semester,
            s.code
    """

    rows = db.execute(
        sql,
        params
    ).fetchall()

    subjects_data = [
        dict(row)
        for row in rows
    ]

    return jsonify({
        "success": True,
        "count": len(subjects_data),
        "subjects": subjects_data
    })


# =========================================================
# SUBJECT OPTIONS
# =========================================================

@lecturer_bp.route(
    "/subject-options",
    methods=["GET"]
)
@require_auth
@require_role("lecturer")
def subject_options():

    db = get_db()

    rows = db.execute(
        """
        SELECT
            s.id,
            s.code,
            s.title,
            s.programme,
            s.stream,
            s.year,
            s.semester,

            (
                SELECT COUNT(*)
                FROM questions q
                WHERE q.subject_id = s.id
            ) AS question_count

        FROM subjects s

        INNER JOIN lecturer_subjects ls
            ON ls.subject_id = s.id

        WHERE ls.lecturer_id = ?

        ORDER BY
            s.programme,
            s.year,
            s.semester,
            s.code
        """,
        (lecturer_id(),)
    ).fetchall()

    return jsonify({
        "success": True,
        "subjects": [
            dict(row)
            for row in rows
        ]
    })


# =========================================================
# ADD SUBJECT
# =========================================================

@lecturer_bp.route(
    "/my-subjects",
    methods=["POST"]
)
@require_auth
@require_role("lecturer")
def add_my_subject():

    db = get_db()

    data = request.get_json(
        silent=True
    ) or {}

    subject_id = data.get("subject_id")

    if not subject_id:

        return jsonify({
            "success": False,
            "message": "subject_id is required."
        }), 400

    subject = db.execute(
        """
        SELECT id
        FROM subjects
        WHERE id = ?
        """,
        (subject_id,)
    ).fetchone()

    if subject is None:

        return jsonify({
            "success": False,
            "message": "Subject not found."
        }), 404

    existing = db.execute(
        """
        SELECT id
        FROM lecturer_subjects
        WHERE lecturer_id = ?
        AND subject_id = ?
        """,
        (
            lecturer_id(),
            subject_id
        )
    ).fetchone()

    if existing:

        return jsonify({
            "success": True,
            "message": "Subject is already added."
        })

    db.execute(
        """
        INSERT INTO lecturer_subjects
        (
            lecturer_id,
            subject_id
        )
        VALUES (?, ?)
        """,
        (
            lecturer_id(),
            subject_id
        )
    )

    db.commit()

    return jsonify({
        "success": True,
        "message": "Subject added successfully."
    }), 201


# =========================================================
# REMOVE SUBJECT
# =========================================================

@lecturer_bp.route(
    "/my-subjects/<int:subject_id>",
    methods=["DELETE"]
)
@require_auth
@require_role("lecturer")
def remove_my_subject(subject_id):

    db = get_db()

    cursor = db.execute(
        """
        DELETE FROM lecturer_subjects
        WHERE lecturer_id = ?
        AND subject_id = ?
        """,
        (
            lecturer_id(),
            subject_id
        )
    )

    db.commit()

    if cursor.rowcount == 0:

        return jsonify({
            "success": False,
            "message":
                "Subject was not found in My Subjects."
        }), 404

    return jsonify({
        "success": True,
        "message": "Subject removed successfully."
    })


# =========================================================
# QUESTIONS - GET
# =========================================================

@lecturer_bp.route(
    "/questions",
    methods=["GET"]
)
@require_auth
@require_role("lecturer")
def questions():

    db = get_db()

    subject_id = request.args.get(
        "subject_id"
    )

    question_type = request.args.get(
        "question_type",
        ""
    ).strip()

    difficulty = request.args.get(
        "difficulty",
        ""
    ).strip()

    search = request.args.get(
        "search",
        ""
    ).strip()

    params = [lecturer_id()]

    sql = """
        SELECT
            q.id,
            q.subject_id,
            q.question_type,
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_answer,
            q.expected_answer,
            q.marks,
            q.difficulty,
            q.created_by,
            q.created_at,

            s.code AS subject_code,
            s.title AS subject_title,
            s.programme,
            s.stream,
            s.year,
            s.semester

        FROM questions q

        INNER JOIN subjects s
            ON s.id = q.subject_id

        INNER JOIN lecturer_subjects ls
            ON ls.subject_id = q.subject_id

        WHERE ls.lecturer_id = ?
    """

    if subject_id:

        sql += " AND q.subject_id = ?"
        params.append(subject_id)

    if question_type:

        sql += " AND q.question_type = ?"
        params.append(question_type)

    if difficulty:

        sql += " AND q.difficulty = ?"
        params.append(difficulty)

    if search:

        sql += " AND q.question_text LIKE ?"
        params.append(
            f"%{search}%"
        )

    sql += " ORDER BY q.id DESC"

    rows = db.execute(
        sql,
        params
    ).fetchall()

    question_list = []

    for row in rows:

        item = dict(row)

        item["correct_option"] = (
            item.get("correct_answer")
        )

        question_list.append(item)

    return jsonify({
        "success": True,
        "questions": question_list
    })


# =========================================================
# ADD QUESTION
# =========================================================

@lecturer_bp.route(
    "/questions",
    methods=["POST"]
)
@require_auth
@require_role("lecturer")
def add_question():

    db = get_db()

    data = request.get_json(
        silent=True
    ) or {}

    subject_id = data.get("subject_id")

    question_type = str(
        data.get(
            "question_type",
            "Multiple Choice"
        )
    ).strip()

    question_text = str(
        data.get(
            "question_text",
            ""
        )
    ).strip()

    option_a = str(
        data.get("option_a", "")
    ).strip()

    option_b = str(
        data.get("option_b", "")
    ).strip()

    option_c = str(
        data.get("option_c", "")
    ).strip()

    option_d = str(
        data.get("option_d", "")
    ).strip()

    correct_answer = str(
        data.get(
            "correct_answer",
            data.get(
                "correct_option",
                ""
            )
        )
    ).strip()

    expected_answer = str(
        data.get(
            "expected_answer",
            ""
        )
    ).strip()

    difficulty = str(
        data.get(
            "difficulty",
            "Medium"
        )
    ).strip()

    marks = data.get("marks", 1)

    valid_types = [
        "Multiple Choice",
        "True/False",
        "Short Answer",
        "Essay/Long Answer",
        "Fill in the Blank",
        "Matching",
        "Scenario/Structured"
    ]

    if question_type not in valid_types:

        return jsonify({
            "success": False,
            "message": "Invalid question type."
        }), 400

    if not subject_id:

        return jsonify({
            "success": False,
            "message": "Subject is required."
        }), 400

    if not question_text:

        return jsonify({
            "success": False,
            "message":
                "Question text is required."
        }), 400

    ownership = get_owned_subject(
        db,
        subject_id
    )

    if ownership is None:

        return jsonify({
            "success": False,
            "message":
                "This subject is not assigned to you."
        }), 403

    if question_type == "Multiple Choice":

        if not all([
            option_a,
            option_b,
            option_c,
            option_d
        ]):

            return jsonify({
                "success": False,
                "message":
                    "All four options are required."
            }), 400

        if correct_answer.upper() not in [
            "A", "B", "C", "D"
        ]:

            return jsonify({
                "success": False,
                "message":
                    "Correct answer must be A, B, C or D."
            }), 400

        correct_answer = correct_answer.upper()

    elif question_type == "True/False":

        if correct_answer.lower() not in [
            "true",
            "false"
        ]:

            return jsonify({
                "success": False,
                "message":
                    "Correct answer must be True or False."
            }), 400

        correct_answer = (
            correct_answer.capitalize()
        )

        option_a = "True"
        option_b = "False"
        option_c = None
        option_d = None

    else:

        if not expected_answer:

            return jsonify({
                "success": False,
                "message":
                    "Expected answer is required."
            }), 400

        correct_answer = None

    try:

        marks = int(marks)

    except (
        TypeError,
        ValueError
    ):

        marks = 1

    if marks <= 0:
        marks = 1

    if difficulty not in [
        "Easy",
        "Medium",
        "Hard"
    ]:

        difficulty = "Medium"

    cursor = db.execute(
        """
        INSERT INTO questions
        (
            subject_id,
            question_type,
            question_text,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer,
            expected_answer,
            marks,
            difficulty,
            created_by
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subject_id,
            question_type,
            question_text,
            option_a or None,
            option_b or None,
            option_c or None,
            option_d or None,
            correct_answer or None,
            expected_answer or None,
            marks,
            difficulty,
            lecturer_id()
        )
    )

    db.commit()

    return jsonify({
        "success": True,
        "message":
            "Question added successfully.",
        "question_id":
            cursor.lastrowid
    }), 201


# =========================================================
# UPDATE QUESTION
# =========================================================

@lecturer_bp.route(
    "/questions/<int:question_id>",
    methods=["PUT"]
)
@require_auth
@require_role("lecturer")
def update_question(question_id):

    db = get_db()

    question = get_owned_question(
        db,
        question_id
    )

    if question is None:

        return jsonify({
            "success": False,
            "message": "Question not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    question_type = str(
        data.get(
            "question_type",
            question["question_type"]
        )
    ).strip()

    question_text = str(
        data.get(
            "question_text",
            ""
        )
    ).strip()

    option_a = str(
        data.get("option_a", "")
    ).strip()

    option_b = str(
        data.get("option_b", "")
    ).strip()

    option_c = str(
        data.get("option_c", "")
    ).strip()

    option_d = str(
        data.get("option_d", "")
    ).strip()

    correct_answer = str(
        data.get(
            "correct_answer",
            data.get(
                "correct_option",
                ""
            )
        )
    ).strip()

    expected_answer = str(
        data.get(
            "expected_answer",
            ""
        )
    ).strip()

    difficulty = str(
        data.get(
            "difficulty",
            "Medium"
        )
    ).strip()

    marks = data.get("marks", 1)

    valid_types = [
        "Multiple Choice",
        "True/False",
        "Short Answer",
        "Essay/Long Answer",
        "Fill in the Blank",
        "Matching",
        "Scenario/Structured"
    ]

    if question_type not in valid_types:

        return jsonify({
            "success": False,
            "message":
                "Invalid question type."
        }), 400

    if not question_text:

        return jsonify({
            "success": False,
            "message":
                "Question text is required."
        }), 400

    if question_type == "Multiple Choice":

        if not all([
            option_a,
            option_b,
            option_c,
            option_d
        ]):

            return jsonify({
                "success": False,
                "message":
                    "All four options are required."
            }), 400

        if correct_answer.upper() not in [
            "A", "B", "C", "D"
        ]:

            return jsonify({
                "success": False,
                "message":
                    "Correct answer must be A, B, C or D."
            }), 400

        correct_answer = correct_answer.upper()
        expected_answer = None

    elif question_type == "True/False":

        if correct_answer.lower() not in [
            "true",
            "false"
        ]:

            return jsonify({
                "success": False,
                "message":
                    "Correct answer must be True or False."
            }), 400

        correct_answer = (
            correct_answer.capitalize()
        )

        option_a = "True"
        option_b = "False"
        option_c = None
        option_d = None
        expected_answer = None

    else:

        if not expected_answer:

            return jsonify({
                "success": False,
                "message":
                    "Expected answer is required."
            }), 400

        correct_answer = None

    try:

        marks = int(marks)

    except (
        TypeError,
        ValueError
    ):

        marks = 1

    if marks <= 0:
        marks = 1

    if difficulty not in [
        "Easy",
        "Medium",
        "Hard"
    ]:

        difficulty = "Medium"

    db.execute(
        """
        UPDATE questions

        SET
            question_type = ?,
            question_text = ?,
            option_a = ?,
            option_b = ?,
            option_c = ?,
            option_d = ?,
            correct_answer = ?,
            expected_answer = ?,
            marks = ?,
            difficulty = ?

        WHERE id = ?
        """,
        (
            question_type,
            question_text,
            option_a or None,
            option_b or None,
            option_c or None,
            option_d or None,
            correct_answer,
            expected_answer,
            marks,
            difficulty,
            question_id
        )
    )

    db.commit()

    return jsonify({
        "success": True,
        "message":
            "Question updated successfully."
    })


# =========================================================
# DELETE QUESTION
# =========================================================

@lecturer_bp.route(
    "/questions/<int:question_id>",
    methods=["DELETE"]
)
@require_auth
@require_role("lecturer")
def delete_question(question_id):

    db = get_db()

    question = get_owned_question(
        db,
        question_id
    )

    if question is None:

        return jsonify({
            "success": False,
            "message":
                "Question not found."
        }), 404

    db.execute(
        """
        DELETE FROM exam_questions
        WHERE question_id = ?
        """,
        (question_id,)
    )

    db.execute(
        """
        DELETE FROM questions
        WHERE id = ?
        """,
        (question_id,)
    )

    db.commit()

    return jsonify({
        "success": True,
        "message":
            "Question deleted successfully."
    })


# =========================================================
# EXAMS - GET
# =========================================================

@lecturer_bp.route(
    "/exams",
    methods=["GET"]
)
@require_auth
@require_role("lecturer")
def exams():

    db = get_db()

    rows = db.execute(
        """
        SELECT
            e.id,
            e.title,
            e.subject_id,
            e.duration,
            e.exam_date,
            e.status,

            s.code AS subject_code,
            s.title AS subject_title,

            (
                SELECT COUNT(*)
                FROM exam_questions eq
                WHERE eq.exam_id = e.id
            ) AS question_count

        FROM exams e

        INNER JOIN subjects s
            ON s.id = e.subject_id

        WHERE e.lecturer_id = ?

        ORDER BY e.id DESC
        """,
        (lecturer_id(),)
    ).fetchall()

    return jsonify({
        "success": True,
        "exams": [
            dict(row)
            for row in rows
        ]
    })


# =========================================================
# CREATE EXAM
# =========================================================

@lecturer_bp.route(
    "/exams",
    methods=["POST"]
)
@require_auth
@require_role("lecturer")
def create_exam():

    db = get_db()

    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get("title", "")
    ).strip()

    subject_id = data.get("subject_id")

    duration = data.get(
        "duration",
        data.get(
            "duration_minutes",
            60
        )
    )

    exam_date = data.get(
        "exam_date",
        data.get(
            "start_time",
            ""
        )
    )

    status = str(
        data.get(
            "status",
            "Draft"
        )
    ).strip()

    question_ids = data.get(
        "question_ids",
        []
    )

    if not title:

        return jsonify({
            "success": False,
            "message":
                "Exam title is required."
        }), 400

    if not subject_id:

        return jsonify({
            "success": False,
            "message":
                "Subject is required."
        }), 400

    if not isinstance(
        question_ids,
        list
    ):

        return jsonify({
            "success": False,
            "message":
                "question_ids must be a list."
        }), 400

    if len(question_ids) == 0:

        return jsonify({
            "success": False,
            "message":
                "Select at least one question."
        }), 400

    subject = get_owned_subject(
        db,
        subject_id
    )

    if subject is None:

        return jsonify({
            "success": False,
            "message":
                "This subject is not assigned to you."
        }), 403

    try:

        duration = int(duration)

    except (
        TypeError,
        ValueError
    ):

        duration = 60

    if duration <= 0:
        duration = 60

    clean_question_ids = []

    for question_id in question_ids:

        try:

            question_id = int(
                question_id
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        if question_id not in clean_question_ids:

            clean_question_ids.append(
                question_id
            )

    if not clean_question_ids:

        return jsonify({
            "success": False,
            "message":
                "No valid questions were selected."
        }), 400

    placeholders = ",".join(
        "?"
        for _ in clean_question_ids
    )

    valid_questions = db.execute(
        f"""
        SELECT q.id

        FROM questions q

        INNER JOIN lecturer_subjects ls
            ON ls.subject_id = q.subject_id

        WHERE ls.lecturer_id = ?

        AND q.subject_id = ?

        AND q.id IN ({placeholders})
        """,
        [
            lecturer_id(),
            subject_id,
            *clean_question_ids
        ]
    ).fetchall()

    valid_ids = {
        row["id"]
        for row in valid_questions
    }

    if len(valid_ids) != len(
        clean_question_ids
    ):

        return jsonify({
            "success": False,
            "message":
                "One or more selected questions do not belong to your subject."
        }), 403

    cursor = db.execute(
        """
        INSERT INTO exams
        (
            title,
            subject_id,
            lecturer_id,
            duration,
            exam_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            subject_id,
            lecturer_id(),
            duration,
            exam_date,
            status
        )
    )

    exam_id = cursor.lastrowid

    for question_id in clean_question_ids:

        db.execute(
            """
            INSERT INTO exam_questions
            (
                exam_id,
                question_id
            )
            VALUES (?, ?)
            """,
            (
                exam_id,
                question_id
            )
        )

    db.commit()

    return jsonify({
        "success": True,
        "message":
            "Exam created successfully.",
        "exam_id":
            exam_id
    }), 201


# =========================================================
# EXAM QUESTIONS
# =========================================================

@lecturer_bp.route(
    "/exams/<int:exam_id>/questions",
    methods=["GET"]
)
@require_auth
@require_role("lecturer")
def exam_questions(exam_id):

    db = get_db()

    exam = db.execute(
        """
        SELECT *
        FROM exams
        WHERE id = ?
        AND lecturer_id = ?
        """,
        (
            exam_id,
            lecturer_id()
        )
    ).fetchone()

    if exam is None:

        return jsonify({
            "success": False,
            "message":
                "Exam not found."
        }), 404

    rows = db.execute(
        """
        SELECT
            q.id,
            q.subject_id,
            q.question_type,
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_answer,
            q.expected_answer,
            q.marks,
            q.difficulty

        FROM questions q

        INNER JOIN exam_questions eq
            ON eq.question_id = q.id

        WHERE eq.exam_id = ?

        ORDER BY q.id
        """,
        (exam_id,)
    ).fetchall()

    return jsonify({
        "success": True,
        "questions": [
            dict(row)
            for row in rows
        ]
    })


# =========================================================
# RESULTS
# =========================================================

@lecturer_bp.route(
    "/exams/<int:exam_id>/results",
    methods=["GET"]
)
@require_auth
@require_role("lecturer")
def exam_results(exam_id):

    db = get_db()

    exam = db.execute(
        """
        SELECT
            e.id,
            e.title,
            e.subject_id,
            e.duration,
            e.exam_date,
            e.status,

            s.code AS subject_code,
            s.title AS subject_title

        FROM exams e

        INNER JOIN subjects s
            ON s.id = e.subject_id

        WHERE e.id = ?
        AND e.lecturer_id = ?
        """,
        (
            exam_id,
            lecturer_id()
        )
    ).fetchone()

    if exam is None:

        return jsonify({
            "success": False,
            "message":
                "Exam not found."
        }), 404

    rows = db.execute(
        """
        SELECT
            id,
            exam_id,
            student_id,
            student_name,
            score,
            total_marks,
            submitted_at

        FROM results

        WHERE exam_id = ?

        ORDER BY score DESC
        """,
        (exam_id,)
    ).fetchall()

    return jsonify({
        "success": True,

        "exam": dict(exam),

        "results": [
            dict(row)
            for row in rows
        ]
    })


# =========================================================
# DELETE EXAM
# =========================================================

@lecturer_bp.route(
    "/exams/<int:exam_id>",
    methods=["DELETE"]
)
@require_auth
@require_role("lecturer")
def delete_exam(exam_id):

    db = get_db()

    exam = db.execute(
        """
        SELECT id
        FROM exams
        WHERE id = ?
        AND lecturer_id = ?
        """,
        (
            exam_id,
            lecturer_id()
        )
    ).fetchone()

    if exam is None:

        return jsonify({
            "success": False,
            "message":
                "Exam not found."
        }), 404

    db.execute(
        """
        DELETE FROM exam_questions
        WHERE exam_id = ?
        """,
        (exam_id,)
    )

    db.execute(
        """
        DELETE FROM results
        WHERE exam_id = ?
        """,
        (exam_id,)
    )

    db.execute(
        """
        DELETE FROM exams
        WHERE id = ?
        AND lecturer_id = ?
        """,
        (
            exam_id,
            lecturer_id()
        )
    )

    db.commit()

    return jsonify({
        "success": True,
        "message":
            "Exam deleted successfully."
    })