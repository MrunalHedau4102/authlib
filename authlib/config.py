"""Configuration management for AuthLib."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-secret-key-change-this-in-production"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRY_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRY_MINUTES", "15")
    )
    JWT_REFRESH_TOKEN_EXPIRY_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRY_DAYS", "7")
    )

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/authlib_db"
    )

    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "noreply@authlib.com")

    # Application Configuration
    APP_NAME: str = os.getenv("APP_NAME", "AuthLib")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Password Reset Configuration
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES: int = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", "60")
    )
    PASSWORD_RESET_REDIRECT_URL: Optional[str] = os.getenv(
        "PASSWORD_RESET_REDIRECT_URL"
    )

    # Bcrypt Configuration
    BCRYPT_LOG_ROUNDS: int = int(os.getenv("BCRYPT_LOG_ROUNDS", "12"))

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        if cls.APP_ENV == "production":
            if cls.JWT_SECRET_KEY == "your-secret-key-change-this-in-production":
                raise ValueError(
                    "JWT_SECRET_KEY must be set for production environment"
                )
            if not cls.SMTP_USERNAME or not cls.SMTP_PASSWORD:
                raise ValueError(
                    "SMTP credentials must be set for production environment"
                )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    APP_ENV = "development"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    APP_ENV = "production"


class TestConfig(Config):
    """Test configuration."""
    DATABASE_URL = "postgresql://user:password@localhost:5432/authlib_test_db"
    JWT_SECRET_KEY = "test-secret-key"
    SMTP_USERNAME = "test@example.com"
    SMTP_PASSWORD = "test-password"
    APP_ENV = "testing"


# Get configuration based on environment
def get_config() -> Config:
    """Get appropriate config based on APP_ENV."""
    env = os.getenv("APP_ENV", "development").lower()

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestConfig,
    }

    return config_map.get(env, DevelopmentConfig)()
