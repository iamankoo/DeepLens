import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logger import logger


class EmailSender:

    def send(self, *, to: str, subject: str, body: str) -> None:
        if not settings.SMTP_HOST:
            logger.info(
                "SMTP not configured — logging email instead of sending",
                extra={"to": to, "subject": subject, "body": body},
            )
            return

        message = EmailMessage()
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)

        logger.info("email sent", extra={"to": to, "subject": subject})


email_sender = EmailSender()
