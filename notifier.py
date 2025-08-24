import os, smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
TO_EMAIL = os.getenv("TO_EMAIL", SMTP_USER)

def send_email(subject, body, to_email: str = None):
    if not to_email:
        to_email = TO_EMAIL
    if not (SMTP_USER and SMTP_PASS and FROM_EMAIL and to_email):
        raise RuntimeError("SMTP credentials or emails are not set. Check your .env")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
