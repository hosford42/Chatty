import os
import time
import unittest
from abc import abstractmethod, ABCMeta
from collections import deque
from typing import Tuple, Iterable

from chatty.bots.interface import Bot
from chatty.bots.standard import make_bot
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.support import get_protocol_config
from chatty.types import ProtocolConfig, Handle


def get_protocol_test_config(protocol: str, default_port: int, path: str = None) -> ProtocolConfig:
    if path is None:
        # Some IDEs (e.g. PyCharm) run the tests with the default CWD set to the test code's path when they're run
        # individually, so we can't rely on relative paths to be consistent.
        if os.path.isfile('.chatty_test_config'):
            path = '.chatty_test_config'
        else:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.chatty_test_config')
    return get_protocol_config(protocol, default_port, path)


def assert_same_message(original: Message, received: Message):
    if original.meta_data.identifier is not None:
        assert original.meta_data.identifier == received.meta_data.identifier
    assert original.meta_data.origin == received.meta_data.origin, received.meta_data
    assert original.meta_data.addressees == received.meta_data.addressees
    if original.meta_data.visible_to:
        assert original.meta_data.visible_to == received.meta_data.visible_to
    else:
        assert set(received.meta_data.visible_to) <= set(original.meta_data.addressees) | {original.meta_data.origin}
    assert original.meta_data.response_to == received.meta_data.response_to
    if original.meta_data.sent_at is not None:
        assert original.meta_data.sent_at == received.meta_data.sent_at
    assert set(str(original.content).splitlines()) <= set(str(received.content).splitlines())


class BaseClasses:
    """This is just an empty container around the unit test base classes, which prevents them from
    being picked up and run by unittest despite being abstract."""

    class SessionTestCase(unittest.TestCase, metaclass=ABCMeta):

        post_setup_pause = 1
        max_receiver_delay = 10

        @abstractmethod
        def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
            raise NotImplementedError()

        def meta_data_sequence(self) -> Iterable[SignalMetaData]:
            for counter in range(10):
                yield SignalMetaData(origin=self.sender_handle, addressees=[self.receiver_handle])

        def get_bot(self) -> Bot:
            return make_bot(lambda sess, sig: self.received.append(sig))

        def setUp(self):
            self.sender_handle, self.sender_session, self.receiver_handle, self.receiver_session = \
                self.get_session_pair()
            self.received = deque()
            self.bot = self.get_bot()
            self.receiver_session.add_bot(self.bot)
            time.sleep(self.post_setup_pause)

        def tearDown(self):
            self.bot.close()
            self.sender_session.close()
            self.receiver_session.close()
            assert not self.received

        def check_signal(self, original: Signal, received: Signal):
            self.assertEqual(type(original), type(received))
            if isinstance(original, Message):
                assert isinstance(received, Message)
                assert_same_message(original, received)

        def test(self):
            for index, meta_data in enumerate(self.meta_data_sequence()):
                content = "Message #%s" % index
                message = Message(meta_data, content)
                self.sender_session.send(message)

                for _ in range(self.max_receiver_delay * 1000):
                    time.sleep(.001)
                    if self.received:
                        self.check_signal(message, self.received.popleft())
                        break
                else:
                    self.check_signal(message, self.received.popleft())
                print("%s message #%s successful." % (type(self).__name__, index))
