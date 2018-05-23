import logging
from itertools import chain
from typing import Dict, Set

from chatty.bots.interface import Bot
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.types import Handle


LOGGER = logging.getLogger(__name__)


class RouterBot(Bot):
    """A bot router which directs each incoming signal to the correct bot(s) based on its metadata."""

    def __init__(self):
        super().__init__()
        self._bot_map = {}  # type: Dict[Handle, Set[Bot]]

    def register_bot(self, handle: Handle, bot: Bot):
        if handle in self._bot_map:
            self._bot_map[handle].add(bot)
        else:
            self._bot_map[handle] = {bot}

    def unregister_bot(self, handle: Handle, bot: Bot):
        if handle in self._bot_map:
            self._bot_map[handle].discard(bot)
            if not self._bot_map[handle]:
                del self._bot_map[handle]

    def receive(self, session: Session, signal: Signal):
        mapped = False
        for handle in chain(signal.meta_data.addressees, signal.meta_data.visible_to):
            if handle in self._bot_map:
                for bot in self._bot_map[handle]:
                    # noinspection PyBroadException
                    try:
                        bot.receive(session, signal)
                    except Exception:
                        LOGGER.exception("Exception in bot router for handle %s" % handle)
                    mapped = True
        if not mapped:
            LOGGER.warning("Unhandled signal in bot router:\n%s" % signal)
