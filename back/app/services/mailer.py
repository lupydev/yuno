import os
import smtplib
import logging
import time
from email.message import EmailMessage
from typing import List, Optional

logger = logging.getLogger(__name__)

# Configuration via environment variables:
# MAIL_HOST (default: smtp.gmail.com)
# MAIL_PORT (default: 587)
# MAIL_USER (your Gmail address)
# MAIL_PASSWORD (Gmail App Password)
# MAIL_USE_TLS (default: True)

MAIL_HOST = os.getenv("MAIL_HOST", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("1", "true", "yes")



class MailerConfigError(Exception):
    pass


def _ensure_config():
    if not MAIL_USER or not MAIL_PASSWORD:
        raise MailerConfigError(
            "MAIL_USER and MAIL_PASSWORD must be set in environment to send emails."
        )


def _connect_smtp():
    if MAIL_USE_TLS:
        server = smtplib.SMTP(MAIL_HOST, MAIL_PORT, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
    else:
        server = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT, timeout=30)
    server.login(MAIL_USER, MAIL_PASSWORD)
    return server


def send_email(
    subject: str,
    body: str,
    recipients: List[str],
    sender: Optional[str] = None,
    html: Optional[str] = None,
    attempt_max: int = 3,
) -> None:
    """
    Send a simple email via Gmail SMTP. Uses environment variables for configuration.

    subject: email subject
    body: plain-text body
    recipients: list of recipient email addresses
    sender: optional from address (defaults to MAIL_USER)
    html: optional HTML body
    attempt_max: retry attempts on transient failure
    """
    _ensure_config()

    if not recipients:
        raise ValueError("recipients must be a non-empty list")

    sender = sender or MAIL_USER

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    last_exc = None
    for attempt in range(1, attempt_max + 1):
        try:
            server = _connect_smtp()
            server.send_message(msg)
            server.quit()
            logger.info("Email sent to %s (subject=%s)", recipients, subject)
            return
        except smtplib.SMTPException as e:
            last_exc = e
            wait = 2 ** attempt
            logger.warning(
                "SMTP send failed (attempt %s/%s): %s — retrying in %s seconds",
                attempt,
                attempt_max,
                e,
                wait,
            )
            time.sleep(wait)
        except Exception as e:
            # Non-SMTP exceptions are likely fatal; log and re-raise
            logger.exception("Unexpected error while sending email: %s", e)
            raise

    # If we exhausted retries, raise the last SMTP exception
    logger.error("Failed to send email to %s after %s attempts", recipients, attempt_max)
    raise last_exc
