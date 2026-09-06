from flask import Flask, jsonify
from database import init_db
from api.auth import auth_bp
from api.lecturer import lecturer_bp

app = Flask(__name__)

# --- CORS (manual, since flask-cors isn't installed) ---
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/api/<path:_any>", methods=["OPTIONS"])
def cors_preflight(_any):
    return "", 204


app.register_blueprint(auth_bp)
app.register_blueprint(lecturer_bp)


@app.route("/")
def index():
    return jsonify({
        "service": "ExamPortal API",
        "status": "running",
        "try": [
            "POST /api/auth/login  {\"email\": \"davis@susl.ac.lk\", \"password\": \"password123\"}",
            "GET  /api/lecturer/dashboard   (Authorization: Bearer <token>)",
            "GET  /api/lecturer/subjects",
            "GET  /api/lecturer/questions",
            "POST /api/lecturer/questions",
            "PUT  /api/lecturer/questions/<id>",
            "DELETE /api/lecturer/questions/<id>",
            "GET  /api/lecturer/exams",
            "POST /api/lecturer/exams",
            "GET  /api/lecturer/exams/<id>/results",
        ],
    })


if __name__ == "__main__":
    init_db()  # creates + seeds exam_portal.db on first run
    app.run(host="0.0.0.0", port=5001, debug=False)
