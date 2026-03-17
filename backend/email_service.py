import base64
import os
import smtplib
import ssl
from email.message import EmailMessage

import httpx


def _bool_env(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, str(default))).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _send_via_resend(to_email: str, subject: str, body: str, attachment_bytes: bytes, attachment_name: str):
    api_key = str(os.getenv("RESEND_API_KEY", "")).strip()
    from_email = str(os.getenv("RESEND_FROM_EMAIL", "")).strip()
    reply_to = str(os.getenv("RESEND_REPLY_TO", "")).strip()

    if not api_key:
        raise RuntimeError("Resend not configured: missing RESEND_API_KEY")
    if not from_email:
        raise RuntimeError("Resend not configured: missing RESEND_FROM_EMAIL")

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body or "Please find your quotation attached.",
        "attachments": [
            {
                "filename": attachment_name,
                "content": base64.b64encode(attachment_bytes).decode("ascii"),
            }
        ],
    }
    if reply_to:
        payload["reply_to"] = [reply_to]

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=45,
    )

    if not response.is_success:
        raise RuntimeError(f"Resend email send failed: {response.text}")


def _send_via_smtp(to_email: str, subject: str, body: str, attachment_bytes: bytes, attachment_name: str):
    smtp_host = str(os.getenv("SMTP_HOST", "")).strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = str(os.getenv("SMTP_USER", "")).strip()
    smtp_pass = str(os.getenv("SMTP_PASS", "")).strip()
    smtp_from = str(os.getenv("SMTP_FROM", smtp_user)).strip()
    smtp_ssl = _bool_env("SMTP_SSL", False)
    smtp_starttls = _bool_env("SMTP_STARTTLS", True)

    if not smtp_host:
        raise RuntimeError("SMTP not configured: missing SMTP_HOST")
    if not smtp_from:
        raise RuntimeError("SMTP not configured: missing SMTP_FROM/SMTP_USER")

    message = EmailMessage()
    message["From"] = smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body or "Please find your quotation attached.")
    message.add_attachment(
        attachment_bytes,
        maintype="application",
        subtype="pdf",
        filename=attachment_name,
    )

    if smtp_ssl:
        with smtplib.SMTP_SSL(
            smtp_host,
            smtp_port,
            context=ssl.create_default_context(),
            timeout=30,
        ) as server:
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            if smtp_starttls:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(message)


def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    attachment_bytes: bytes,
    attachment_name: str,
):
    if str(os.getenv("RESEND_API_KEY", "")).strip():
        _send_via_resend(to_email, subject, body, attachment_bytes, attachment_name)
        return

    _send_via_smtp(to_email, subject, body, attachment_bytes, attachment_name)
