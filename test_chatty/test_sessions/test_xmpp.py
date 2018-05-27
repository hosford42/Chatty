from typing import Tuple
import unittest

from chatty.sessions.interface import Session
from chatty.types import Handle
from chatty.sessions.xmpp import XMPPSession

from test_chatty.support import BaseClasses
from test_chatty.support import get_protocol_test_config


# NOTES:
# * Prosody.IM is an easy way to setup your own local XMPP test server.
# * If you are connected to the receiver test account with another client, such as Pidgin, the messages may be
#   intercepted, causing the tests to fail.


class TestXMPPSession(BaseClasses.SessionTestCase):

    def setUp(self):
        self.config1 = get_protocol_test_config('XMPP #1', 5222)
        self.config2 = get_protocol_test_config('XMPP #2', 5222)
        super().setUp()

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        return self.config1.handle, XMPPSession(self.config1), self.config2.handle, XMPPSession(self.config2)


if __name__ == '__main__':
    unittest.main()
