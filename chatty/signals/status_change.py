from chatty.signals.interface import Signal
from chatty.signals.metadata import SignalMetaData
from chatty.types import Content, StatusType, StatusValue


class StatusChange(Signal):

    def __init__(self, meta_data: SignalMetaData, type_: StatusType, value: StatusValue, content: Content = None):
        super().__init__(meta_data, content)
        self._type = type_
        self._value = value

    @property
    def type(self) -> StatusType:
        return self._type

    @property
    def value(self) -> StatusValue:
        return self._value
