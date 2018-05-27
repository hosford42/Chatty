from typing import Tuple
import unittest

from chatty.sessions.echo import EchoSession
from chatty.sessions.interface import Session
from chatty.types import Handle
from test_chatty.support import BaseClasses


class EchoSessionTestCase(BaseClasses.SessionTestCase):

    def get_session_pair(self) -> Tuple[Handle, Session, Handle, Session]:
        session = EchoSession()
        return Handle('test1'), session, Handle('test2'), session


if __name__ == '__main__':
    unittest.main()
