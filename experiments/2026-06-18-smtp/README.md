You’re thinking about this the right way. For a FastAPI notification microservice, **do not start by building a real public SMTP server**. Start by learning the flow locally, then use a trusted SMTP/email provider for real delivery.

## The mental model

SMTP is just the protocol for moving email between systems.

Your app is usually an **SMTP client**, not the SMTP server. It connects to some SMTP server and says:

> “Please send this message from `noreply@mydomain.com` to `user@gmail.com`.”

The SMTP server can be:

1. **A fake local SMTP server** for development, such as Mailpit.
2. **Your personal email provider’s SMTP server**, such as Gmail SMTP.
3. **A transactional email provider**, such as Amazon SES, Postmark, Resend, Mailgun, SendGrid, etc.
4. **Your own real mail server**, such as Postfix, which is possible but usually painful for beginners.

For your first step, use **Mailpit**. It acts like an SMTP server, catches emails locally, and gives you a web UI to inspect them. It does **not** deliver to Gmail; it helps you test safely. Mailpit describes itself as an SMTP testing tool with a web UI and API for developers. ([mailpit.axllent.org][1])

---

## Step 1: Run a local SMTP catcher

With Docker:

```bash
docker run -d \
  --name mailpit \
  -p 1025:1025 \
  -p 8025:8025 \
  axllent/mailpit
```

Then open:

```text
http://localhost:8025
```

Your app will send SMTP mail to:

```text
host: localhost
port: 1025
username: none
password: none
TLS: false
```

---

## Step 2: Send a test email from Python

Create `send_email.py`:

```python
import smtplib
from email.message import EmailMessage


def send_email() -> None:
    message = EmailMessage()
    message["From"] = "noreply@example.local"
    message["To"] = "you@example.com"
    message["Subject"] = "Hello from local SMTP"
    message.set_content("This is my first test email from Python.")

    with smtplib.SMTP("localhost", 1025) as smtp:
        smtp.send_message(message)


if __name__ == "__main__":
    send_email()
```

Run:

```bash
python send_email.py
```

Then check Mailpit at:

```text
http://localhost:8025
```

Python’s built-in `smtplib` is the standard SMTP client library; it creates an SMTP client session that can send mail to an SMTP/ESMTP server. ([Python documentation][2])

---

## Step 3: Use it from FastAPI

Example project shape:

```text
app/
  main.py
  email_sender.py
```

`app/email_sender.py`:

```python
import smtplib
from email.message import EmailMessage


SMTP_HOST = "localhost"
SMTP_PORT = 1025
EMAIL_FROM = "noreply@example.local"


def send_email(to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.send_message(message)
```

`app/main.py`:

```python
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, EmailStr

from app.email_sender import send_email


app = FastAPI()


class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str


@app.post("/notifications/email")
def create_email_notification(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(
        send_email,
        request.to_email,
        request.subject,
        request.body,
    )

    return {
        "status": "queued",
        "channel": "email",
        "to_email": request.to_email,
    }
```

Run:

```bash
uvicorn main:app --reload --port=8010
```

Test:

```bash
curl -X POST http://localhost:8000/notifications/email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "me@example.com",
    "subject": "FastAPI email test",
    "body": "Hello from my notification microservice."
  }'
```

FastAPI’s `BackgroundTasks` are appropriate for small background work like email notifications, especially when the user should not wait for the SMTP call to finish. For heavier or more reliable processing, FastAPI’s docs suggest tools like Celery with Redis/RabbitMQ. ([FastAPI][3])

---

## Can you send email to yourself for real?

Yes, but probably **not** from your own simple local SMTP server.

For real delivery to Gmail, Outlook, Yahoo, etc., you usually need one of these:

### Option A: Use an email provider’s SMTP server

For example:

```text
smtp.gmail.com
smtp.mailgun.org
email-smtp.eu-central-1.amazonaws.com
smtp.postmarkapp.com
smtp.resend.com
```

Your app authenticates with username/password/API credentials. The provider handles much of the infrastructure.

### Option B: Use an email provider’s HTTP API

Many modern transactional email services offer APIs. For a microservice, this is often cleaner than raw SMTP because you get structured errors, templates, analytics, webhooks, retries, and easier credential handling.

### Option C: Run your own mail server

