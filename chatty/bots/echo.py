from chatty.bots.interface import Bot
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal


class EchoBot(Bot):
    """
    A bot which simply echos any signal it receives back to the originating session.
    """

    def receive(self, session: Session, signal: Signal) -> None:
        session.send(signal)
