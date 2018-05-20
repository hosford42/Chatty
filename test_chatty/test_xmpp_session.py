from typing import Tuple

from chatty.sessions.interface import Session
from chatty.types import Handle
from chatty.sessions.xmpp import XMPPSession

from test_chatty.support import SessionTestCase
from test_chatty.support import get_protocol_test_config


class TestXMPPSession(SessionTestCase):

    def setUp(self):
        self.config1 = get_protocol_test_config('XMPP #1', 5222)
        self.config2 = get_protocol_test_config('XMPP #2', 5222)
        super().setUp()

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        return self.config1.handle, XMPPSession(self.config1), self.config2.handle, XMPPSession(self.config2)
