# AuthLib - Python Authentication Library

A scalable, framework-agnostic Python authentication library with JWT token management, user registration, login, and password reset functionality. Designed for minimal overhead and maximum flexibility for integration across web, mobile, and other applications.

## Features

✨ **Core Features**
- User registration and login with email/password
- JWT-based access and refresh tokens
- Password reset flow with email verification
- Token blacklisting for logout and revocation
- User account management (activation/deactivation)
- Password strength validation and bcrypt hashing

🔧 **Technical Features**
- **Framework-agnostic**: Pure Python, no framework dependencies
- **Minimal dependencies**: Only SQLAlchemy, PyJWT, bcrypt, Pydantic, python-dotenv
- **Production-ready**: Type hints, error handling, comprehensive tests
- **Extensible**: Well-structured for custom integrations
- **Database-agnostic**: SQLAlchemy ORM supports PostgreSQL, MySQL, SQLite, etc.
- **Async-ready**: Services are stateless and can be used with async frameworks

## Installation

### 1. Install from source

```bash
git clone https://github.com/yourusername/authlib.git
cd authlib
pip install -r requirements.txt
```

### 2. Install with pip (when published)

```bash
pip install authlib
```

### 3. Install with optional dependencies

```bash
# With FastAPI support
pip install authlib[fastapi]

# With Flask support
pip install authlib[flask]

# With PostgreSQL support
pip install authlib[psycopg]

# With development tools
pip install authlib[dev]
```

## Quick Start

### 1. Set up environment

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
JWT_SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=postgresql://user:password@localhost:5432/authlib_db
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 2. Initialize database

```python
from authlib.database import db

# Create all tables
db.create_all_tables()
```

### 3. Use in your application

#### Basic Usage

```python
from sqlalchemy.orm import Session
from authlib.services.auth_service import AuthService
from authlib.database import db

# Get database session
session = db.create_session()

# Initialize auth service
auth_service = AuthService(session)

# Register user
result = auth_service.register(
    email="user@example.com",
    password="SecurePass123!",
    first_name="John",
    last_name="Doe"
)

print(result["access_token"])  # Access token for API requests
print(result["refresh_token"])  # Refresh token for getting new access tokens
```

#### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from authlib.database import db
from authlib.services.auth_service import AuthService

app = FastAPI()

@app.post("/auth/signup")
def signup(email: str, password: str, session: Session = Depends(get_db)):
    auth_service = AuthService(session)
    result = auth_service.register(email=email, password=password)
    return result

@app.post("/auth/login")
def login(email: str, password: str, session: Session = Depends(get_db)):
    auth_service = AuthService(session)
    result = auth_service.login(email=email, password=password)
    return result
```

See [examples/fastapi_example.py](examples/fastapi_example.py) for complete FastAPI integration.

#### Flask Integration

```python
from flask import Flask, request, jsonify
from authlib.services.auth_service import AuthService
from authlib.database import db

app = Flask(__name__)

@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    session = db.create_session()
    try:
        auth_service = AuthService(session)
        result = auth_service.register(
            email=data["email"],
            password=data["password"]
        )
        return jsonify(result), 201
    finally:
        session.close()
