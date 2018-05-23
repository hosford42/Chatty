import logging
from itertools import chain
from typing import Dict, Set

from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.types import Handle


LOGGER = logging.getLogger(__name__)


class RouterSession(Session):
    """A session router which directs each outbound signal to the correct session(s) based on its metadata."""

    def __init__(self):
        super().__init__()
        self._session_map = {}  # type: Dict[Handle, Set[Session]]

    def register_session(self, handle: Handle, session: Session):
        if handle in self._session_map:
            self._session_map[handle].add(session)
        else:
            self._session_map[handle] = {session}

    def unregister_session(self, handle: Handle, session: Session):
        if handle in self._session_map:
            self._session_map[handle].discard(session)
            if not self._session_map[handle]:
                del self._session_map[handle]

    def send(self, signal: Signal):
        mapped = False
        for handle in chain(signal.meta_data.addressees, signal.meta_data.visible_to):
            if handle in self._session_map:
                for session in self._session_map[handle]:
                    # noinspection PyBroadException
                    try:
                        session.send(signal)
                    except Exception:
                        LOGGER.exception("Exception in session router for handle %s" % handle)
                    mapped = True
        if not mapped:
            LOGGER.warning("Unhandled signal in session router:\n%s" % signal)
