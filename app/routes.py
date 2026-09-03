from flask import Blueprint, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from urllib.parse import urlparse
import string
import secrets

from app import db
from app.models import User, ShortURL, ClickEvent


bp = Blueprint("routes", __name__)


# -------------------------
# AUTHENTICATION
# -------------------------

@bp.route("/auth/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return {"message": "Request body is required."}, 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"message": "Username and password are required."}, 400

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return {"message": "Username already exists."}, 409

    hashed_password = generate_password_hash(password)

    user = User(
        username=username,
        password=hashed_password
    )

    db.session.add(user)
    db.session.commit()

    return {
        "message": "User registered successfully."
    }, 201


@bp.route("/auth/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return {"message": "Request body is required."}, 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"message": "Username and password are required."}, 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return {"message": "Invalid username or password."}, 401

    access_token = create_access_token(identity=str(user.id))

    return {
        "access_token": access_token
    }, 200


# -------------------------
# CREATE SHORT URL
# -------------------------

@bp.route("/urls", methods=["POST"])
@jwt_required()
def create_short_url():

    user_id = get_jwt_identity()

    data = request.get_json()

    if not data:
        return {"message": "Request body is required."}, 400

    original_url = data.get("original_url")

    if not original_url:
        return {"message": "original_url is required."}, 400

    # Validate URL
    parsed_url = urlparse(original_url)

    if parsed_url.scheme not in ["http", "https"] or not parsed_url.netloc:
        return {"message": "Invalid URL."}, 400

    # Generate short code
    characters = string.ascii_letters + string.digits

    while True:
        short_code = "".join(
            secrets.choice(characters)
            for _ in range(6)
        )

        existing_url = ShortURL.query.filter_by(
            short_code=short_code
        ).first()

        if not existing_url:
            break

    short_url = ShortURL(
        original_url=original_url,
        short_code=short_code,
        user_id=user_id
    )

    db.session.add(short_url)
    db.session.commit()

    return {
        "message": "Short URL created successfully.",
        "id": short_url.id,
        "original_url": short_url.original_url,
        "short_code": short_url.short_code
    }, 201


# -------------------------
# REDIRECT
# -------------------------

@bp.route("/<short_code>", methods=["GET"])
def redirect_to_original(short_code):

    short_url = ShortURL.query.filter_by(
        short_code=short_code
    ).first()

    if not short_url:
        return {"message": "Short URL not found."}, 404

    # Record click
    click = ClickEvent(
        short_url_id=short_url.id
    )

    db.session.add(click)
    db.session.commit()

    return redirect(short_url.original_url)


# -------------------------
# GET USER'S URLS
# -------------------------

@bp.route("/urls", methods=["GET"])
@jwt_required()
def get_urls():

    user_id = get_jwt_identity()

    urls = ShortURL.query.filter_by(
        user_id=user_id
    ).all()

    result = []

    for url in urls:
        result.append({
            "id": url.id,
            "original_url": url.original_url,
            "short_code": url.short_code
        })

    return {
        "urls": result
    }, 200


# -------------------------
# GET SINGLE URL
# -------------------------

@bp.route("/urls/<int:url_id>", methods=["GET"])
@jwt_required()
def get_single_url(url_id):

    user_id = get_jwt_identity()

    short_url = ShortURL.query.filter_by(
        id=url_id,
        user_id=user_id
    ).first()

    if not short_url:
        return {"message": "URL not found."}, 404

    click_count = ClickEvent.query.filter_by(
        short_url_id=short_url.id
    ).count()

    return {
        "id": short_url.id,
        "original_url": short_url.original_url,
        "short_code": short_url.short_code,
        "clicks": click_count
    }, 200


# -------------------------
# DELETE URL
# -------------------------

@bp.route("/urls/<int:url_id>", methods=["DELETE"])
@jwt_required()
def delete_url(url_id):

    user_id = get_jwt_identity()

    short_url = ShortURL.query.filter_by(
        id=url_id,
        user_id=user_id
    ).first()

    if not short_url:
        return {"message": "URL not found."}, 404

    # Delete click events first
    ClickEvent.query.filter_by(
        short_url_id=short_url.id
    ).delete()

    db.session.delete(short_url)
    db.session.commit()

    return {
        "message": "Short URL deleted successfully."
    }, 200
