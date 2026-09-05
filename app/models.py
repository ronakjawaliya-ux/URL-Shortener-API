from datetime import datetime, timezone
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    urls = db.relationship("ShortURL", backref="owner", lazy=True)


class ShortURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    original_url = db.Column(db.String(2048), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    clicks = db.relationship("ClickEvent", backref="short_url", lazy=True, cascade="all, delete-orphan")


class ClickEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_url_id = db.Column(db.Integer, db.ForeignKey("short_url.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    referrer = db.Column(db.String(2048), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)