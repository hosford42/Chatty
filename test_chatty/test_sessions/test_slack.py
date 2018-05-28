import datetime
import time
import unittest
from typing import Tuple

from chatty.signals.delivery_failure import DeliveryFailure
from chatty.signals.message import Message
from slackclient import SlackClient

from chatty.sessions.interface import Session
from chatty.sessions.slack import SlackSession
from chatty.signals.interface import Signal
from chatty.signals.metadata import SignalMetaData
from chatty.types import Handle
from test_chatty.support import get_test_login_config, BaseClasses


import logging
logging.basicConfig()


# NOTES:
# * To setup your own local test server for email, a good option is to use postfix together with courier and dovecot.
#   Some useful guides can be found [here](https://notblog.org/install-mail-server/) and
#   [here](https://gist.github.com/raelgc/6031274).


class SlackSessionTestCase(BaseClasses.SessionTestCase):

    def setUp(self):
        self.slack_config1 = get_test_login_config('Slack #1')
        self.slack_config2 = get_test_login_config('Slack #2')
        super().setUp()

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        sender_client = SlackClient(token=self.slack_config1.password)
        sender_client.rtm_connect()
        sender_session = SlackSession(sender_client)
        receiver_client = SlackClient(token=self.slack_config2.password)
        receiver_client.rtm_connect()
        receiver_session = SlackSession(receiver_client)
        return (self.slack_config1.handle_configs[0].handle, sender_session,
                self.slack_config2.handle_configs[0].handle, receiver_session)

    def check_signal(self, original: Signal, received: Signal):
        self.assertEqual(type(original), type(received))
        self.assertEqual(original.content, received.content)
        self.assertEqual(original.meta_data.origin, received.meta_data.origin)

    def test_delivery_failure(self):
        sent_at = datetime.datetime.now()
        meta_data = SignalMetaData(
            origin=self.slack_config2.handle_configs[0].handle,
            addressees=[Handle('nonexistent_channel')],
            sent_at=sent_at
        )
        content = "Delivery failure"
        message = Message(meta_data, content)
        self.receiver_session.send(message)

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
