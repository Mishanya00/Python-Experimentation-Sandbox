The **Transactional Outbox Pattern** solves one specific but very important problem:

> How do I safely change my database and publish an event/message without losing consistency between them?

This matters because your database and RabbitMQ are **two different systems**. A normal DB transaction cannot automatically include RabbitMQ.

---

# 1. The standard approach

Imagine user registration.

Your main service does this:

```text
1. Save user to DB
2. Publish "SendWelcomeEmail" message to RabbitMQ
3. Return success to user
```

Code may look like this:

```python
async def register_user(data: RegisterUserDTO) -> User:
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )

    await user_repository.create(user)

    await rabbitmq_publisher.publish(
        queue="email_notifications",
        message={
            "type": "welcome_email",
            "user_id": str(user.id),
            "email": user.email,
        },
    )

    return user
```

Looks fine.

But there are dangerous failure cases.

---

## Problem A: DB succeeds, RabbitMQ publish fails

```text
1. Save user to DB               ✅
2. Publish message to RabbitMQ   ❌
3. Return success?               maybe
```

Now the user exists, but the welcome email was never queued.

Result:

```text
User registered, but no welcome email.
```

This is bad, but common.

---

## Problem B: RabbitMQ succeeds, DB transaction fails

This can happen if you publish before the transaction is committed.

```text
1. Start DB transaction
2. Insert user                   pending
3. Publish message to RabbitMQ   ✅
4. DB commit fails               ❌
```

Now your notification service receives:

```json
{
  "type": "welcome_email",
  "user_id": "123"
}
```

But user `123` may not exist in the database.

Result:

```text
Email task exists for a user that was never actually created.
```

---

## Problem C: Service crashes between DB and RabbitMQ

```text
1. Save user to DB               ✅
2. App crashes                   ❌
3. Publish message to RabbitMQ   never happened
```

Again:

```text
User registered, but no email event.
```

---

# 2. The transactional outbox approach

Instead of writing to the DB and RabbitMQ in one function, you write **both the business data and the event into the same database transaction**.

You create an `outbox_messages` table.

When user registers:

```text
1. Start DB transaction
2. Save user
3. Save outbox message in same DB
4. Commit transaction
```

Then a separate process publishes outbox messages to RabbitMQ:

```text
5. Poll unsent outbox messages
6. Publish to RabbitMQ
7. Mark outbox message as published
```

The key is this:

> The user and the event are saved atomically in the same database.

So either both exist:

```text
User created ✅
Outbox message created ✅
```

or neither exists:

```text
User created ❌
Outbox message created ❌
```

---

# 3. Standard approach vs outbox approach

## Standard approach

```text
HTTP request
   |
   v
Main service
   |
   +--> Save user to DB
   |
   +--> Publish email event to RabbitMQ
   |
   v
Return response
```

Risk:

```text
DB save succeeds, RabbitMQ publish fails.
```

## Transactional outbox approach

```text
HTTP request
   |
   v
Main service
   |
   +--> Save user to DB
   |
   +--> Save outbox event to DB
   |
   v
Return response
```

Then separately:

```text
Outbox publisher
   |
   v
Reads unpublished DB events
   |
   v
Publishes to RabbitMQ
   |
   v
Marks event as published
```

The difference:

```text
Standard approach:
DB + RabbitMQ are updated directly in the request flow.

Outbox approach:
Only DB is updated in the request flow.
RabbitMQ publishing happens later from durable DB records.
```

---

# 4. Simple visual comparison

```text
Standard approach:

register_user()
    create user in DB
    publish event to RabbitMQ
    return success

Failure gap:
    between DB commit and RabbitMQ publish
```

```text
Transactional outbox:

register_user()
    create user in DB
    create outbox message in DB
    return success

outbox_worker()
    publish outbox message to RabbitMQ
    mark as published

Failure gap:
    much smaller and recoverable
```

The main benefit is **recoverability**.

If RabbitMQ is temporarily down, your outbox messages remain in the database and can be retried later.

---

# 5. Example database tables

Suppose you have a `users` table:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Add an `outbox_messages` table:

```sql
CREATE TABLE outbox_messages (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,

    status TEXT NOT NULL DEFAULT 'pending',
    attempts INT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ NULL,
    last_error TEXT NULL
);
```

Example row:

