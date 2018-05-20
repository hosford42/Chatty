from collections import deque
import getpass
import time
import unittest
from typing import Iterable, Tuple

from chatty.messages import Message
from chatty.session_interface import Session
from chatty.signal_metadata import SignalMetaData
from chatty.types import Handle, SignalID
from chatty.standard_bot import make_bot
from chatty.xmpp_session import XMPPSession

from test_chatty.support import assert_same_message, SessionTestCase
from test_chatty.support import get_protocol_test_config


class TestXMPPSession(SessionTestCase):

    def setUp(self):
        self.config1 = get_protocol_test_config('XMPP #1', 5222)
        self.config2 = get_protocol_test_config('XMPP #2', 5222)
        super().setUp()

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        return self.config1.handle, XMPPSession(self.config1), self.config2.handle, XMPPSession(self.config2)
