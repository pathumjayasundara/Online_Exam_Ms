from flask import Flask, jsonify, request

from database import init_db, close_db
from api.auth import auth_bp
from api.lecturer import lecturer_bp


app = Flask(__name__)


# =========================================================
# CORS
# =========================================================

@app.after_request
def add_cors_headers(response):

    response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization"
    )

    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, PUT, DELETE, OPTIONS"
    )

    return response


@app.route(
    "/api/<path:_any>",
    methods=["OPTIONS"]
)
def cors_preflight(_any):

    return "", 204


# =========================================================
# DATABASE CLEANUP
# =========================================================

@app.teardown_appcontext
def teardown_db(exception=None):

    close_db(exception)


# =========================================================
# BLUEPRINTS
# =========================================================

app.register_blueprint(auth_bp)
app.register_blueprint(lecturer_bp)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return jsonify({
        "service": "ExamPortal - Lecturer Module",
        "status": "running",

        "frontend":
            "Run exam_portal_lecturer.html with Live Server",

        "api": {

            "login":
                "POST /api/auth/login",

            "dashboard":
                "GET /api/lecturer/dashboard",

            "subjects":
                "GET /api/lecturer/subjects",

            "available_subjects":
                "GET /api/lecturer/available-subjects",

            "subject_options":
                "GET /api/lecturer/subject-options",

            "programmes":
                "GET /api/lecturer/programmes",

            "streams":
                "GET /api/lecturer/streams",

            "years":
                "GET /api/lecturer/years",

            "semesters":
                "GET /api/lecturer/semesters",

            "my_subjects":
                "POST /api/lecturer/my-subjects",

            "remove_subject":
                "DELETE /api/lecturer/my-subjects/<subject_id>",

            "questions":
                "GET /api/lecturer/questions",

            "add_question":
                "POST /api/lecturer/questions",

            "update_question":
                "PUT /api/lecturer/questions/<question_id>",

            "delete_question":
                "DELETE /api/lecturer/questions/<question_id>",

            "exams":
                "GET /api/lecturer/exams",

            "create_exam":
                "POST /api/lecturer/exams",

            "exam_questions":
                "GET /api/lecturer/exams/<id>/questions",

            "results":
                "GET /api/lecturer/exams/<id>/results",

            "delete_exam":
                "DELETE /api/lecturer/exams/<id>"
        }
    })


# =========================================================
# DEBUG AUTH
# =========================================================

@app.route(
    "/debug-auth",
    methods=["GET"]
)
def debug_auth():

    return jsonify({
        "authorization_header":
            request.headers.get("Authorization"),

        "all_headers":
            dict(request.headers)
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    with app.app_context():

        init_db()

    print()
    print("=" * 60)
    print("ExamPortal - Lecturer Module")
    print("Database initialized successfully.")
    print("Backend running on port 5001.")
    print("http://127.0.0.1:5001")
    print("=" * 60)
    print()

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )