from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from email_sender import send_email
from smtp_client import SMTPEmailSender


SMTP_HOST = "localhost"
SMTP_PORT = 1025
EMAIL_FROM = "noreply@example.local"

app = FastAPI()


class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    text_body: str
    html_body: str | None = Field(default=None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "user@example.com",
                "subject": "string",
                "text_body": "string",
                "html_body": '<h1> Greetings </h1>\n\n<p>Welcome to our private equity club!</p>',
            }
        }
    )


@app.post("/notifications/email")
def create_email_notification(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(
        send_email,
        request.to_email,
        request.subject,
        request.text_body,
        request.html_body,
    )

    return {
        "status": "queued",
        "channel": "email",
        "to_email": request.to_email,
    }


@app.post("/notifications/email_via_client")
def create_email_notification(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
):
    email_sender = SMTPEmailSender(
        host=SMTP_HOST,
        port=SMTP_PORT,
        default_from_email=EMAIL_FROM,
    )


    background_tasks.add_task(
        email_sender.send_email,
        request.to_email,
        request.subject,
        request.text_body,
        request.html_body,
    )

    return {
        "status": "queued",
        "channel": "email",
        "to_email": request.to_email,
    }