```json
{
  "id": "d7a0f1e9-8fd9-4f7b-aeb7-09cc8dbd85f4",
  "event_type": "email.welcome_requested",
  "payload": {
    "user_id": "4a3dbfa4-b4c1-4e70-9dc6-3faeaec6cd2d",
    "email": "michael@example.com"
  },
  "status": "pending",
  "attempts": 0
}
```

---

# 6. Registration with standard approach

Without outbox:

```python
class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        rabbitmq_publisher: RabbitMQPublisher,
    ):
        self._user_repository = user_repository
        self._rabbitmq_publisher = rabbitmq_publisher

    async def register_user(self, email: str, password: str) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
        )

        await self._user_repository.create(user)

        await self._rabbitmq_publisher.publish(
            routing_key="email.welcome_requested",
            message={
                "user_id": str(user.id),
                "email": user.email,
            },
        )

        return user
```

Problem:

```text
If user_repository.create() succeeds but publish() fails,
the user exists but the email event is lost.
```

---

# 7. Registration with transactional outbox

With outbox:

```python
class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        outbox_repository: OutboxRepository,
        transaction_manager: TransactionManager,
    ):
        self._user_repository = user_repository
        self._outbox_repository = outbox_repository
        self._transaction_manager = transaction_manager

    async def register_user(self, email: str, password: str) -> User:
        async with self._transaction_manager:
            user = User(
                email=email,
                password_hash=hash_password(password),
            )

            await self._user_repository.create(user)

            await self._outbox_repository.create(
                event_type="email.welcome_requested",
                payload={
                    "user_id": str(user.id),
                    "email": user.email,
                },
            )

        return user
```

Now the DB transaction contains both:

```text
INSERT INTO users ...
INSERT INTO outbox_messages ...
```

So if the transaction succeeds:

```text
User exists.
Outbox event exists.
```

If the transaction fails:

```text
User does not exist.
Outbox event does not exist.
```

That is the main point.

---

# 8. Outbox publisher

Now you need a separate worker.

This worker reads pending outbox messages and publishes them to RabbitMQ.

Simplified version:

```python
class OutboxPublisher:
    def __init__(
        self,
        outbox_repository: OutboxRepository,
        rabbitmq_publisher: RabbitMQPublisher,
    ):
        self._outbox_repository = outbox_repository
        self._rabbitmq_publisher = rabbitmq_publisher

    async def publish_pending_messages(self) -> None:
        messages = await self._outbox_repository.get_pending(limit=100)

        for message in messages:
            try:
                await self._rabbitmq_publisher.publish(
                    routing_key=message.event_type,
                    message=message.payload,
                )
            except Exception as exc:
                await self._outbox_repository.mark_failed_attempt(
                    message_id=message.id,
                    error=str(exc),
                )
                continue

            await self._outbox_repository.mark_published(message.id)
```

This can run:

```text
Every 1 second
Every 5 seconds
Continuously in a loop
As a separate process/container
```

For example:

```python
import asyncio


async def main() -> None:
    publisher = build_outbox_publisher()

    while True:
        await publisher.publish_pending_messages()
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
```

---

# 9. Important issue: duplicate messages

The outbox pattern gives you reliable publishing, but it can still publish duplicates.

Example:

```text
1. Outbox worker publishes message to RabbitMQ ✅
2. Worker crashes before marking outbox row as published ❌
3. Worker restarts
4. Same outbox row is still "pending"
5. Worker publishes it again
```

So consumers must be **idempotent**.

Meaning:

> Processing the same message twice should not produce incorrect behavior.

For email this matters a lot, because you do not want to send the same welcome email 5 times.

---

# 10. Applying this to emails

You probably want three concepts:

```text
outbox_messages
notification_messages
email_send_attempts
```

For a simpler version, start with:

```text
outbox_messages
notifications
```

---

## In the main service

When something happens, such as registration:

```text
1. Create user
2. Create outbox event: email.welcome_requested
3. Commit transaction
4. Return "registered"
```

Example event:

```json
{
  "notification_id": "9271c267-5691-41b6-9762-fbcb89db734a",
  "type": "welcome_email",
  "recipient": "michael@example.com",
  "template": "welcome",
  "template_data": {
    "username": "Michael"
  }
}
```

Your main service outbox table row:

```text
event_type: email.welcome_requested
payload:
  notification_id
  recipient
  template
  template_data
```

---

## Outbox publisher

The outbox publisher sends this to RabbitMQ:

```text
exchange: notifications
routing_key: email.welcome_requested
queue: email_notifications
```

