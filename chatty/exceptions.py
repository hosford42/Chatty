class ChattySessionError(Exception):
    pass


class AuthenticationFailure(ChattySessionError):
    pass


class OperationNotSupported(ChattySessionError):
    pass
