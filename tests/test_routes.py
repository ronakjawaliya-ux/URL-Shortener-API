import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import create_app, db
from app.models import User, ShortURL, ClickEvent



@pytest.fixture
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-bytes-long"
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()



@pytest.fixture
def client(app):
    return app.test_client()


def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == "User registered successfully."



def test_login_user(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "testpassword123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.get_json()



def test_create_short_url(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "urltest@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "urltest@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Create short URL
    response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 201
    assert "short_code" in response.get_json()



def test_create_short_url_without_token(client):
    response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com"
        }
    )

    assert response.status_code == 401



def test_get_urls(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "list@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "list@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Create a short URL
    client.post(
        "/urls",
        json={
            "original_url": "https://example.com"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    # Get user's URLs
    response = client.get(
        "/urls",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data["urls"], list)
    assert len(data["urls"]) == 1



def test_user_cannot_access_another_users_url(client):
    # Register User 1
    client.post(
        "/auth/register",
        json={
            "email": "user1@example.com",
            "password": "testpassword123"
        }
    )

    # Login User 1
    login1 = client.post(
        "/auth/login",
        json={
            "email": "user1@example.com",
            "password": "testpassword123"
        }
    )

    token1 = login1.get_json()["access_token"]

    # Create URL as User 1
    create_response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com"
        },
        headers={
            "Authorization": f"Bearer {token1}"
        }
    )

    url_id = create_response.get_json()["id"]

    # Register User 2
    client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "password": "testpassword123"
        }
    )

    # Login User 2
    login2 = client.post(
        "/auth/login",
        json={
            "email": "user2@example.com",
            "password": "testpassword123"
        }
    )

    token2 = login2.get_json()["access_token"]

    # User 2 tries to access User 1's URL
    response = client.get(
        f"/urls/{url_id}",
        headers={
            "Authorization": f"Bearer {token2}"
        }
    )

    assert response.status_code == 404



def test_short_url_redirect(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "redirect@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "redirect@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Create short URL
    create_response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    short_code = create_response.get_json()["short_code"]

    # Visit short URL
    response = client.get(
        f"/{short_code}",
        follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com"



def test_click_tracking(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "click@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "click@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Create short URL
    create_response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    short_code = create_response.get_json()["short_code"]

    # Visit short URL
    response = client.get(
        f"/{short_code}",
        follow_redirects=False
    )

    assert response.status_code == 302

    # Check URL analytics
    url_response = client.get(
        "/urls/1/analytics",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert url_response.status_code == 200

    data = url_response.get_json()

    assert data["total_clicks"] == 1
    assert len(data["clicks"]) == 1



def test_expired_short_url(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "expired@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "expired@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Create an already-expired URL
    response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com",
            "expires_at": "2020-01-01T12:00:00"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    # API should reject an expiration date in the past
    assert response.status_code == 400



def test_expired_url_returns_410(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "expired410@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "expired410@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Create a URL with a future expiration date
    create_response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com",
            "expires_at": "2030-01-01T12:00:00"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert create_response.status_code == 201

    short_code = create_response.get_json()["short_code"]

    # Manually expire the URL in the test database
    url = ShortURL.query.filter_by(short_code=short_code).first()
    url.expires_at = datetime(2020, 1, 1, 12, 0, 0)
    db.session.commit()

    # Try to access expired URL
    response = client.get(
        f"/{short_code}",
        follow_redirects=False
    )

    assert response.status_code == 410
    assert response.get_json()["message"] == "Short URL has expired."



def test_login_with_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "correctpassword123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword123"
        }
    )

    assert response.status_code == 401



def test_create_short_url_invalid_url(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "invalidurl@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "invalidurl@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Try to create an invalid URL
    response = client.post(
        "/urls",
        json={
            "original_url": "not-a-valid-url"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 400



def test_create_short_url_missing_url(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "missingurl@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "missingurl@example.com",
            "password": "testpassword123"
        }
    )

    token = login_response.get_json()["access_token"]

    # Try to create a URL without original_url
    response = client.post(
        "/urls",
        json={},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 400



def test_nonexistent_short_url(client):
    response = client.get(
        "/doesnotexist",
        follow_redirects=False
    )

    assert response.status_code == 404



