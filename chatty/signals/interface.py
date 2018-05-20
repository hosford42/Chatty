
from chatty.signals.metadata import SignalMetaData


class Signal:

    def __init__(self, meta_data: SignalMetaData):
        self._meta_data = meta_data

    @property
    def meta_data(self) -> SignalMetaData:
        return self._meta_data
