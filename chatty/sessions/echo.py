import time

from chatty.sessions.interface import Session
from chatty.signals.interface import Signal


class EchoSession(Session):
    """
    A session which simply echos any signal it is asked to send back to its own bots.
    """

    def __init__(self):
        super().__init__()
        self._alive = True

    def close(self):
        self._alive = False

    def join(self, timeout=None) -> None:
        if timeout is None:
            while self._alive:
                time.sleep(1)
        else:
            time.sleep(timeout)

    def send(self, signal: Signal) -> None:
        self.receive(signal)
