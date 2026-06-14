"""
server/services/hdm_service.py — HDM Bridge email integration
"""
import logging
import requests
from typing import Optional
from server.config.settings import settings

logger = logging.getLogger(__name__)


class HDMService:
    """Service for sending emails via HDM Bridge API."""

    def __init__(self):
        self.api_url = settings.HDM_API_URL.rstrip("/")
        self.api_key = settings.HDM_API_KEY
        self.from_email = settings.HDM_FROM_EMAIL
        self.from_name = settings.HDM_FROM_NAME

    @property
    def is_configured(self) -> bool:
        """Check if HDM Bridge is properly configured."""
        return bool(self.api_key and self.api_url)

    def send_email(
        self,
        to: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> dict:
        """
        Send an email via HDM Bridge.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML content (optional)
            text_body: Plain text content (optional)
            from_email: Override sender email
            from_name: Override sender name
            
        Returns:
            API response as dict
            
        Raises:
            ValueError: If HDM Bridge is not configured
            requests.RequestException: On API failure
        """
        if not self.is_configured:
            raise ValueError("HDM Bridge is not configured. Set HDM_API_KEY and HDM_API_URL in .env")

        payload = {
            "from": from_email or self.from_email,
            "fromName": from_name or self.from_name,
            "to": to,
            "subject": subject,
        }

        if html_body:
            payload["htmlBody"] = html_body
        if text_body:
            payload["textBody"] = text_body

        try:
            response = requests.post(
                f"{self.api_url}/emails/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Email sent to {to} - Subject: {subject}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise

    def send_welcome_email(self, to: str, username: str) -> dict:
        """Send a welcome email template."""
        return self.send_email(
            to=to,
            subject=f"Welcome to {self.from_name}!",
            html_body=f"""
            <h1>Welcome, {username}!</h1>
            <p>Thank you for joining {self.from_name}.</p>
            <p>We're excited to have you on board!</p>
            """,
            text_body=f"Welcome, {username}! Thank you for joining {self.from_name}. We're excited to have you on board!",
        )

    def send_notification(self, to: str, title: str, message: str) -> dict:
        """Send a notification email."""
        return self.send_email(
            to=to,
            subject=title,
            html_body=f"<h2>{title}</h2><p>{message}</p>",
            text_body=f"{title}\n\n{message}",
        )


# Singleton instance
hdm_service = HDMService()