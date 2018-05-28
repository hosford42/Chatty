# noinspection PyProtectedMember
from email.message import MIMEPart
from typing import NamedTuple, NewType, Optional, Tuple, Union

ErrorCode = NewType('ErrorCode', str)
SignalID = NewType('SignalID', str)

IPAddress = NewType('IPAddress', str)
Port = NewType('Port', int)
Handle = NewType('Handle', str)
Password = NewType('Password', str)

Content = NewType('Content', Union[str, MIMEPart])

StatusType = NewType('StatusType', str)
StatusValue = NewType('StatusValue', str)

HandleConfig = NamedTuple(
    'HandleConfig',
    [('label', str),
     ('handle', Handle),
     ('nickname', Optional[Handle])]
)

LoginConfig = NamedTuple(
    'LoginConfig',
    [('label', str),
     ('host', IPAddress),
     ('port', Port),
     ('user', Handle),
     ('password', Password),
     ('handle_configs', Tuple[HandleConfig, ...])]
)
