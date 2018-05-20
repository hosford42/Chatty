from abc import ABCMeta, abstractmethod

import chatty.session_interface
import chatty.signals


class Bot(metaclass=ABCMeta):
    """Abstract interface for bots."""

    def __init__(self, session: 'chatty.session_interface.Session'):
        self._session = session
        session.add_bot(self)

    def __del__(self) -> None:
        self.close()

    @property
    def session(self) -> 'chatty.session_interface.Session':
        return self._session

    @session.setter
    def session(self, value: 'chatty.session_interface.Session') -> None:
        if value != self._session:
            value.add_bot(self)
            self._session.remove_bot(self)
            self._session = value

    def close(self) -> None:
        pass

    @abstractmethod
    def receive(self, signal: 'chatty.signals.Signal') -> None:
        raise NotImplementedError()
