# ruff: noqa: F401
import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

from logger import logger

load_dotenv()

print()

subject = "Tutorial Notification"
body = "test_email"
sender = "mhafiz87.engineer@gmail.com"
recipients = [
    "mhafiz.muhamad@gmail.com",
]
password = os.getenv("GSPD")


def send_email(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    logger.info(f"Email sent to {', '.join(recipients)} with subject: {subject}")


if __name__ == "__main__":
    pass
