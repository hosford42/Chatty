from abc import abstractmethod, ABCMeta
from collections import deque
# noinspection PyProtectedMember
from email.message import MIMEPart
from typing import Tuple, Iterable
import time
import unittest

from chatty.bots.standard_bot import make_bot
from chatty.signals.messages import Message
from chatty.sessions.interface import Session
from chatty.signals.metadata import SignalMetaData
from chatty.support import get_protocol_config
from chatty.types import ProtocolConfig, Handle


def get_protocol_test_config(protocol: str, default_port: int, path='.test_config') -> ProtocolConfig:
    return get_protocol_config(protocol, default_port, path)


def assert_same_message(original: Message, received: Message):
    if original.meta_data.identifier is not None:
        assert original.meta_data.identifier == received.meta_data.identifier
    assert original.meta_data.origin == received.meta_data.origin, \
        (original.meta_data.origin, received.meta_data.origin)
    assert original.meta_data.addressees == received.meta_data.addressees
    assert original.meta_data.visible_to == received.meta_data.visible_to
    assert original.meta_data.response_to == received.meta_data.response_to
    if original.meta_data.sent_at is not None:
        assert original.meta_data.sent_at == received.meta_data.sent_at
    assert set(str(original.content).splitlines()) <= set(str(received.content).splitlines())


class SessionTestCase(unittest.TestCase, metaclass=ABCMeta):

    post_setup_pause = 1
    max_receiver_delay = 10

    @abstractmethod
    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        raise NotImplementedError()

    def meta_data_sequence(self) -> Iterable[SignalMetaData]:
        for counter in range(10):
            yield SignalMetaData(origin=self.sender_handle, addressees=[self.receiver_handle])

    def setUp(self):
        self.sender_handle, self.sender_session, self.receiver_handle, self.receiver_session = self.get_session_pair()
        self.received = deque()
        self.bot = make_bot(self.receiver_session, lambda x: self.received.append(x))
        time.sleep(self.post_setup_pause)

    def tearDown(self):
        self.bot.close()
        self.sender_session.close()
        self.receiver_session.close()

    def test(self):
        for index, meta_data in enumerate(self.meta_data_sequence()):
            content = MIMEPart()
            content.set_payload("Message #%s" % index)
            message = Message(meta_data, content)
            self.sender_session.send(message)

            for _ in range(self.max_receiver_delay * 1000):
                time.sleep(.001)
                if self.received:
                    assert_same_message(message, self.received.popleft())
                    break
            else:
                assert_same_message(message, self.received.popleft())
