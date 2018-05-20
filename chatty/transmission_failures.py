from typing import Optional

from chatty.signals import Signal
from chatty.signal_metadata import SignalMetaData
from chatty.types import ErrorCode


class TransmissionFailure(Signal):

    def __init__(self, meta_data: SignalMetaData, error_code: ErrorCode, error_message: str = None):
        super().__init__(meta_data)
        self._error_code = error_code
        self._error_message = error_message

    @property
    def error_code(self) -> ErrorCode:
        return self._error_code

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message
