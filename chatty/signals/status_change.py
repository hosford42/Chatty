from typing import NewType, Optional

from chatty.signals.interface import Signal
from chatty.signals.metadata import SignalMetaData


StatusType = NewType('StatusType', str)
StatusValue = NewType('StatusValue', str)


class StatusChange(Signal):

    def __init__(self, meta_data: SignalMetaData, type_: StatusType, value: StatusValue, message: str = None):
        super().__init__(meta_data)
        self._type = type_
        self._value = value
        self._message = message

    @property
    def type(self) -> StatusType:
        return self._type

    @property
    def value(self) -> StatusValue:
        return self._value

    @property
    def message(self) -> Optional[str]:
        return self._message
