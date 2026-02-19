# Quick Start Guide - AuthLib

Get up and running with AuthLib in 5 minutes!

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/authlib.git
cd authlib

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Setup

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Minimum required:
JWT_SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/authlib_db
```

### 2. Initialize Database

```bash
python -c "from authlib.database import db; db.create_all_tables()"
```

### 3. Run Tests (Optional)

```bash
pip install -e ".[dev]"
pytest tests/
```

## Usage Examples

### Using with FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from authlib.database import db
from authlib.services.auth_service import AuthService

app = FastAPI()

def get_db():
    session = db.create_session()
    try:
        yield session
    finally:
        session.close()

@app.post("/signup")
def signup(email: str, password: str, session: Session = Depends(get_db)):
    auth_service = AuthService(session)
    result = auth_service.register(email=email, password=password)
    return result

@app.post("/login")
def login(email: str, password: str, session: Session = Depends(get_db)):
    auth_service = AuthService(session)
    result = auth_service.login(email=email, password=password)
    return result

# See examples/fastapi_example.py for complete example
```

### Using with Flask

```python
from flask import Flask, request, jsonify
from authlib.services.auth_service import AuthService
from authlib.database import db

app = Flask(__name__)

@app.route("/signup", methods=["POST"])
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

# See examples/flask_example.py for complete example
```

## API Endpoints

### Authentication

**POST /auth/signup**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```
Returns: `{user, access_token, refresh_token}`

**POST /auth/login**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```
Returns: `{user, access_token, refresh_token}`

**POST /auth/refresh**
```json
{
  "refresh_token": "eyJhbGc..."
}
```
Returns: `{access_token, token_type}`

**POST /auth/logout**
- Headers: `Authorization: Bearer {access_token}`
- Returns: `{message: "Successfully logged out"}`

### Password Reset

**POST /auth/password-reset/request**
```json
{
  "email": "user@example.com"
}
```
Returns: `{reset_token, expires_in}`

**POST /auth/password-reset/confirm**
```json
{
  "token": "eyJhbGc...",
  "new_password": "NewSecurePass456!"
}
```
Returns: `{user, access_token, refresh_token}`

## Protected Routes

### FastAPI

```python
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected")
def protected_route(credentials = Depends(security)):
    token = credentials.credentials
    auth_service = AuthService(session)
    payload = auth_service.verify_token(token)
    return {"message": f"Hello, user {payload['user_id']}"}
```

### Flask

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
        except:
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    return decorated

@app.route("/protected")
@require_auth
def protected_route(user=None):
    return {"message": f"Hello, user {user['user_id']}"}
```

## Configuration Reference

Essential configuration variables:

```env
# JWT
JWT_SECRET_KEY=your-secret-key          # Change in production!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRY_DAYS=7

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Email (optional, for password reset emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=noreply@yourapp.com

# Security
APP_ENV=production
BCRYPT_LOG_ROUNDS=12
```

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server
```
**Solution**: Ensure PostgreSQL is running and `DATABASE_URL` is correct.

### JWT Secret Key Error
```
Error: JWT_SECRET_KEY must be set for production
```
**Solution**: Set `JWT_SECRET_KEY` in `.env` file with a strong random key.

### Password Validation Error
```
ValidationError: Password must contain...
```
**Solution**: Password must be 8+ chars with uppercase, lowercase, digit, and special character.

### Email Sending Error
```
EmailSendError: Failed to send email
```
**Solution**: Check SMTP credentials and `APP_ENV` is not 'testing'.

## Next Steps

- Read [README.md](../README.md) for detailed documentation
- Explore [ARCHITECTURE.md](../docs/ARCHITECTURE.md) for design details
- Run [fastapi_example.py](../examples/fastapi_example.py) or [flask_example.py](../examples/flask_example.py)
- Check [tests/](../tests/) for usage examples
- Customize validators and email templates for your app

## Support

- Documentation: [README.md](../README.md)
- Issues: GitHub Issues
- Email: support@authlib.dev

---

Happy building! 🚀
