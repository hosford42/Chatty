from abc import ABCMeta, abstractmethod

import chatty.sessions.interface
import chatty.signals.interface


class Bot(metaclass=ABCMeta):
    """Abstract interface for bots."""

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        pass

    @abstractmethod
    def receive(self, session: 'chatty.sessions.interface.Session', signal: 'chatty.signals.interface.Signal') -> None:
        raise NotImplementedError()