RabbitMQ message:

```json
{
  "notification_id": "9271c267-5691-41b6-9762-fbcb89db734a",
  "type": "welcome_email",
  "recipient": "michael@example.com",
  "template": "welcome",
  "template_data": {
    "username": "Michael"
  }
}
```

---

## Notification service

The notification service consumes the message:

```text
1. Receive email.welcome_requested
2. Check if notification_id was already processed
3. Render template
4. Send email
5. Save status
6. ACK RabbitMQ message
```

Example:

```python
from pydantic import BaseModel, EmailStr


class EmailRequestedEvent(BaseModel):
    notification_id: str
    type: str
    recipient: EmailStr
    template: str
    template_data: dict
```

Consumer:

```python
@broker.subscriber("email_notifications")
async def handle_email_requested(event: EmailRequestedEvent) -> None:
    already_sent = await notification_repository.is_sent(
        notification_id=event.notification_id,
    )

    if already_sent:
        return

    html_body, text_body = await template_renderer.render(
        template_name=event.template,
        data=event.template_data,
    )

    await email_sender.send(
        to_email=event.recipient,
        subject="Welcome!",
        html_body=html_body,
        text_body=text_body,
    )

    await notification_repository.mark_sent(
        notification_id=event.notification_id,
    )
```

This is the basic idea, but there is a subtle bug.

---

# 11. Safer email consumer

The previous code checks:

```text
Was this notification already sent?
```

Then sends email.

Then marks it sent.

But a crash can still happen here:

```text
1. Check notification status       not sent
2. Send email                      ✅
3. App crashes                     ❌
4. mark_sent never happens
5. Message is retried
6. Email is sent again             ❌
```

You cannot fully solve this with SMTP alone.

With a professional email provider, you can often use:

```text
idempotency key
custom message ID
metadata
deduplication key
```

But the basic version is still useful.

A safer flow is:

```text
1. Create notification record with unique notification_id
2. Mark as processing
3. Send email
4. Mark as sent
```

And put a unique constraint on `notification_id`.

---

# 12. Email notification table

In the notification service DB:

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    channel TEXT NOT NULL,
    recipient TEXT NOT NULL,
    template TEXT NOT NULL,
    status TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processing_started_at TIMESTAMPTZ NULL,
    sent_at TIMESTAMPTZ NULL,
    failed_at TIMESTAMPTZ NULL,

    error TEXT NULL
);
```

Statuses:

```text
pending
processing
sent
failed
```

Consumer logic:

```python
@broker.subscriber("email_notifications")
async def handle_email_requested(event: EmailRequestedEvent) -> None:
    notification = await notification_repository.get_or_create(
        notification_id=event.notification_id,
        channel="email",
        recipient=event.recipient,
        template=event.template,
    )

    if notification.status == "sent":
        return

    await notification_repository.mark_processing(event.notification_id)

    html_body, text_body = await template_renderer.render(
        template_name=event.template,
        data=event.template_data,
    )

    try:
        await email_sender.send(
            to_email=event.recipient,
            subject=get_subject(event.template),
            html_body=html_body,
            text_body=text_body,
        )
    except Exception as exc:
        await notification_repository.mark_failed(
            notification_id=event.notification_id,
            error=str(exc),
        )
        raise

    await notification_repository.mark_sent(event.notification_id)
```

If you raise after failure, RabbitMQ can retry or dead-letter depending on your configuration.

---

# 13. Full email flow with transactional outbox

Here is the clean production-ish version:

```text
User registers
   |
   v
Main service DB transaction
   |
   +-- INSERT users
   |
   +-- INSERT outbox_messages
   |
   v
Commit
   |
   v
Return "registered"
```

Then:

```text
Outbox publisher
   |
   v
SELECT pending outbox messages
   |
   v
Publish to RabbitMQ
   |
   v
Mark outbox message as published
```

Then:

```text
Notification service
   |
   v
Consume RabbitMQ message
   |
   v
Create/get notification record
   |
   v
Render email
   |
   v
Send email
   |
   v
Mark notification as sent
   |
   v
