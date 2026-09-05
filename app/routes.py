from flask import Blueprint, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from urllib.parse import urlparse
from datetime import datetime, timezone
import string
import secrets

from app import db
from app.models import User, ShortURL, ClickEvent


bp = Blueprint("routes", __name__)

@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


# -------------------------
# AUTHENTICATION
# -------------------------

@bp.route("/auth/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return {"message": "Request body is required."}, 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"message": "Email and password are required."}, 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return {"message": "Email already exists."}, 409

    hashed_password = generate_password_hash(password)

    user = User(
        email=email,
        password_hash=hashed_password
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

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"message": "Email and password are required."}, 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return {"message": "Invalid email or password."}, 401

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

    # Validate expiration date
    expires_at = None

    if data.get("expires_at"):
        from datetime import datetime

        try:
            expires_at = datetime.fromisoformat(data["expires_at"])
        except ValueError:
            return {
                "message": "Invalid expires_at format. Use YYYY-MM-DDTHH:MM:SS."
            }, 400

        if expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
            return {
                "message": "expires_at must be in the future."
            }, 400

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
        user_id=user_id,
        expires_at=expires_at
    )

    db.session.add(short_url)
    db.session.commit()

    return {
        "message": "Short URL created successfully.",
        "id": short_url.id,
        "original_url": short_url.original_url,
        "short_code": short_url.short_code,
        "expires_at": short_url.expires_at.isoformat() if short_url.expires_at else None
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

    # Check if URL has expired
    if short_url.expires_at is not None:
        from datetime import datetime

        if datetime.now(timezone.utc).replace(tzinfo=None) >= short_url.expires_at:
            return {"message": "Short URL has expired."}, 410

    # Record click
    click = ClickEvent(
    short_url_id=short_url.id,
    referrer=request.referrer,
    user_agent=request.headers.get("User-Agent")
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
# URL ANALYTICS
# -------------------------

@bp.route("/urls/<int:url_id>/analytics", methods=["GET"])
@jwt_required()
def url_analytics(url_id):

    user_id = get_jwt_identity()

    short_url = ShortURL.query.filter_by(
        id=url_id,
        user_id=user_id
    ).first()

    if not short_url:
        return {"message": "URL not found."}, 404

    clicks = ClickEvent.query.filter_by(
        short_url_id=short_url.id
    ).order_by(
        ClickEvent.timestamp.desc()
    ).all()

    return {
        "url_id": short_url.id,
        "short_code": short_url.short_code,
        "original_url": short_url.original_url,
        "total_clicks": len(clicks),
        "clicks": [
            {
                "id": click.id,
                "timestamp": click.timestamp.isoformat(),
                "referrer": click.referrer,
                "user_agent": click.user_agent
            }
            for click in clicks
        ]
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
