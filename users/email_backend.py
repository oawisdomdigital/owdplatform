from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend
from smtplib import SMTPException
import logging

from .models import EmailSettings

logger = logging.getLogger(__name__)

class FallbackEmailBackend(SmtpEmailBackend):
    def __init__(self, **kwargs):
        # Initialize with default settings
        self.default_settings = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'username': None,
            'password': None,
            'from_email': None
        }

        # Fallback settings (Mailjet)
        self.fallback_settings = {
            'host': 'in-v3.mailjet.com',
            'port': 587,
            'use_tls': True,
            'username': 'f378fb1358a57d5e6aba848d75f4a38c',  # Mailjet API Key
            'password': 'f4d57c01bae3cb7496d978ebe5d78782',  # Mailjet API Secret
            'from_email': 'oawisdomdigitalfirm@gmail.com'
        }
        
        # Fetch email settings from the database
        email_settings = EmailSettings.objects.first()
        if email_settings:
            self.default_settings.update({
                'host': email_settings.email_host,
                'port': email_settings.email_port,
                'use_tls': email_settings.email_use_tls,
                'username': email_settings.email_host_user,
                'password': email_settings.email_host_password,
                'from_email': email_settings.default_from_email
            })
        else:
            raise ValueError("No email settings found in the database")

        super().__init__(**self.default_settings)
    
    def send_messages(self, email_messages):
        try:
            # Attempt to send using the default settings (Gmail)
            return super().send_messages(email_messages)
        except SMTPException as e:
            logger.error(f"Failed to send email using primary account: {e}")
            # Switch to Mailjet settings and retry
            return self._send_with_fallback(email_messages)
    
    def _send_with_fallback(self, email_messages):
        # Use Mailjet settings and create a new connection
        fallback_backend = SmtpEmailBackend(
            host=self.fallback_settings['host'],
            port=self.fallback_settings['port'],
            use_tls=self.fallback_settings['use_tls'],
            username=self.fallback_settings['username'],
            password=self.fallback_settings['password'],
            from_email=self.fallback_settings['from_email']
        )
        try:
            return fallback_backend.send_messages(email_messages)
        except SMTPException as e:
            logger.error(f"Failed to send email using Mailjet: {e}")
            raise
