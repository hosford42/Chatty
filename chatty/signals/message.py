from chatty.signals.interface import Signal
from chatty.signals.metadata import SignalMetaData
from chatty.types import Content


class Message(Signal):

    def __init__(self, meta_data: SignalMetaData, content: Content):
        super().__init__(meta_data, content)

    @property
    def content(self) -> Content:  # The difference here is it's not optional
        return self._content
