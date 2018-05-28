
from chatty.signals.interface import Signal
from chatty.signals.metadata import SignalMetaData
from chatty.types import ErrorCode, Content


class DeliveryFailure(Signal):

    def __init__(self, meta_data: SignalMetaData, content: Content = None, error_code: ErrorCode=None):
        super().__init__(meta_data, content)
        self._error_code = error_code

    @property
    def error_code(self) -> ErrorCode:
        return self._error_code
