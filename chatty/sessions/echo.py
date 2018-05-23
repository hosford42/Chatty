from chatty.sessions.interface import Session
from chatty.signals.interface import Signal


class EchoSession(Session):
    """
    A session which simply echos any signal it is asked to send back to its own bots.
    """

    def __init__(self):
        super().__init__()

    def send(self, signal: Signal) -> None:
        self.receive(signal)
