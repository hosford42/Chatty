from typing import Callable, Optional
import logging

from chatty.bot_interface import Bot
from chatty.session_interface import Session
from chatty.signals import Signal
from chatty.synchronized_bot import SynchronizedBot


LOGGER = logging.getLogger(__name__)


class StandardBot(Bot):

    def __init__(self, session: Session):
        super().__init__(session)
        self._handlers = []

    def add_handler(self, handler: Callable[[Session, Signal], None]):
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[Session, Signal], None]):
        self._handlers.remove(handler)

    def receive(self, signal: Signal) -> None:
        for handler in self._handlers:
            # noinspection PyBroadException
            try:
                handler(self._session, signal)
            except Exception:
                LOGGER.exception("Unhandled error in signal handler.")


def make_bot(session: Session, converser: Callable[[Signal], Optional[Signal]]) -> SynchronizedBot:
    def handler(sess: Session, sig: Signal) -> None:
        # noinspection PyBroadException
        try:
            response = converser(sig)
        except Exception:
            LOGGER.exception("Unhandled error in converser function.")
        else:
            if response is not None:
                sess.send(response)
    bot = StandardBot(session)
    bot.add_handler(handler)
    return SynchronizedBot(bot)
