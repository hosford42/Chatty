class ChattySessionError(Exception):
    pass


class AuthenticationFailure(ChattySessionError, ConnectionRefusedError):
    pass


class OperationNotSupported(ChattySessionError, NotImplementedError):
    pass


class SignalTypeNotSupported(ChattySessionError, TypeError):
    pass
