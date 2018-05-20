import imaplib
import smtplib
from typing import Tuple

from chatty.email_session import EmailSession, SMTPFactory, IMAPFactory
from chatty.session_interface import Session
from chatty.types import Handle

from test_chatty.support import get_protocol_test_config, SessionTestCase


class EmailSessionTestCase(SessionTestCase):

    def setUp(self):
        self.smtp_config = get_protocol_test_config('SMTP', smtplib.SMTP_PORT)
        self.imap_config = get_protocol_test_config('IMAP (SSL)', imaplib.IMAP4_SSL_PORT)
        super().setUp()

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        session = EmailSession(
            SMTPFactory(self.smtp_config, connection_type=smtplib.SMTP),
            IMAPFactory(self.imap_config, connection_type=imaplib.IMAP4_SSL),
            rate=.001
        )

        return self.smtp_config.handle, session, self.imap_config.handle, session
