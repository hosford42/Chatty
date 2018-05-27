from typing import Callable, Optional, Iterable
import logging

from chatty.bots.interface import Bot
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.bots.synchronized import SynchronizedBot


LOGGER = logging.getLogger(__name__)


class StandardBot(Bot):

    def __init__(self, handler: Callable[[Session, Signal], None] = None):
        super().__init__()
        self._handlers = []
        if handler is not None:
            self._handlers.append(handler)

    @property
    def handlers(self) -> Iterable[Callable[[Session, Signal], None]]:
        return iter(self._handlers)

    def add_handler(self, handler: Callable[[Session, Signal], None]):
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[Session, Signal], None]):
        if handler in self._handlers:
            self._handlers.remove(handler)

    def receive(self, session: Session, signal: Signal) -> None:
        for handler in self._handlers:
            # noinspection PyBroadException
            try:
                handler(session, signal)
            except Exception:
                LOGGER.exception("Unhandled error in signal handler.")


def make_bot(converser: Callable[[Session, Signal], Optional[Signal]], synchronized: bool = False) -> Bot:
    def handler(sess: Session, sig: Signal) -> None:
        # noinspection PyBroadException
        try:
            response = converser(sess, sig)
        except Exception:
            LOGGER.exception("Unhandled error in converser function.")
        else:
            if response is not None:
                sess.send(response)
    bot = StandardBot(handler)
    if synchronized:
        bot = SynchronizedBot(bot)
    return bot
