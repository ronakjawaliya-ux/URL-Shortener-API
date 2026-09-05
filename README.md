# URL Shortener API

A RESTful URL Shortener API built with **Flask**, **SQLite**, **SQLAlchemy**, and **JWT authentication**.

The API allows users to register and log in, create secure short URLs, set expiration times, track clicks, view analytics, and manage their own URLs.

## Features

* User registration and login
* Password hashing
* JWT-based authentication
* Protected API endpoints
* Short URL generation
* URL validation
* URL expiration
* Expired URLs return `410 Gone`
* Click tracking
* Referrer tracking
* User-agent tracking
* URL analytics
* User ownership and authorization
* Delete short URLs
* SQLite database
* Automated API tests with pytest
* Rate limiting with Flask-Limiter

## Tech Stack

* Python
* Flask
* Flask-SQLAlchemy
* Flask-JWT-Extended
* Flask-Limiter
* SQLite
* SQLAlchemy
* Pytest

## Project Structure

```
URL-Shortener-API/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   └── routes.py
│
├── tests/
│   └── test_routes.py
│
├── .gitignore
├── config.py
├── requirements.txt
├── run.py
├── test.http
└── README.md
```

## Installation

### 1. Clone the repository

```
git clone https://github.com/ronakjawaliya-ux/URL-Shortener-API.git
cd URL-Shortener-API
```

### 2. Create a virtual environment

Windows:

```
python -m venv venv
```

### 3. Activate the virtual environment

```
venv\Scripts\activate
```

### 4. Install dependencies

```
pip install -r requirements.txt
```

## Running the API

Start the Flask application:

```
python run.py
```

The API will run locally at:

```
http://127.0.0.1:5000
```

## Authentication

The API uses JWT authentication.

### Register

```
POST /auth/register
Content-Type: application/json
```

Request:

```
{
    "email": "user@example.com",
    "password": "yourpassword"
}
```

### Login

```
POST /auth/login
Content-Type: application/json
```

Request:

```
{
    "email": "user@example.com",
    "password": "yourpassword"
}
```

The response contains an access token.

Use the token in protected requests:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## API Endpoints

### Authentication

| Method | Endpoint         | Authentication | Description           |
| ------ | ---------------- | -------------- | --------------------- |
| POST   | `/auth/register` | No             | Register a new user   |
| POST   | `/auth/login`    | No             | Login and receive JWT |

### URL Management

| Method | Endpoint                   | Authentication | Description              |
| ------ | -------------------------- | -------------- | ------------------------ |
| POST   | `/urls`                    | JWT            | Create a short URL       |
| GET    | `/urls`                    | JWT            | List user's URLs         |
| GET    | `/urls/<url_id>`           | JWT            | Get URL details          |
| GET    | `/urls/<url_id>/analytics` | JWT            | View click analytics     |
| DELETE | `/urls/<url_id>`           | JWT            | Delete a URL             |
| GET    | `/<short_code>`            | No             | Redirect to original URL |

## Creating a Short URL

```
POST /urls
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

Request:

```
{
    "original_url": "https://example.com"
}
```

Example response:

```
{
    "id": 1,
    "short_code": "Ab12Cd",
    "original_url": "https://example.com"
}
```

## URL Expiration

A URL can optionally have an expiration time.

Example:

```
{
    "original_url": "https://example.com",
    "expires_at": "2026-12-31T23:59:59"
}
```

Once the URL expires, the API returns:

```
410 Gone
```

Response:

```
{
    "message": "Short URL has expired."
}
```

## Click Analytics

The API records information about visits to short URLs.

Analytics include:

* Total clicks
* Click ID
* Timestamp
* Referrer
* User agent

Example:

```
GET /urls/1/analytics
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Authorization

Users can only access and manage their own URLs.

If a user attempts to access a URL belonging to another user, the API returns:

```
404 Not Found
```

This prevents unauthorized access to another user's URL data.

## Testing

The project includes automated tests using **pytest**.

Run all tests:

```
pytest
```

Current test status:

```
14 passed
```

The tests cover:

* User registration
* User login
* JWT authentication
* Protected endpoints
* Short URL creation
* URL validation
* URL listing
* URL ownership
* URL redirection
* Click tracking
* URL expiration
* Expired URL handling
* Invalid login
* Missing URL data
* Non-existent short URLs

## API Testing with VS Code

The project also includes:

```
test.http
```

You can use the **REST Client** extension in VS Code to send HTTP requests directly from the file.

## Database

The project uses SQLite with SQLAlchemy.

The main database models are:

* `User`
* `ShortURL`
* `ClickEvent`

### User

Stores user account information and password hashes.

### ShortURL

Stores:

* Original URL
* Short code
* Creation time
* Expiration time
* Owner

### ClickEvent

Stores:

* Short URL
* Timestamp
* Referrer
* User agent

## Security

The API includes several security features:

* Password hashing
* JWT authentication
* User-level authorization
* URL ownership checks
* Input validation
* URL expiration
* Rate limiting

Passwords are never stored in plain text.

## Future Improvements

Possible future improvements include:

* URL update endpoint
* Custom short codes
* QR code generation
* Redis-based rate limiting
* Production database such as PostgreSQL
* Docker support
* CI/CD with GitHub Actions
* API documentation with Swagger/OpenAPI
* Cloud deployment
* Advanced analytics
* Automated test coverage reporting

## Author

**Ronak Jawalia**

GitHub: https://github.com/ronakjawaliya-ux
