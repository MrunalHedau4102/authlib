"""Tests for EmailService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from authlib.services.email_service import EmailService
from authlib.config import Config
from authlib.utils.exceptions import EmailSendError


@pytest.fixture
def email_config():
    """Create test email config."""
    config = Config()
    config.SMTP_SERVER = "smtp.test.com"
    config.SMTP_PORT = 587
    config.SMTP_USERNAME = "test@example.com"
    config.SMTP_PASSWORD = "password123"
    config.SENDER_EMAIL = "noreply@authlib.com"
    config.PASSWORD_RESET_REDIRECT_URL = "https://app.com/reset"
    config.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 60
    return config


@pytest.fixture
def email_service(email_config):
    """Create EmailService instance."""
    return EmailService(config=email_config)


class TestEmailServiceInit:
    """Test EmailService initialization."""

    def test_init_with_config(self, email_config):
        """Test initialization with config."""
        service = EmailService(config=email_config)
        assert service.config == email_config

    def test_init_without_config(self):
        """Test initialization without config (uses default)."""
        service = EmailService()
        assert service.config is not None


class TestSendEmail:
    """Test email sending functionality."""

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp, email_service):
        """Test successful email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_content="<p>Test content</p>",
            plain_text="Test content",
        )

        assert result is True
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_without_plain_text(self, mock_smtp, email_service):
        """Test sending email with only HTML content."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_content="<p>Test content</p>",
        )

        assert result is True
        mock_server.sendmail.assert_called_once()

    def test_send_email_missing_required_fields(self, email_service):
        """Test sending email with missing required fields."""
        # Missing to_email
        with pytest.raises(ValueError):
            email_service.send_email(
                to_email="",
                subject="Test",
                html_content="<p>Test</p>",
            )

        # Missing subject
        with pytest.raises(ValueError):
            email_service.send_email(
                to_email="user@example.com",
                subject="",
                html_content="<p>Test</p>",
            )

        # Missing html_content
        with pytest.raises(ValueError):
            email_service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_content="",
            )

    @patch("smtplib.SMTP")
    def test_send_email_smtp_error(self, mock_smtp, email_service):
        """Test sending email with SMTP error."""
        import smtplib

        mock_smtp.return_value.__enter__.return_value.login.side_effect = (
            smtplib.SMTPException("SMTP error")
        )

        with pytest.raises(EmailSendError) as exc_info:
            email_service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_content="<p>Test</p>",
            )

        assert "Failed to send email" in str(exc_info.value)

    @patch("smtplib.SMTP")
    def test_send_email_unexpected_error(self, mock_smtp, email_service):
        """Test sending email with unexpected error."""
        mock_smtp.return_value.__enter__.side_effect = Exception("Unexpected error")

        with pytest.raises(EmailSendError) as exc_info:
            email_service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_content="<p>Test</p>",
            )

        assert "Unexpected error" in str(exc_info.value)


class TestPasswordResetEmail:
    """Test password reset email."""

    @patch("smtplib.SMTP")
    def test_send_password_reset_email_success(self, mock_smtp, email_service):
        """Test successful password reset email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token_12345",
            user_name="John Doe",
        )

        assert result is True
        mock_server.sendmail.assert_called_once()

        # Verify email content
        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "Password Reset Request" in email_content
        assert "John Doe" in email_content

    @patch("smtplib.SMTP")
    def test_send_password_reset_email_without_name(self, mock_smtp, email_service):
        """Test password reset email without user name."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token_12345",
        )

        assert result is True
        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "Hello," in email_content

    @patch("smtplib.SMTP")
    def test_password_reset_email_includes_token(self, mock_smtp, email_service):
        """Test that password reset email includes the token."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        reset_token = "test_token_xyz789"
        email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token=reset_token,
        )

        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert reset_token in email_content

    @patch("smtplib.SMTP")
    def test_password_reset_email_includes_expiry(self, mock_smtp, email_service):
        """Test that password reset email includes token expiry time."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="test_token",
        )

        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "60 minutes" in email_content  # PASSWORD_RESET_TOKEN_EXPIRY_MINUTES

    @patch("smtplib.SMTP")
    def test_password_reset_email_error(self, mock_smtp, email_service):
        """Test password reset email error handling."""
        import smtplib

        mock_smtp.return_value.__enter__.return_value.sendmail.side_effect = (
            smtplib.SMTPException("SMTP error")
        )

        with pytest.raises(EmailSendError):
            email_service.send_password_reset_email(
                to_email="user@example.com",
                reset_token="test_token",
            )


class TestWelcomeEmail:
    """Test welcome email."""

    @patch("smtplib.SMTP")
    def test_send_welcome_email_success(self, mock_smtp, email_service):
        """Test successful welcome email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_welcome_email(
            to_email="newuser@example.com",
            user_name="Jane Smith",
        )

        assert result is True
        mock_server.sendmail.assert_called_once()

        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "Welcome to AuthLib" in email_content
        assert "Jane Smith" in email_content

    @patch("smtplib.SMTP")
    def test_send_welcome_email_without_name(self, mock_smtp, email_service):
        """Test welcome email without user name."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_welcome_email(
            to_email="newuser@example.com",
        )

        assert result is True
        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "Hello," in email_content

    @patch("smtplib.SMTP")
    def test_welcome_email_error(self, mock_smtp, email_service):
        """Test welcome email error handling."""
        import smtplib

        mock_smtp.return_value.__enter__.return_value.sendmail.side_effect = (
            smtplib.SMTPException("SMTP error")
        )

        with pytest.raises(EmailSendError):
            email_service.send_welcome_email(
                to_email="newuser@example.com",
            )


class TestVerificationEmail:
    """Test email verification email."""

    @patch("smtplib.SMTP")
    def test_send_verification_email_success(self, mock_smtp, email_service):
        """Test successful verification email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_verification_email(
            to_email="user@example.com",
            verification_token="verify_token_123",
            user_name="John User",
        )

        assert result is True
        mock_server.sendmail.assert_called_once()

        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "Verify Your Email" in email_content
        assert "John User" in email_content

    @patch("smtplib.SMTP")
    def test_send_verification_email_without_name(self, mock_smtp, email_service):
        """Test verification email without user name."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_verification_email(
            to_email="user@example.com",
            verification_token="verify_token_123",
        )

        assert result is True

    @patch("smtplib.SMTP")
    def test_verification_email_includes_token(self, mock_smtp, email_service):
        """Test that verification email includes the token."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        verify_token = "verify_abc123xyz"
        email_service.send_verification_email(
            to_email="user@example.com",
            verification_token=verify_token,
        )

        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert verify_token in email_content

    @patch("smtplib.SMTP")
    def test_verification_email_error(self, mock_smtp, email_service):
        """Test verification email error handling."""
        import smtplib

        mock_smtp.return_value.__enter__.return_value.sendmail.side_effect = (
            smtplib.SMTPException("SMTP error")
        )

        with pytest.raises(EmailSendError):
            email_service.send_verification_email(
                to_email="user@example.com",
                verification_token="verify_token",
            )


class TestEmailServiceConfiguration:
    """Test email service configuration."""

    @patch("smtplib.SMTP")
    def test_uses_correct_smtp_server(self, mock_smtp, email_service, email_config):
        """Test that correct SMTP server is used."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        mock_smtp.assert_called_with(
            email_config.SMTP_SERVER,
            email_config.SMTP_PORT,
            timeout=10,
        )

    @patch("smtplib.SMTP")
    def test_uses_correct_credentials(self, mock_smtp, email_service, email_config):
        """Test that correct credentials are used."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        mock_server.login.assert_called_with(
            email_config.SMTP_USERNAME,
            email_config.SMTP_PASSWORD,
        )

    @patch("smtplib.SMTP")
    def test_uses_correct_sender_email(self, mock_smtp, email_service, email_config):
        """Test that correct sender email is used."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        call_args = mock_server.sendmail.call_args
        sender = call_args[0][0]
        assert sender == email_config.SENDER_EMAIL
