from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from urllib.parse import urlparse
import string
import secrets


from app import db
from app.models import User, ShortURL

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



@bp.route("/urls", methods=["POST"])
@jwt_required()
def create_url():
    data = request.get_json()

    if not data:
        return {"message": "Request body is required."}, 400

    if "original_url" not in data:
        return {"message": "Original URL is required."}, 400

    original_url = data["original_url"]

    if not isinstance(original_url, str) or not original_url.strip():
        return {"message": "Original URL must be a valid string."}, 400

    parsed_url = urlparse(original_url)

    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        return {"message": "Original URL must be a valid HTTP or HTTPS URL."}, 400


    characters = string.ascii_letters + string.digits

    short_code = ''.join(secrets.choice(characters) for _ in range(7))

    existing_url = ShortURL.query.filter_by(short_code=short_code).first()

    if existing_url is not None:
        return {"message": "Short code already exists. Please try again."}, 409

    user_id = get_jwt_identity()

    new_url = ShortURL(
        short_code=short_code,
        original_url=original_url,
        user_id=user_id
    )


    db.session.add(new_url)
    db.session.commit()


    return {
        "message": "URL created successfully.",
        "id": new_url.id,
        "short_code": new_url.short_code,
        "original_url": new_url.original_url
    }, 201