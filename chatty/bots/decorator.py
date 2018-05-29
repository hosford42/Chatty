import logging
from typing import Callable, Type

from chatty.bots.standard import StandardBot
from chatty.bots.synchronized import SynchronizedBot
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal


LOGGER = logging.getLogger(__name__)


class DecoratorBot(StandardBot):

    def __init__(self, decorated: Callable[[Session, Signal], Signal]):
        self._decorated = decorated
        super().__init__(self.primary_handler)

    def primary_handler(self, session: Session, signal: Signal) -> None:
        # noinspection PyBroadException
        try:
            response = self._decorated(session, signal)
        except Exception:
            LOGGER.exception("Unhandled error in decorated function.")
        else:
            if response is not None:
                session.send(response)

    def remove_handler(self, handler: Callable[[Session, Signal], None]):
        if handler == self.primary_handler:
            raise ValueError("Cannot remove primary handler.")
        super().remove_handler(handler)

    def __call__(self, *args, **kwargs):
        return self._decorated(*args, **kwargs)


def as_bot(converser: Callable[[Session, Signal], None] = None, *, synchronized: bool = False,
           bot_type: Type[DecoratorBot] = None):
    if bot_type is None:
        bot_type = DecoratorBot
    if converser is None:
        return lambda func: as_bot(func, synchronized=synchronized, bot_type=bot_type)
    elif callable(converser):
        result = bot_type(converser)
        if synchronized:
            return SynchronizedBot(result)
        else:
            return result
    else:
        raise TypeError(converser)
