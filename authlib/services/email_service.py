"""Email service for sending authentication-related emails."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from authlib.config import Config
from authlib.utils.exceptions import EmailSendError


class EmailService:
    """Service for sending emails."""

    def __init__(self, config: Config = None) -> None:
        """
        Initialize EmailService.

        Args:
            config: Config object (uses default if not provided)
        """
        self.config = config or Config()

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text: Plain text email body (optional)

        Returns:
            True if email sent successfully

        Raises:
            EmailSendError: If email sending fails
        """
        if not to_email or not subject or not html_content:
            raise ValueError("to_email, subject, and html_content are required")

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.config.SENDER_EMAIL
            message["To"] = to_email

            # Add plain text part
            if plain_text:
                message.attach(MIMEText(plain_text, "plain"))

            # Add HTML part
            message.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(
                self.config.SMTP_SERVER,
                self.config.SMTP_PORT,
                timeout=10,
            ) as server:
                server.starttls()
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                server.sendmail(
                    self.config.SENDER_EMAIL,
                    to_email,
                    message.as_string(),
                )

            return True
        except smtplib.SMTPException as e:
            raise EmailSendError(f"Failed to send email: {str(e)}") from e
        except Exception as e:
            raise EmailSendError(f"Unexpected error while sending email: {str(e)}") from e

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: User name for personalization (optional)

        Returns:
            True if email sent successfully

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Password Reset Request"

        # Create reset URL
        reset_url = f"{self.config.PASSWORD_RESET_REDIRECT_URL}?token={reset_token}"
        if not self.config.PASSWORD_RESET_REDIRECT_URL:
            reset_url = reset_token

        # Create HTML content
        user_greeting = f"Hello {user_name}," if user_name else "Hello,"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Password Reset Request</h2>
                    <p>{user_greeting}</p>
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    <div style="margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #666;">{reset_url}</p>
                    <p>This link will expire in {self.config.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES} minutes.</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">If you did not request a password reset, ignore this email.</p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
        Password Reset Request
        
        {user_greeting}
        
        We received a request to reset your password. Visit this link to reset it:
        {reset_url}
        
        This link will expire in {self.config.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES} minutes.
        
        If you did not request a password reset, ignore this email.
        """

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_text=plain_text,
        )

    def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """
        Send welcome email to new user.

        Args:
            to_email: Recipient email address
            user_name: User name for personalization (optional)

        Returns:
            True if email sent successfully

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Welcome to AuthLib"

        user_greeting = f"Hello {user_name}," if user_name else "Hello,"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Welcome to AuthLib</h2>
                    <p>{user_greeting}</p>
                    <p>Thank you for signing up! Your account has been created successfully.</p>
                    <p>You can now log in with your email and password.</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">Questions? Contact support at support@authlib.dev</p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
        Welcome to AuthLib
        
        {user_greeting}
        
        Thank you for signing up! Your account has been created successfully.
        
        You can now log in with your email and password.
        
        Questions? Contact support at support@authlib.dev
        """

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_text=plain_text,
        )

    def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """
        Send email verification email.

        Args:
            to_email: Recipient email address
            verification_token: Email verification token
            user_name: User name for personalization (optional)

        Returns:
            True if email sent successfully

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Verify Your Email"

        user_greeting = f"Hello {user_name}," if user_name else "Hello,"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Verify Your Email</h2>
                    <p>{user_greeting}</p>
                    <p>Please verify your email address by clicking the button below:</p>
                    <div style="margin: 30px 0;">
                        <a href="{verification_token}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verify Email
                        </a>
                    </div>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #666;">{verification_token}</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">If you did not create this account, ignore this email.</p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
        Verify Your Email
        
        {user_greeting}
        
        Please verify your email address by visiting this link:
        {verification_token}
        
        If you did not create this account, ignore this email.
        """

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_text=plain_text,
        )
