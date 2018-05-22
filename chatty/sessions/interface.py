from abc import ABCMeta, abstractmethod
import logging

import chatty.bots.interface
import chatty.signals


LOGGER = logging.getLogger(__name__)


class Session(metaclass=ABCMeta):
    """Abstract interface for bot sessions."""

    def __init__(self):
        self._bots = set()

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        pass

    @abstractmethod
    def send(self, signal: 'chatty.signals.interface.Signal') -> None:
        raise NotImplementedError()

    def add_bot(self, bot: 'chatty.bots.interface.Bot') -> None:
        self._bots.add(bot)

    def remove_bot(self, bot: 'chatty.bots.interface.Bot') -> None:
        self._bots.remove(bot)

    def receive(self, signal: 'chatty.signals.interface.Signal') -> None:
        for bot in self._bots:
            # noinspection PyBroadException
            try:
                bot.receive(self, signal)
            except Exception:
                LOGGER.exception("Error in Bot.receive().")
