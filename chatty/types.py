from typing import NamedTuple, Optional, NewType

ErrorCode = NewType('ErrorCode', str)
SignalID = NewType('SignalID', str)

IPAddress = NewType('IPAddress', str)
Port = NewType('Port', int)
Handle = NewType('Handle', str)
Password = NewType('Password', str)

ProtocolConfig = NamedTuple(
    'ProtocolConfig',
    [('host', IPAddress),
     ('port', Port),
     ('user', Handle),
     ('password', Password),
     ('handle', Handle),
     ('nickname', Optional[Handle])]
)
