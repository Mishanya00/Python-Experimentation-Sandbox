import smtplib
from email.message import EmailMessage


SMTP_HOST = "localhost"
SMTP_PORT = 1025
EMAIL_FROM = "noreply@example.local"


def send_email(
    to_email: str, 
    subject: str, 
    text_body: str,
    html_body: str | None = None,
) -> None:
    message = EmailMessage()

    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.send_message(message)