from collections import deque
from threading import Thread, Condition

from chatty.bots.interface import Bot
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal


class SynchronizedBot(Bot):

    def __init__(self, wrapped: Bot):
        super().__init__()
        self._wrapped = wrapped
        self._queue = deque()
        self._queue_thread = Thread(target=self._process_signals, daemon=True)
        self._signal_queued = Condition()
        self._alive = True
        self._queue_thread.start()

    def __del__(self):
        with self._signal_queued:
            self._alive = False
            self._signal_queued.notify()
        self._queue_thread.join()

    @property
    def wrapped(self) -> Bot:
        return self._wrapped

    def close(self) -> None:
        with self._signal_queued:
            self._alive = False
            self._signal_queued.notify()

    def receive(self, session: Session, signal: Signal) -> None:
        if not self._alive:
            return
        with self._signal_queued:
            self._queue.append((session, signal))
            self._signal_queued.notify()

    def _process_signals(self):
        with self._signal_queued:
            while self._alive:
                self._signal_queued.wait_for(lambda: not self._alive or bool(self._queue))
                if self._alive and self._queue:
                    session, signal = self._queue.popleft()
                    self._wrapped.receive(session, signal)
