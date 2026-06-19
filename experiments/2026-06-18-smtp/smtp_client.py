import smtplib
import ssl
from email.message import EmailMessage


class SMTPEmailSender:
    def __init__(
        self,
        host: str,
        port: int,
        default_from_email: str,
        use_ssl: bool = False,
        use_tls: bool = False,
        username: str | None = None,
        password: str | None = None,
    ):
        if use_ssl and use_tls:
            raise ValueError("EMAIL_USE_SSL and EMAIL_USE_TLS cannot both be enabled")

        self._host = host
        self._port = port
        self._default_from_email = default_from_email
        self._use_ssl = use_ssl
        self._use_tls = use_tls
        self._username = username
        self._password = password

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
        from_email: str | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = from_email or self._default_from_email
        message["To"] = to_email
        message["Subject"] = subject

        message.set_content(text_body)

        if html_body is not None:
            message.add_alternative(html_body, subtype="html")

        self._send_message(message)

    def _send_message(self, message: EmailMessage) -> None:
        context = ssl.create_default_context()

        if self._use_ssl:
            with smtplib.SMTP_SSL(
                host=self._host,
                port=self._port,
                context=context,
            ) as smtp:
                self._login_if_needed(smtp)
                smtp.send_message(message)
            return None

        with smtplib.SMTP(
            host=self._host,
            port=self._port,
        ) as smtp:
            if self._use_tls:
                smtp.starttls(context=context)

            self._login_if_needed(smtp)
            smtp.send_message(message)

    def _login_if_needed(self, smtp: smtplib.SMTP) -> None:
        if self._username and self._password:
            smtp.login(self._username, self._password)