"""
ExamPortal — core backend (Admin + Student modules).

    pip install -r requirements.txt   (Flask only)
    python app.py

Runs on port 5000 and auto-creates + seeds the SQLite database on first
run — nothing else to configure for local use. See README.md at the
project root for the full architecture (this service + backend/lecturer-api).
"""
import os

from flask import Flask, jsonify, request

from database import init_db, close_db
from api.auth import auth_bp
from api.student import student_bp
from api.admin import admin_bp


app = Flask(__name__)


# =========================================================
# CORS — mirrors backend/lecturer-api's approach. Restrict with the
# CORS_ORIGINS env var (comma-separated) before deploying beyond localhost.
# =========================================================

ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "*")


@app.after_request
def add_cors_headers(response):
    if ALLOWED_ORIGINS == "*":
        response.headers["Access-Control-Allow-Origin"] = "*"
    else:
        origin = request.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS.split(","):
            response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/api/<path:_any>", methods=["OPTIONS"])
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
app.register_blueprint(student_bp)
app.register_blueprint(admin_bp)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():
    return jsonify({
        "service": "ExamPortal - Core API (Admin + Student)",
        "status": "running",
        "api": {
            "register": "POST /api/auth/register",
            "verify": "POST /api/auth/verify",
            "login": "POST /api/auth/login",
            "forgot_password": "POST /api/auth/forgot-password",
            "verify_otp": "POST /api/auth/verify-otp",
            "reset_password": "POST /api/auth/reset-password",
            "student_profile": "GET/PUT /api/student/profile",
            "student_subjects": "GET /api/student/subjects",
            "student_enroll": "POST/DELETE /api/student/subjects/<code>/enroll",
            "student_exams": "GET /api/student/exams",
            "student_exam_details": "GET /api/student/exams/<id>",
            "student_exam_answer": "POST /api/student/exams/<id>/answers",
            "student_exam_submit": "POST /api/student/exams/<id>/submit",
            "student_attempt_history": "GET /api/student/results",
            "student_result_sheet": "GET /api/student/results/sheet?semester=",
            "student_result_summary": "GET /api/student/results/summary",
            "admin_dashboard": "GET /api/admin/dashboard",
            "admin_activity": "GET /api/admin/activity",
            "admin_exams": "GET/POST/PUT/DELETE /api/admin/exams",
            "admin_students": "GET/POST/PUT/DELETE /api/admin/students",
            "admin_lecturers": "GET/POST/PUT/DELETE /api/admin/lecturers",
            "admin_questions": "GET/POST/PUT/DELETE /api/admin/questions",
            "admin_results": "GET /api/admin/results, POST /api/admin/results/<id>/publish",
            "admin_settings": "GET/PUT /api/admin/settings",
        },
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    with app.app_context():
        init_db()

    if not os.environ.get("EXAM_PORTAL_SECRET"):
        print("WARNING: EXAM_PORTAL_SECRET is not set - using an insecure "
              "default signing key. Set the EXAM_PORTAL_SECRET environment "
              "variable before deploying this service.")

    print()
    print("=" * 65)
    print("ExamPortal - Core API (Admin + Student)")
    print("Database initialized and seeded successfully.")
    print("Backend running on port 5000.")
    print("http://127.0.0.1:5000")
    print("=" * 65)
    print()

    app.run(host="0.0.0.0", port=5000, debug=False)
