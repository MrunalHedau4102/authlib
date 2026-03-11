"""Tests for authentication service."""

import pytest
import pyotp
from authlib.services.auth_service import AuthService
from authlib.utils.exceptions import (
    UserNotFound,
    InvalidCredentials,
    InvalidToken,
    UserAlreadyExists,
    ValidationError,
    InvalidOTP,
)


class TestAuthService:
    """Test cases for AuthService."""

    def test_register_user(self, test_db_session, test_user_data):
        """Test user registration."""
        auth_service = AuthService(test_db_session)

        result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
        )

        assert "user" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["email"] == test_user_data["email"]
        assert result["token_type"] == "Bearer"

    def test_register_duplicate_user(self, test_db_session, test_user_data):
        """Test registering a duplicate user."""
        auth_service = AuthService(test_db_session)

        # Register first user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Try to register duplicate
        with pytest.raises(UserAlreadyExists):
            auth_service.register(
                email=test_user_data["email"],
                password=test_user_data["password"],
            )

    def test_register_invalid_email(self, test_db_session):
        """Test registration with invalid email."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(ValidationError):
            auth_service.register(
                email="invalid-email",
                password="ValidPass123!",
            )

    def test_register_weak_password(self, test_db_session):
        """Test registration with weak password."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(ValidationError):
            auth_service.register(
                email="test@example.com",
                password="weak",
            )

    def test_login_success(self, test_db_session, test_user_data):
        """Test successful login."""
        auth_service = AuthService(test_db_session)

        # Register user first
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Login
        result = auth_service.login(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        assert "user" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["email"] == test_user_data["email"]

    def test_login_user_not_found(self, test_db_session):
        """Test login with non-existent user."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(UserNotFound):
            auth_service.login(
                email="nonexistent@example.com",
                password="SomePass123!",
            )

    def test_login_wrong_password(self, test_db_session, test_user_data):
        """Test login with wrong password."""
        auth_service = AuthService(test_db_session)

        # Register user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Try to login with wrong password
        with pytest.raises(InvalidCredentials):
            auth_service.login(
                email=test_user_data["email"],
                password="WrongPassword456!",
            )

    def test_refresh_access_token(self, test_db_session, test_user_data):
        """Test refreshing access token."""
        auth_service = AuthService(test_db_session)

        # Register and login
        login_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        refresh_token = login_result["refresh_token"]

        # Refresh token
        result = auth_service.refresh_access_token(refresh_token)

        assert "access_token" in result
        assert result["token_type"] == "Bearer"

    def test_refresh_token_invalid(self, test_db_session):
        """Test refreshing with invalid token."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(InvalidToken):
            auth_service.refresh_access_token("invalid_token")

    def test_logout(self, test_db_session, test_user_data):
        """Test user logout."""
        auth_service = AuthService(test_db_session)

        # Register and login
        login_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        access_token = login_result["access_token"]

        # Logout
        auth_service.logout(access_token, token_type="access")

        # Try to verify token (should fail as it's blacklisted)
        with pytest.raises(InvalidToken):
            auth_service.verify_token(access_token)

    def test_request_password_reset(self, test_db_session, test_user_data):
        """Test password reset request."""
        auth_service = AuthService(test_db_session)

        # Register user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Request password reset
        result = auth_service.request_password_reset(test_user_data["email"])

        assert "reset_token" in result
        assert result["token_type"] == "Bearer"

    def test_request_password_reset_user_not_found(self, test_db_session):
        """Test password reset request for non-existent user."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(UserNotFound):
            auth_service.request_password_reset("nonexistent@example.com")

    def test_confirm_password_reset(self, test_db_session, test_user_data):
        """Test confirming password reset."""
        auth_service = AuthService(test_db_session)

        # Register user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Request password reset
        reset_result = auth_service.request_password_reset(test_user_data["email"])
        reset_token = reset_result["reset_token"]

        # Confirm password reset
        new_password = "NewPassword789!"
        result = auth_service.confirm_password_reset(reset_token, new_password)

        assert "user" in result
        assert "access_token" in result

        # Verify can login with new password
        login_result = auth_service.login(
            email=test_user_data["email"],
            password=new_password,
        )
        assert login_result["user"]["email"] == test_user_data["email"]

    def test_confirm_password_reset_invalid_token(self, test_db_session):
        """Test password reset with invalid token."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(InvalidToken):
            auth_service.confirm_password_reset("invalid_token", "NewPass123!")

    def test_verify_token(self, test_db_session, test_user_data):
        """Test token verification."""
        auth_service = AuthService(test_db_session)

        # Register and get token
        login_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        access_token = login_result["access_token"]

        # Verify token
        payload = auth_service.verify_token(access_token)

        assert payload["user_id"] is not None
        assert payload["email"] == test_user_data["email"]

    def test_verify_invalid_token(self, test_db_session):
        """Test verification of invalid token."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(InvalidToken):
            auth_service.verify_token("invalid_token")
    # ============== 2FA Tests ==============

    def test_setup_2fa(self, test_db_session, test_user_data):
        """Test 2FA setup generates secret and URI."""
        auth_service = AuthService(test_db_session)

        # Register user first
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        # Setup 2FA
        result = auth_service.setup_2fa(user_id)

        assert "secret" in result
        assert "provisioning_uri" in result
        assert result["provisioning_uri"].startswith("otpauth://totp/")
        # Email is URL-encoded in the provisioning URI
        assert "test%40example.com" in result["provisioning_uri"] or test_user_data["email"] in result["provisioning_uri"]
        assert "AuthLib" in result["provisioning_uri"]

    def test_setup_2fa_user_not_found(self, test_db_session):
        """Test 2FA setup with non-existent user."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(UserNotFound):
            auth_service.setup_2fa(9999)

    def test_verify_2fa_setup_with_valid_otp(self, test_db_session, test_user_data):
        """Test 2FA setup verification with valid OTP."""
        auth_service = AuthService(test_db_session)

        # Register user
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        # Setup 2FA and get secret
        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]

        # Generate valid OTP code
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        # Verify 2FA setup
        result = auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        assert result is True

        # Verify user has 2FA enabled
        user = auth_service.user_service.get_user_by_id(user_id)
        assert user.is_two_factor_enabled is True
        assert user.two_factor_secret == secret

    def test_verify_2fa_setup_with_invalid_otp(self, test_db_session, test_user_data):
        """Test 2FA setup verification with invalid OTP."""
        auth_service = AuthService(test_db_session)

        # Register user
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        # Setup 2FA
        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]

        # Try with invalid OTP code
        with pytest.raises(InvalidOTP):
            auth_service.verify_2fa_setup_with_secret(user_id, secret, "000000")

        # Verify user does NOT have 2FA enabled
        user = auth_service.user_service.get_user_by_id(user_id)
        assert user.is_two_factor_enabled is False

    def test_verify_2fa_setup_invalid_format(self, test_db_session, test_user_data):
        """Test 2FA setup with invalid OTP format."""
        auth_service = AuthService(test_db_session)

        # Register user
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        # Setup 2FA
        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]

        # Try with invalid format
        with pytest.raises(ValidationError):
            auth_service.verify_2fa_setup_with_secret(user_id, secret, "12345")  # 5 digits

        with pytest.raises(ValidationError):
            auth_service.verify_2fa_setup_with_secret(user_id, secret, "abcdef")  # letters

    def test_login_without_2fa(self, test_db_session, test_user_data):
        """Test login without 2FA enabled."""
        auth_service = AuthService(test_db_session)

        # Register user
        auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        # Login should return tokens directly
        result = auth_service.login(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        assert "user" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert "requires_2fa" not in result or result.get("requires_2fa") is False

    def test_login_with_2fa_enabled(self, test_db_session, test_user_data):
        """Test login with 2FA enabled returns verification token."""
        auth_service = AuthService(test_db_session)

        # Register user
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        # Enable 2FA
        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Login should return OTP verification token
        result = auth_service.login(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )

        assert result["requires_2fa"] is True
        assert "otp_verification_token" in result
        assert "access_token" not in result
        assert "refresh_token" not in result
        assert result["user_id"] == user_id

    def test_verify_otp_valid_code(self, test_db_session, test_user_data):
        """Test OTP verification with valid code."""
        auth_service = AuthService(test_db_session)

        # Setup user with 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Verify OTP during login
        new_otp_code = totp.now()
        result = auth_service.verify_otp(user_id, new_otp_code)

        assert result is True

    def test_verify_otp_invalid_code(self, test_db_session, test_user_data):
        """Test OTP verification with invalid code."""
        auth_service = AuthService(test_db_session)

        # Setup user with 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Try invalid OTP
        with pytest.raises(InvalidOTP):
            auth_service.verify_otp(user_id, "000000")

    def test_complete_2fa_login(self, test_db_session, test_user_data):
        """Test completing login with 2FA."""
        auth_service = AuthService(test_db_session)

        # Setup user with 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Get verification token from login
        login_result = auth_service.login(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        otp_verification_token = login_result["otp_verification_token"]

        # Complete login with OTP code
        new_otp_code = totp.now()
        result = auth_service.complete_2fa_login(otp_verification_token, new_otp_code)

        assert "user" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "Bearer"

    def test_complete_2fa_login_with_invalid_token(self, test_db_session, test_user_data):
        """Test 2FA login with invalid verification token."""
        auth_service = AuthService(test_db_session)

        with pytest.raises(InvalidToken):
            auth_service.complete_2fa_login("invalid_token", "123456")

    def test_complete_2fa_login_with_invalid_otp(self, test_db_session, test_user_data):
        """Test 2FA login with invalid OTP code."""
        auth_service = AuthService(test_db_session)

        # Setup user with 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Get verification token
        login_result = auth_service.login(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        otp_verification_token = login_result["otp_verification_token"]

        # Try with invalid OTP
        with pytest.raises(InvalidOTP):
            auth_service.complete_2fa_login(otp_verification_token, "000000")

    def test_disable_2fa_success(self, test_db_session, test_user_data):
        """Test disabling 2FA."""
        auth_service = AuthService(test_db_session)

        # Setup user with 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Disable 2FA
        result = auth_service.disable_2fa(
            user_id=user_id,
            user_password=test_user_data["password"],
        )

        assert result is True

        # Verify 2FA is disabled
        user = auth_service.user_service.get_user_by_id(user_id)
        assert user.is_two_factor_enabled is False
        assert user.two_factor_secret is None

    def test_disable_2fa_with_wrong_password(self, test_db_session, test_user_data):
        """Test disabling 2FA with wrong password."""
        auth_service = AuthService(test_db_session)

        # Setup user with 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Try to disable with wrong password
        with pytest.raises(InvalidCredentials):
            auth_service.disable_2fa(
                user_id=user_id,
                user_password="WrongPassword123!",
            )

    def test_disable_2fa_without_2fa_enabled(self, test_db_session, test_user_data):
        """Test disabling 2FA when not enabled."""
        auth_service = AuthService(test_db_session)

        # Register user without 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        # Try to disable 2FA
        with pytest.raises(ValidationError):
            auth_service.disable_2fa(
                user_id=user_id,
                user_password=test_user_data["password"],
            )

    def test_disable_2fa_with_valid_otp(self, test_db_session, test_user_data):
        """Test disabling 2FA with OTP verification."""
        auth_service = AuthService(test_db_session)

        # Setup user with 2FA
        register_result = auth_service.register(
            email=test_user_data["email"],
            password=test_user_data["password"],
        )
        user_id = register_result["user"]["id"]

        setup_result = auth_service.setup_2fa(user_id)
        secret = setup_result["secret"]
        totp = pyotp.TOTP(secret)
        otp_code = totp.now()

        auth_service.verify_2fa_setup_with_secret(user_id, secret, otp_code)

        # Disable with OTP verification
        new_otp_code = totp.now()
        result = auth_service.disable_2fa(
            user_id=user_id,
            user_password=test_user_data["password"],
            otp_code=new_otp_code,
        )

        assert result is True

        # Verify 2FA is disabled
        user = auth_service.user_service.get_user_by_id(user_id)
        assert user.is_two_factor_enabled is False