ACK RabbitMQ message
```

---

# 14. Why not just publish directly?

For a small pet project, direct publishing is acceptable.

For example:

```text
create user
publish RabbitMQ message
return success
```

This is fine when:

```text
Losing one email is acceptable.
You do not need strong reliability.
The system is simple.
You are still prototyping.
```

But use outbox when:

```text
The event must not be lost.
Business flow depends on it.
You need auditability.
You need retries.
You need clear failure recovery.
You have multiple microservices reacting to domain events.
```

Examples where outbox is worth it:

```text
payment.created
order.paid
user.registered
subscription.cancelled
invoice.created
email.verification_requested
password_reset_requested
```

For your email notification service, I would especially use it for:

```text
email verification
password reset
payment receipt
security alert
```

Maybe not needed for:

```text
weekly newsletter
low-priority marketing email
minor engagement notification
```

---

# 15. Concrete email example

User registration endpoint:

```python
@router.post("/register")
async def register_user(
    data: RegisterUserDTO,
    user_service: UserService = Depends(),
):
    user = await user_service.register_user(data)

    return {
        "id": user.id,
        "email": user.email,
        "status": "registered",
        "email_status": "queued",
    }
```

Service:

```python
class UserService:
    async def register_user(self, data: RegisterUserDTO) -> User:
        async with self._transaction_manager:
            user = User(
                email=data.email,
                password_hash=hash_password(data.password),
            )

            await self._user_repository.create(user)

            await self._outbox_repository.create(
                event_type="email.welcome_requested",
                payload={
                    "notification_id": str(uuid.uuid4()),
                    "recipient": user.email,
                    "template": "welcome",
                    "template_data": {
                        "email": user.email,
                    },
                },
            )

        return user
```

Outbox publisher:

```python
class OutboxPublisher:
    async def run_once(self) -> None:
        messages = await self._outbox_repository.get_pending(limit=100)

        for message in messages:
            try:
                await self._broker.publish(
                    message=message.payload,
                    routing_key=message.event_type,
                )
            except Exception as exc:
                await self._outbox_repository.increment_attempts(
                    message_id=message.id,
                    error=str(exc),
                )
                continue

            await self._outbox_repository.mark_published(message.id)
```

Notification consumer:

```python
@broker.subscriber("email_notifications")
async def handle_welcome_email(event: EmailRequestedEvent) -> None:
    notification = await notification_repository.get_or_create(
        notification_id=event.notification_id,
        channel="email",
        recipient=event.recipient,
        template=event.template,
    )

    if notification.status == "sent":
        return

    html_body = f"""
    <h1>Welcome!</h1>
    <p>Nice to see you here, {event.template_data["email"]}.</p>
    """

    text_body = f"""
    Welcome!

    Nice to see you here, {event.template_data["email"]}.
    """

    await email_sender.send(
        to_email=event.recipient,
        subject="Welcome!",
        html_body=html_body,
        text_body=text_body,
    )

    await notification_repository.mark_sent(event.notification_id)
```

---

# 16. One warning about “exactly once”

Many people think outbox gives “exactly once delivery.”

It usually does not.

A more accurate statement is:

```text
Transactional outbox gives reliable at-least-once publishing.
```

That means:

```text
Messages should not be lost.
Messages may occasionally be duplicated.
```

Therefore consumers should be idempotent.

For emails, that means:

```text
Use notification_id.
Store send status.
Skip if already sent.
Avoid side effects before idempotency checks.
```

---

# 17. Practical recommendation for your project

Given your architecture:

```text
Main FastAPI service
RabbitMQ
Notification service with FastStream
SMTP/email provider
```

I would build in this order:

## Stage 1: Simple direct publish

```text
Main service -> RabbitMQ -> notification service -> Mailpit
```

Return:

```json
{
  "email_status": "queued"
}
```

This helps you learn RabbitMQ/FastStream/email basics.

## Stage 2: Add notification status

```text
Notification service stores sent/failed status
```

This helps you debug and retry.

## Stage 3: Add transactional outbox in main service

```text
Main service writes outbox rows
Outbox publisher sends to RabbitMQ
```

This improves reliability.

## Stage 4: Add idempotency

```text
notification_id unique
skip if already sent
deduplicate repeated RabbitMQ messages
```

This prevents duplicated sends as much as possible.

---

The short version of the pattern is:

```text
Do not publish to RabbitMQ directly inside your business transaction.

Instead:
1. Save the business change.
2. Save the event in an outbox table in the same DB transaction.
3. Publish the event from the outbox asynchronously.
```

For your email case, that means:

```text
Do not only say:
"User registered, now publish welcome email."

Say:
"User registered, and a durable welcome-email event was stored.
A publisher will reliably send that event to RabbitMQ."
```
