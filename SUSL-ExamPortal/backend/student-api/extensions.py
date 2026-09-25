"""
Shared Flask extension instances. Created here (unbound) and initialised
against the app in app.py's create_app(), so models.py / api/*.py can
import `db` and `jwt` without circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()