```

See [examples/flask_example.py](examples/flask_example.py) for complete Flask integration.

## API Reference

### AuthService

Main service for authentication operations.

#### Methods

**`register(email, password, first_name=None, last_name=None) -> dict`**
- Register a new user
- Returns: `{"user": {...}, "access_token": "...", "refresh_token": "..."}`
- Raises: `UserAlreadyExists`, `ValidationError`

**`login(email, password) -> dict`**
- Authenticate user and get tokens
- Returns: Same as register
- Raises: `UserNotFound`, `InvalidCredentials`

**`refresh_access_token(refresh_token) -> dict`**
- Get new access token using refresh token
- Returns: `{"access_token": "...", "token_type": "Bearer"}`
- Raises: `InvalidToken`

**`logout(token, token_type="access") -> None`**
- Revoke a token
- Raises: `InvalidToken`

**`request_password_reset(email) -> dict`**
- Generate password reset token
- Returns: `{"reset_token": "...", "expires_in": 3600}`
- Raises: `UserNotFound`

**`confirm_password_reset(reset_token, new_password) -> dict`**
- Confirm password reset and get new tokens
- Returns: Same as register
- Raises: `InvalidToken`, `ValidationError`

**`verify_token(token) -> dict`**
- Verify and decode access token
- Returns: Token payload with `user_id` and `email`
- Raises: `InvalidToken`

### UserService

Service for user management operations.

#### Methods

**`create_user(email, password, first_name=None, last_name=None) -> User`**
- Create new user in database
- Raises: `UserAlreadyExists`, `ValidationError`

**`get_user_by_id(user_id) -> Optional[User]`**
- Get user by ID

**`get_user_by_email(email) -> Optional[User]`**
- Get user by email

**`update_user(user_id, email=None, first_name=None, ...) -> User`**
- Update user information
- Raises: `UserNotFound`

**`change_password(user_id, new_password) -> User`**
- Change user password
- Raises: `UserNotFound`

**`delete_user(user_id) -> None`**
- Delete user account
- Raises: `UserNotFound`

**`verify_user(user_id) -> User`**
- Mark user as verified

**`deactivate_user(user_id) -> User`**
- Deactivate user account

**`activate_user(user_id) -> User`**
- Activate user account

## Configuration

All configuration is done via environment variables (or `.env` file).

### JWT Configuration

```env
JWT_SECRET_KEY=your-secret-key               # Secret key for signing tokens
JWT_ALGORITHM=HS256                           # Algorithm for token signing
JWT_ACCESS_TOKEN_EXPIRY_MINUTES=15           # Access token expiry time
JWT_REFRESH_TOKEN_EXPIRY_DAYS=7              # Refresh token expiry time
```

### Database Configuration

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/authlib_db
```

Supported databases:
- PostgreSQL: `postgresql://user:pass@host:port/dbname`
- MySQL: `mysql+pymysql://user:pass@host:port/dbname`
- SQLite: `sqlite:///path/to/database.db`

### Email Configuration

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=noreply@yourapp.com
PASSWORD_RESET_REDIRECT_URL=https://yourapp.com/reset-password
```

### Security Configuration

```env
APP_ENV=production                           # development, production, testing
BCRYPT_LOG_ROUNDS=12                         # Cost factor for bcrypt hashing
```

## Password Requirements

By default, passwords must meet these requirements:
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*...)

Customize in [authlib/utils/validators.py](authlib/utils/validators.py).

## Examples

### Complete Authentication Flow

```python
from authlib.services.auth_service import AuthService
from authlib.services.email_service import EmailService
from authlib.database import db

session = db.create_session()

# 1. Register user
auth = AuthService(session)
register_result = auth.register(
    email="john@example.com",
    password="SecurePass123!"
)
access_token = register_result["access_token"]

# 2. User can now login
login_result = auth.login(
    email="john@example.com",
    password="SecurePass123!"
)

# 3. Refresh access token when expired
refresh_result = auth.refresh_access_token(
    login_result["refresh_token"]
)

# 4. Request password reset
reset_result = auth.request_password_reset("john@example.com")
reset_token = reset_result["reset_token"]

# 5. Send email with reset token (optional)
email_service = EmailService()
email_service.send_password_reset_email(
    to_email="john@example.com",
    reset_token=reset_token,
    user_name="John"
)

# 6. Confirm password reset
new_login = auth.confirm_password_reset(
    reset_token=reset_token,
    new_password="NewSecurePass456!"
)

# 7. Logout (revoke token)
auth.logout(access_token, token_type="access")

session.close()
```

### Protecting Routes

**With FastAPI:**

```python
from fastapi import Depends, HTTPException

@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    auth_service = AuthService(session)
    try:
        payload = auth_service.verify_token(token)
        return {"user_id": payload["user_id"]}
    except InvalidToken:
        raise HTTPException(status_code=401)
```

**With Flask:**

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        auth_service = AuthService(session)
        try:
            payload = auth_service.verify_token(token)
            kwargs["user"] = payload
        except InvalidToken:
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    return decorated

@app.route("/protected")
@require_auth
def protected_route(user=None):
    return {"user_id": user["user_id"]}
```

## Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=authlib tests/

