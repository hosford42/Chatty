from typing import Iterable, Tuple
import datetime
import unittest

from chatty.bots.standard import make_bot
from chatty.sessions.interface import Session
from chatty.sessions.tkinter import TkChatSession
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.types import Handle

from test_chatty.support import BaseClasses


class TkChatClientTestCase(BaseClasses.SessionTestCase):

    def setUp(self):
        super().setUp()
        self.thread_error = None

    def meta_data_sequence(self) -> Iterable[SignalMetaData]:
        for counter in range(10):
            yield SignalMetaData(origin=self.sender_handle, addressees=[self.receiver_handle])

    def get_bot(self):
        # noinspection PyUnusedLocal
        def say_what(sess: TkChatSession, sig: Signal):
            assert isinstance(sig, Message)
            meta_data = SignalMetaData(
                origin=sig.meta_data.addressees[0] if sig.meta_data.addressees else 'Bot',
                addressees=[sig.meta_data.origin],
                response_to=sig.meta_data.identifier,
                sent_at=datetime.datetime.now(),
                room=sig.meta_data.room
            )
            return Message(meta_data=meta_data, content="You said: %s" % sig.content)
        return make_bot(say_what)

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        sender_handle = Handle('Human')
        receiver_handle = Handle('Bot')
        session = TkChatSession(sender_handle)
        return sender_handle, session, receiver_handle, session

    def test(self):
        # TODO: Emulate keystrokes on behalf of the user in a separate thread, instead of requiring someone to
        #       actually interact with the bot here.
        self.sender_session.run()


if __name__ == '__main__':
    unittest.main()
