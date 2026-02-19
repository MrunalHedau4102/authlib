"""
FastAPI example integration with AuthLib

Shows how to integrate AuthLib with FastAPI for building
a complete authentication API.

Run with: uvicorn examples.fastapi_example:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
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
# Pydantic Models for Request/Response
# ============================================================================

class SignupRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    first_name: str = None
    last_name: str = None


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class ConfirmPasswordResetRequest(BaseModel):
    """Confirm password reset request."""
    token: str
    new_password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str = None
    token_type: str = "Bearer"


class UserResponse(BaseModel):
    """User response."""
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class AuthResponse(BaseModel):
    """Authentication response."""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="AuthLib API",
    description="Authentication API built with AuthLib and FastAPI",
    version="1.0.0",
)

security = HTTPBearer()


# ============================================================================
# Dependency Injection
# ============================================================================

def get_db_session() -> Session:
    """Get database session."""
    return db.create_session()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db_session),
):
    """Get current user from JWT token."""
    token = credentials.credentials

    try:
        auth_service = AuthService(session)
        payload = auth_service.verify_token(token)
        print(f"Token payload: {payload}")  # Debugging statement
        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidToken("Invalid token payload")

        return payload  # ✅ return token payload only

    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    finally:
        session.close()



# ============================================================================
# Routes
# ============================================================================

@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(
    request: SignupRequest,
    session: Session = Depends(get_db_session),
):
    """
    Register a new user.
    
    Args:
        request: Signup request with email, password, and optional name
        session: Database session
        
    Returns:
        AuthResponse with user data and tokens
    """
    try:
        auth_service = AuthService(session)
        result = auth_service.register(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        return result
    except UserAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        session.close()


@app.post("/api/auth/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    session: Session = Depends(get_db_session),
):
    """
    Authenticate user and return tokens.
    
    Args:
        request: Login request with email and password
        session: Database session
        
    Returns:
        AuthResponse with user data and tokens
    """
    try:
        auth_service = AuthService(session)
        result = auth_service.login(
            email=request.email,
            password=request.password,
        )
        return result
    except (UserNotFound, InvalidCredentials) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        session.close()


@app.post("/api/auth/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_db_session),
):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        session: Database session
        
    Returns:
        TokenResponse with new access token
    """
    try:
        auth_service = AuthService(session)
        result = auth_service.refresh_access_token(request.refresh_token)
        return result
    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        session.close()


@app.post("/api/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db_session),
):
    """
    Logout user by blacklisting token.
    
    Args:
        credentials: Bearer token
        session: Database session
        
    Returns:
        Success message
    """
    try:
        token = credentials.credentials
        auth_service = AuthService(session)
        auth_service.logout(token, token_type="access")
        return {"message": "Successfully logged out"}
    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        session.close()


@app.post("/api/auth/password-reset/request")
def request_password_reset(
    request: PasswordResetRequest,
    session: Session = Depends(get_db_session),
):
    """
    Request password reset token.
    
    Args:
        request: Password reset request with email
        session: Database session
        
    Returns:
        Reset token and expiry information
    """
    try:
        auth_service = AuthService(session)
        result = auth_service.request_password_reset(request.email)
        # In production, send email with reset token
        return result
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        session.close()


@app.post("/api/auth/password-reset/confirm", response_model=AuthResponse)
def confirm_password_reset(
    request: ConfirmPasswordResetRequest,
    session: Session = Depends(get_db_session),
):
    """
    Confirm password reset with token and new password.
    
    Args:
        request: Confirm password reset request
        session: Database session
        
    Returns:
        AuthResponse with new tokens
    """
    try:
        auth_service = AuthService(session)
        result = auth_service.confirm_password_reset(
            reset_token=request.token,
            new_password=request.new_password,
        )
        return result
    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        session.close()


@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_profile(
    current_user = Depends(get_current_user),
):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    return {
        "id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "first_name": current_user.get("first_name"),
        "last_name": current_user.get("last_name"),
        "is_active": current_user.get("is_active"),
        "is_verified": current_user.get("is_verified"),
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Initialization
# ============================================================================

@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup."""
    db.create_all_tables()
    print("Database tables created/verified")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
