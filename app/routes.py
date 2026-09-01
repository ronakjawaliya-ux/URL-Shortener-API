from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from app import db
from app.models import User

bp = Blueprint("routes", __name__)

@bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return {"message": "Request body is required."}, 400

    if "email" not in data:
        return {"message": "Email is required."}, 400

    if "password" not in data:
        return {"message": "Password is required."}, 400

    email = data["email"]
    password = data["password"]

    user = User.query.filter_by(email=email).first()

    if user is None:
        return {"message": "Invalid email or password."}, 401

    if not check_password_hash(user.password_hash, password):
        return {"message": "Invalid email or password."}, 401

    access_token = create_access_token(identity=str(user.id))

    return {
        "message": "Login successful.",
        "access_token": access_token
    }, 200