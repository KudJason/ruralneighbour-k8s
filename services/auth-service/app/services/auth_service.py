import secrets
from datetime import datetime, timedelta

from app.core.config import settings
from app.crud.crud_user import create_user, get_user_by_email, update_last_login
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# 尝试导入SendGrid，如果不可用则使用SMTP作为备选
try:
    import sendgrid
    from sendgrid.helpers.mail import Content, Email, Mail, To

    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

from ..core.security import get_password_hash, verify_password
from ..models.user import User
from ..schemas.user import UserCreate
from .events import EventPublisher


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        existing_user = get_user_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        try:
            user = create_user(db, user_in, get_password_hash(user_in.password))
            if user.full_name is not None:
                EventPublisher.publish_user_registered(
                    user_id=str(user.user_id),
                    email=str(user.email),
                    full_name=str(user.full_name),
                )
            else:
                EventPublisher.publish_user_registered(
                    user_id=str(user.user_id), email=str(user.email)
                )
            return user
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        user = get_user_by_email(db, email)
        if not user:
            return None
        password_hash = str(getattr(user, "password_hash", ""))
        if not verify_password(password, password_hash):
            return None
        update_last_login(db, user)
        return user

    @staticmethod
    def forgot_password(db: Session, email: str) -> dict:
        """Generate and send password reset token"""
        user = get_user_by_email(db, email)
        if not user:
            # Don't reveal if email exists or not for security
            return {
                "message": "If the email exists, a password reset link has been sent"
            }

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_token_expires = datetime.utcnow() + timedelta(
            hours=1
        )  # Token expires in 1 hour

        # Update user with reset token
        setattr(user, "reset_token", reset_token)
        setattr(user, "reset_token_expires", reset_token_expires)
        db.commit()

        # Send reset email
        AuthService._send_password_reset_email(email, reset_token)

        return {"message": "If the email exists, a password reset link has been sent"}

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> dict:
        """Reset password using token"""
        # Find user by reset token
        user = (
            db.query(User)
            .filter(
                User.reset_token == token, User.reset_token_expires > datetime.utcnow()
            )
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Update password
        setattr(user, "password_hash", get_password_hash(new_password))
        setattr(user, "reset_token", None)
        setattr(user, "reset_token_expires", None)
        db.commit()

        return {"message": "Password reset successfully"}

    @staticmethod
    def _send_password_reset_email(email: str, token: str) -> None:
        """Send password reset email using SendGrid or SMTP"""
        try:
            # 优先使用SendGrid
            if SENDGRID_AVAILABLE:
                AuthService._send_with_sendgrid(email, token)
            else:
                AuthService._send_with_smtp(email, token)
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            # Don't raise exception to avoid revealing email sending failures

    @staticmethod
    def _send_with_sendgrid(email: str, token: str) -> None:
        """Send email using SendGrid"""
        if not settings.sendgrid_api_key:
            print(
                f"SendGrid API key not configured. Password reset token for {email}: {token}"
            )
            return

        # Create reset URL
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"

        # Create email content
        subject = "Password Reset - Rural Neighbor"
        body = f"""
        Hello,
        
        You requested a password reset for your Rural Neighbor account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        Rural Neighbor Team
        """

        # Send email using SendGrid
        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        from_email = Email(settings.from_email)
        to_email = To(email)
        subject = subject
        content = Content("text/plain", body)
        mail = Mail(from_email, to_email, subject, content)

        response = sg.send(mail)
        print(f"SendGrid email sent successfully. Status: {response.status_code}")

    @staticmethod
    def _send_with_smtp(email: str, token: str) -> None:
        """Send email using SMTP (fallback)"""
        # Skip sending email if no SMTP credentials are configured
        if not settings.smtp_username or not settings.smtp_password:
            print(
                f"SMTP credentials not configured. Password reset token for {email}: {token}"
            )
            return

        # Create reset URL
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"

        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.from_email
        msg["To"] = email
        msg["Subject"] = "Password Reset - Rural Neighbor"

        body = f"""
        Hello,
        
        You requested a password reset for your Rural Neighbor account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        Rural Neighbor Team
        """

        msg.attach(MIMEText(body, "plain"))

        # Send email
        server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        text = msg.as_string()
        server.sendmail(settings.from_email, email, text)
        server.quit()
        print(f"SMTP email sent successfully to {email}")
