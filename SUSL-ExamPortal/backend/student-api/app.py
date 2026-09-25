"""
Entry point for the Student Module backend.

    pip install -r requirements.txt
    python app.py

Merge this with Team 01 / Team 03's app.py rather than running two separate
Flask apps — register their blueprints alongside student_bp below.
"""
import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from extensions import db, jwt


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///exam_portal.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    from api.auth import auth_bp
    from api.student import student_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    # Team 01 / Team 03 register their own blueprints the same way, e.g.:
    # from api.lecturer import lecturer_bp
    # from api.admin import admin_bp
    # app.register_blueprint(lecturer_bp)
    # app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()  # for quick local setup — use Flask-Migrate for real deployments

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
