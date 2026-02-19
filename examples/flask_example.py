"""
Flask example integration with AuthLib

Shows how to integrate AuthLib with Flask for building
a complete authentication API.

Run with: python -m flask --app examples.flask_example run
"""

from flask import Flask, request, jsonify
from functools import wraps
from sqlalchemy.orm import Session
from authlib.database import db
from authlib.services.auth_service import AuthService
from authlib.services.user_service import UserService
from authlib.utils.exceptions import (
    AuthException,
    UserNotFound,
    InvalidCredentials,
    InvalidToken,
    UserAlreadyExists,
    ValidationError,
)


# ============================================================================
# Flask App Setup
# ============================================================================

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ============================================================================
# Decorators
# ============================================================================

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({"error": "Invalid authorization header"}), 401

            token = parts[1]
            session = db.create_session()

            try:
                auth_service = AuthService(session)
                payload = auth_service.verify_token(token)
                kwargs["current_user"] = payload
                return f(*args, **kwargs)
            finally:
                session.close()
        except InvalidToken as e:
            return jsonify({"error": e.message}), 401
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500

    return decorated_function


def handle_auth_exception(f):
    """Decorator to handle authentication exceptions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except UserAlreadyExists as e:
            return jsonify({"error": e.message}), 409
        except ValidationError as e:
            return jsonify({"error": e.message}), 400
        except (UserNotFound, InvalidCredentials) as e:
            return jsonify({"error": e.message}), 401
        except InvalidToken as e:
            return jsonify({"error": e.message}), 401
        except AuthException as e:
            return jsonify({"error": e.message}), e.status_code
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500

    return decorated_function


# ============================================================================
# Routes
# ============================================================================

@app.route("/api/auth/signup", methods=["POST"])
@handle_auth_exception
def signup():
    """
    Register a new user.

    Request JSON:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }

    Returns:
        JSON with user data and tokens
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    session = db.create_session()

    try:
        auth_service = AuthService(session)
        result = auth_service.register(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return jsonify(result), 201
    finally:
        session.close()


@app.route("/api/auth/login", methods=["POST"])
@handle_auth_exception
def login():
    """
    Authenticate user and return tokens.

    Request JSON:
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }

    Returns:
        JSON with user data and tokens
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    session = db.create_session()

    try:
        auth_service = AuthService(session)
        result = auth_service.login(email=email, password=password)
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/api/auth/refresh", methods=["POST"])
@handle_auth_exception
def refresh_token():
    """
    Refresh access token using refresh token.

    Request JSON:
    {
        "refresh_token": "eyJhbGc..."
    }

    Returns:
        JSON with new access token
    """
    data = request.get_json()

    if not data or not data.get("refresh_token"):
        return jsonify({"error": "refresh_token is required"}), 400

    session = db.create_session()

    try:
        auth_service = AuthService(session)
        result = auth_service.refresh_access_token(data["refresh_token"])
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout(current_user=None):
    """
    Logout user by blacklisting token.

    Returns:
        Success message
    """
    auth_header = request.headers.get("Authorization")

    try:
        token = auth_header.split()[1]
        session = db.create_session()

        try:
            auth_service = AuthService(session)
            auth_service.logout(token, token_type="access")
            return jsonify({"message": "Successfully logged out"}), 200
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": "Failed to logout"}), 500


@app.route("/api/auth/password-reset/request", methods=["POST"])
@handle_auth_exception
def request_password_reset():
    """
    Request password reset token.

    Request JSON:
    {
        "email": "user@example.com"
    }

    Returns:
        Reset token and expiry information
    """
    data = request.get_json()

    if not data or not data.get("email"):
        return jsonify({"error": "email is required"}), 400

    session = db.create_session()

    try:
        auth_service = AuthService(session)
        result = auth_service.request_password_reset(data["email"])
        # In production, send email with reset token
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/api/auth/password-reset/confirm", methods=["POST"])
@handle_auth_exception
def confirm_password_reset():
    """
    Confirm password reset with token and new password.

    Request JSON:
    {
        "token": "eyJhbGc...",
        "new_password": "NewSecurePass123!"
    }

    Returns:
        JSON with new tokens
    """
    data = request.get_json()

    if not data or not data.get("token") or not data.get("new_password"):
        return jsonify({"error": "token and new_password are required"}), 400

    session = db.create_session()

    try:
        auth_service = AuthService(session)
        result = auth_service.confirm_password_reset(
            reset_token=data["token"],
            new_password=data["new_password"],
        )
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def get_current_user_profile(current_user=None):
    """
    Get current user profile.

    Returns:
        User profile data
    """
    session = db.create_session()

    try:
        user_service = UserService(session)
        user = user_service.get_user_by_id(current_user["user_id"])

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user.to_dict()), 200
    finally:
        session.close()


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


# ============================================================================
# Initialization
# ============================================================================

@app.before_request
def init_db():
    """Initialize database tables before first request."""
    if not hasattr(app, "db_initialized"):
        db.create_all_tables()
        app.db_initialized = True
        print("Database tables created/verified")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