# Run specific test
pytest tests/test_auth_service.py::TestAuthService::test_register_user
```

## Error Handling

AuthLib defines specific exceptions for different scenarios:

```python
from authlib.utils.exceptions import (
    AuthException,           # Base exception
    UserNotFound,           # User doesn't exist
    InvalidCredentials,     # Wrong password
    InvalidToken,           # Token invalid/expired
    UserAlreadyExists,      # Duplicate email
    ValidationError,        # Invalid input
    DatabaseError,          # DB operation failed
    EmailSendError,         # Email sending failed
)

try:
    auth.login(email, password)
except UserNotFound:
    print("User doesn't exist")
except InvalidCredentials:
    print("Wrong password")
except InvalidToken:
    print("Token expired")
```

## Security Best Practices

1. **Environment Variables**: Never commit `.env` file to version control
2. **Secret Key**: Use strong, random `JWT_SECRET_KEY` in production
3. **HTTPS**: Always use HTTPS in production to prevent token interception
4. **Token Expiry**: Keep access token expiry short (15 mins) and refresh token expiry moderate (7 days)
5. **Password Reset**: Implement email verification before confirming password reset
6. **Rate Limiting**: Add rate limiting to login and password reset endpoints
7. **CORS**: Configure CORS properly to prevent cross-origin attacks
8. **Database**: Use strong database passwords and enable encryption

## Database Schema

### users table
- `id` (Primary Key, Integer)
- `email` (String, Unique)
- `password_hash` (String)
- `first_name` (String, Nullable)
- `last_name` (String, Nullable)
- `is_active` (Boolean)
- `is_verified` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `last_login` (DateTime, Nullable)

### token_blacklist table
- `id` (Primary Key, Integer)
- `jti` (String, Unique) - JWT ID
- `user_id` (Integer, Foreign Key)
- `token_type` (String)
- `reason` (String, Nullable)
- `revoked_at` (DateTime)
- `expires_at` (DateTime)

## Project Structure

```
authlib/
├── authlib/                           # Main package
│   ├── __init__.py
│   ├── config.py                      # Configuration management
│   ├── database.py                    # Database setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                    # User model
│   │   └── token_blacklist.py         # Token blacklist model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py            # Core auth logic
│   │   ├── user_service.py            # User CRUD
│   │   └── email_service.py           # Email sending
│   └── utils/
│       ├── __init__.py
│       ├── jwt_handler.py             # JWT utilities
│       ├── password.py                # Password hashing
│       ├── exceptions.py              # Custom exceptions
│       └── validators.py              # Input validation
├── examples/
│   ├── fastapi_example.py             # FastAPI integration
│   └── flask_example.py               # Flask integration
├── tests/                             # Test suite
│   ├── conftest.py
│   ├── test_auth_service.py
│   ├── test_user_service.py
│   ├── test_jwt_handler.py
│   ├── test_password.py
│   └── test_validators.py
├── docs/
│   ├── README.md                      # This file
│   └── ARCHITECTURE.md                # Architecture documentation
├── requirements.txt                   # Production dependencies
├── setup.py                           # Package setup
├── pyproject.toml                     # Project configuration
└── .env.example                       # Example environment file
```

## Deployment

### With Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY authlib/ authlib/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

### On Heroku

```bash
git push heroku main
heroku config:set JWT_SECRET_KEY=your-secret-key
heroku run python -c "from authlib.database import db; db.create_all_tables()"
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: [Create an issue](https://github.com/yourusername/authlib/issues)
- **Discussions**: [Community discussions](https://github.com/yourusername/authlib/discussions)
- **Email**: support@authlib.dev

## Roadmap

- [ ] Email verification on signup
- [ ] Two-factor authentication (2FA)
- [ ] OAuth2 provider support
- [ ] Redis-based token blacklist for high-scale
- [ ] GraphQL API example
- [ ] Admin dashboard
- [ ] Audit logging

## Changelog

### v1.0.0 (Initial Release)
- User registration and login
- JWT access and refresh tokens
- Password reset flow
- Token blacklisting
- Password hashing with bcrypt
- Email service
- FastAPI and Flask examples
- Comprehensive test suite

---

**Made with ❤️ by [Your Team]**
