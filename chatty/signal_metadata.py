import datetime
from typing import Sequence, Tuple, Optional

from chatty.types import Handle, SignalID


class SignalMetaData:

    def __init__(self, *, identifier: SignalID = None, origin: Handle = None, addressees: Sequence[Handle] = None,
                 visible_to: Sequence[Handle] = None, response_to: SignalID = None, sent_at: datetime.datetime = None,
                 received_at: datetime.datetime = None, room: Handle = None):
        self._identifier = identifier
        self._origin = origin
        self._addressees = tuple(addressees or ())
        self._visible_to = tuple(visible_to or ())
        self._response_to = response_to
        self._sent_at = sent_at
        self._received_at = received_at
        self._room = room

    def __str__(self) -> str:
        return '|'.join(str(item) for item in (self._identifier, self._origin, self._addressees, self._visible_to,
                                               self._response_to, self._sent_at, self._received_at, self._room))

    @property
    def identifier(self) -> Optional[SignalID]:
        return self._identifier

    @property
    def origin(self) -> Handle:
        return self._origin

    @property
    def addressees(self) -> Tuple[Handle, ...]:
        return self._addressees

    @property
    def visible_to(self) -> Tuple[Handle, ...]:
        return self._visible_to

    @property
    def response_to(self) -> Optional[SignalID]:
        return self._response_to

    @property
    def sent_at(self) -> Optional[datetime.datetime]:
        return self._sent_at

    @property
    def received_at(self) -> Optional[datetime.datetime]:
        return self._received_at

    @property
    def room(self) -> Optional[Handle]:
        return self._room