This is technically possible, but I would avoid it at the start. Deliverability is hard. Many cloud providers block or restrict outbound port 25, and receiving mail servers care about DNS, IP reputation, reverse DNS, authentication, spam complaints, TLS, bounce handling, and more.

---

## Why some emails go to spam

Inbox providers do not simply ask “did the SMTP command succeed?” They judge whether your mail looks trustworthy.

Important factors:

| Factor               | What it means                                                                 |
| -------------------- | ----------------------------------------------------------------------------- |
| SPF                  | DNS record saying which servers may send mail for your domain.                |
| DKIM                 | Cryptographic signature proving the message was authorized by your domain.    |
| DMARC                | Policy connecting SPF/DKIM to your visible `From:` domain.                    |
| Reverse DNS / PTR    | Your sending IP should map back to a valid hostname.                          |
| IP reputation        | Shared or dedicated IP history matters.                                       |
| Domain reputation    | Your domain’s sending behavior matters.                                       |
| Complaint rate       | Users clicking “Report spam” hurts you.                                       |
| Content              | Scammy wording, broken HTML, bad links, attachments, URL shorteners can hurt. |
| Recipient engagement | Opens, replies, deletions, spam reports, etc.                                 |
| Unsubscribe support  | Required for marketing/subscription emails.                                   |

Google’s sender guidelines require all senders to use SPF or DKIM, and bulk senders to use SPF, DKIM, and DMARC. Google also mentions TLS, valid forward/reverse DNS, spam rates below 0.3%, RFC 5322 formatting, and one-click unsubscribe for marketing/subscribed messages. ([Google Help][4]) Yahoo has similar sender requirements: SPF or DKIM for all senders, SPF and DKIM plus DMARC for bulk senders, low spam complaint rates, valid forward/reverse DNS, and one-click unsubscribe for marketing/subscribed messages. ([Sender Hub][5])

---

## Do you need to pay money?

For learning: **no**.

For local development:

```text
FastAPI -> Mailpit -> Web UI
```

Free.

For sending a few personal test emails:

```text
FastAPI -> Gmail/your mailbox SMTP -> your inbox
```

Usually free, but not ideal for production.

For a real product:

```text
FastAPI -> transactional email provider -> users
```

You should expect to pay eventually, even if there is a free tier. This is usually worth it because the provider helps with deliverability, logs, bounces, domain authentication, retries, and reputation.

---

## Recommended path for your microservice

Start with this progression:

```text
Phase 1: Local only
FastAPI -> Mailpit

Phase 2: Real test delivery
FastAPI -> provider sandbox/test domain -> your real email

Phase 3: Production
FastAPI -> queue/outbox table -> worker -> email provider -> user
```

For production, I would design the notification service like this:

```text
POST /notifications/email
        |
        v
Create notification record in DB
        |
        v
Background worker picks it up
        |
        v
Send via provider
        |
        v
Store status: sent / failed / bounced / retrying
```

Avoid making your user-facing request depend directly on SMTP success. SMTP can be slow, temporarily unavailable, or return ambiguous errors.

---

## Good first implementation target

Your first working milestone should be:

1. Run Mailpit.
2. Send an email from plain Python with `smtplib`.
3. Send an email from FastAPI using `BackgroundTasks`.
4. Move SMTP config into environment variables.
5. Later replace Mailpit config with a real provider config.

Example env-style config:

```env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=false
EMAIL_FROM=noreply@example.local
```

Once this works locally, the next major concept to learn is **domain authentication**: SPF, DKIM, and DMARC. That is the point where email changes from “my code sent a message” to “Gmail/Yahoo/Outlook trust my app enough to inbox it.”

[1]: https://mailpit.axllent.org/?utm_source=chatgpt.com "Mailpit - email & SMTP testing tool"
[2]: https://docs.python.org/3/library/smtplib.html "smtplib — SMTP protocol client — Python 3.14.6 documentation"
[3]: https://fastapi.tiangolo.com/tutorial/background-tasks/ "Background Tasks - FastAPI"
[4]: https://support.google.com/a/answer/81126?hl=en "Email sender guidelines - Gmail Help"
[5]: https://senders.yahooinc.com/best-practices/ "Sender Best Practices | Sender Hub"
