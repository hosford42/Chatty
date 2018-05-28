from typing import Optional

from chatty.signals.metadata import SignalMetaData
from chatty.types import Content


class Signal:

    def __init__(self, meta_data: SignalMetaData, content: Content = None):
        self._meta_data = meta_data
        self._content = content

    @property
    def meta_data(self) -> SignalMetaData:
        return self._meta_data

    @property
    def content(self) -> Optional[Content]:
        return self._content

    def __eq__(self, other: 'Signal') -> bool:
        if not isinstance(other, Signal):
            return NotImplemented
        return type(self) is type(other) and self._meta_data == other._meta_data and self._content == other._content

    def __ne__(self, other: 'Signal') -> bool:
        if not isinstance(other, Signal):
            return NotImplemented
        return not (type(self) is type(other) and self._meta_data == other._meta_data and
                    self._content == other._content)

    def __hash__(self) -> int:
        return hash(self._meta_data)
