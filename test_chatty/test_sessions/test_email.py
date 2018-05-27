import imaplib
import smtplib
import unittest
from typing import Tuple

from chatty.sessions.email import EmailSession, SMTPFactory, IMAPFactory
from chatty.sessions.interface import Session
from chatty.types import Handle

from test_chatty.support import get_protocol_test_config, BaseClasses


# NOTES:
# * To setup your own local test server for email, a good option is to use postfix together with courier and dovecot.
#   Some useful guides can be found [here](https://notblog.org/install-mail-server/) and
#   [here](https://gist.github.com/raelgc/6031274).


class EmailSessionTestCase(BaseClasses.SessionTestCase):

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


if __name__ == '__main__':
    unittest.main()
