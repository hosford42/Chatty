import unittest
from typing import Tuple

from chatty.sessions.interface import Session
from chatty.sessions.xmpp import XMPPSession, make_xmpp_client
from chatty.types import Handle
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
        xmpp_client1 = make_xmpp_client(self.config1)
        xmpp_client1.add_event_handler("ssl_invalid_cert", lambda *args, **kwargs: None)
        xmpp_client2 = make_xmpp_client(self.config2)
        xmpp_client2.add_event_handler("ssl_invalid_cert", lambda *args, **kwargs: None)
        return (self.config1.handle, XMPPSession(self.config1, xmpp_client1),
                self.config2.handle, XMPPSession(self.config2, xmpp_client2))

    # TODO: Add a test for this once support for XEP 0079 is added to sleekxmpp.
    # def test_delivery_failure(self):


if __name__ == '__main__':
    unittest.main()
