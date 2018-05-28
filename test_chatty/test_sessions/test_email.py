import datetime
import imaplib
import smtplib
import time
import unittest
from typing import Tuple

from chatty.sessions.email import EmailSession, SMTPFactory, IMAPFactory
from chatty.sessions.interface import Session
from chatty.signals.delivery_failure import DeliveryFailure
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.types import Handle, SignalID
from test_chatty.support import get_test_login_config, BaseClasses


# NOTES:
# * To setup your own local test server for email, a good option is to use postfix together with courier and dovecot.
#   Some useful guides can be found [here](https://notblog.org/install-mail-server/) and
#   [here](https://gist.github.com/raelgc/6031274).


class EmailSessionTestCase(BaseClasses.SessionTestCase):

    def setUp(self):
        self.smtp_config = get_test_login_config('SMTP', port=smtplib.SMTP_PORT)
        self.imap_config = get_test_login_config('IMAP (SSL)', port=imaplib.IMAP4_SSL_PORT)
        super().setUp()

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        session = EmailSession(
            SMTPFactory(self.smtp_config, connection_type=smtplib.SMTP),
            IMAPFactory(self.imap_config, connection_type=imaplib.IMAP4_SSL),
            rate=.001
        )

        return self.smtp_config.handle_configs[0].handle, session, self.imap_config.handle_configs[0].handle, session

    def test_delivery_failure(self):
        sent_at = datetime.datetime.now()
        meta_data = SignalMetaData(
            identifier=SignalID('bad-message-%s' % sent_at.timestamp()),
            origin=Handle('mailer-daemon@' + self.smtp_config.host),
            addressees=[self.imap_config.handle_configs[0].handle],
            sent_at=sent_at
        )
        content = "Delivery failure"
        message = Message(meta_data, content)
        self.sender_session.send(message)

        for _ in range(self.max_receiver_delay * 1000):
            time.sleep(.001)
            if self.received:
                failure = self.received.popleft()
                break
        else:
            failure = self.received.popleft()
        assert isinstance(failure, DeliveryFailure)
        assert failure.meta_data.identifier == meta_data.identifier


if __name__ == '__main__':
    unittest.main()
