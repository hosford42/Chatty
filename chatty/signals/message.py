from typing import Union
# noinspection PyProtectedMember
from email.message import MIMEPart

from chatty.signals.metadata import SignalMetaData
from chatty.signals.interface import Signal


class Message(Signal):

    def __init__(self, meta_data: SignalMetaData, content: Union[str, MIMEPart]):
        super().__init__(meta_data)
        self._content = content

    @property
    def content(self) -> Union[str, MIMEPart]:
        return self._content

    def __eq__(self, other: 'Message') -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return self._meta_data == other._meta_data and self._content == other._content

    def __ne__(self, other: 'Message') -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return not (self._meta_data == other._meta_data and self._content == other._content)

    def __hash__(self) -> int:
        return hash(self._meta_data)
