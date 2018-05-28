import datetime
import logging
import threading
from collections import OrderedDict

import tzlocal

# See:
#   * http://sleekxmpp.com/getting_started/muc.html
#   * http://sleekxmpp.com/getting_started/echobot.html
#   * https://github.com/fritzy/SleekXMPP/wiki/Stanzas:-Message
from sleekxmpp import ClientXMPP, JID

from chatty.exceptions import OperationNotSupported
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.types import LoginConfig, Handle, SignalID

LOGGER = logging.getLogger(__name__)


def search_nested_dict(root, keys):
    assert isinstance(root, (dict, OrderedDict))

    # Search for direct entries, in the order they appear in keys.
    for key in keys:
        if key not in root:
            continue
        nested = root[key]
        if isinstance(nested, str):
            LOGGER.debug("Found %s: %s", key, nested)
            yield (key,), nested
        elif isinstance(nested, JID):
            LOGGER.debug("Found %s: %s", key, nested)
            yield (key,), str(nested.bare)

    # Search for nested entries, in the order they appear in keys.
    for key in keys:
        if key not in root:
            continue
        nested = root[key]
        if isinstance(nested, (dict, OrderedDict)):
            LOGGER.debug("Searching %s: %s", key, nested)
            for path, value in search_nested_dict(nested, keys):
                yield (key,) + path, value


class XMPPSession(Session):
    """
    An XMPP chat session interface.
    """

    def __init__(self, connection_info: LoginConfig, xmpp_client: ClientXMPP = None,
                 starting: datetime.datetime = None):
        super().__init__()

        if xmpp_client is None:
            xmpp_client = make_xmpp_client(connection_info)

        self._xmpp_client = xmpp_client
        self._xmpp_connection_info = connection_info
        self._starting = datetime.datetime.now(tzlocal.get_localzone()) if starting is None else starting

        # Register callbacks for incoming messages
        self._xmpp_client.add_event_handler("session_start", self.on_session_started)
        self._xmpp_client.add_event_handler("message", self.on_message)
        self._xmpp_client.add_event_handler("groupchat_message", self.on_group_chat_message)
        self._xmpp_client.add_event_handler("failed_auth", self.on_failed_authentication)
        self._xmpp_client.add_event_handler("error", self.on_error)

        self._main_thread = threading.current_thread()
        self._thread_error = None

        # Connect to the XMPP server and start processing XMPP stanzas.
        if self._xmpp_client.connect((connection_info.host, connection_info.port)):
            self._xmpp_client.process(block=False)
        else:
            raise ConnectionError()

        self._check_for_thread_errors()

    def _check_for_thread_errors(self):
        if self._thread_error and threading.current_thread() == self._main_thread:
            thread_error, self._thread_error = self._thread_error, None
            raise thread_error

    def _notify_thread_error(self, exc: Exception):
        LOGGER.exception("Error in thread: %s" % exc)
        self._thread_error = exc

    def close(self):
        if hasattr(self, '_xmpp_client'):
            self._xmpp_client.disconnect()
        self._check_for_thread_errors()

    def send(self, signal: Signal) -> None:
        if not isinstance(signal, Message):
            raise TypeError(signal)
        assert isinstance(signal, Message)

        origin = signal.meta_data.origin
        if signal.meta_data.visible_to:
            raise OperationNotSupported("XMPP protocol does not support carbon-copying.")

        if signal.meta_data.room:
            self._xmpp_client.send_message(
                mfrom=origin,
                mto=signal.meta_data.room,
                mbody=str(signal.content),
                mtype='groupchat'
            )

        for recipient in signal.meta_data.addressees:
            self._xmpp_client.send_message(
                mfrom=origin,
                mto=recipient,
                mbody=str(signal.content),
                mtype='chat'
            )

        self._check_for_thread_errors()

    # noinspection PyUnusedLocal
    def on_session_started(self, event):
        try:
            LOGGER.info("Successfully connected and authenticated.")
            self._xmpp_client.get_roster()
            self._xmpp_client.send_presence()
        except Exception as exc:
            LOGGER.exception("Error in on_session_started()")
            self._notify_thread_error(exc)

    def on_message(self, message):
        try:
            LOGGER.info("Message received.")

            origin = message['from'].bare

            # Only handle regular chat messages
            if message['type'] not in ('chat', 'normal'):
                LOGGER.debug("Ignoring non-chat message.")
                return

            meta_data = SignalMetaData(
                identifier=SignalID(message['id']),
                origin=Handle(origin),
                addressees=[Handle(self._xmpp_connection_info.handle_configs[0].handle)],
                visible_to=[Handle(origin), Handle(self._xmpp_connection_info.handle_configs[0].handle)],
                response_to=None,
                sent_at=None,
                received_at=datetime.datetime.now(),
                room=None
            )
            message = Message(meta_data, message['body'])
            self.receive(message)
        except Exception as exc:
            LOGGER.exception("Error in on_message()")
            self._notify_thread_error(exc)

    def on_group_chat_message(self, message):
        try:
            LOGGER.info("Group-chat message received.")

            origin = Handle(message['from'].bare)

            nicks = [
                value
                for path, value
                in search_nested_dict(message.values, ['nick', 'mucnick'])
            ]

            # If the bot said it, it shouldn't respond to it.
            if self._xmpp_connection_info.nickname in nicks or self._xmpp_connection_info.handle == origin:
                LOGGER.debug("Ignoring self-generated message.")
                return

            # Only handle group chat messages
            if message['type'] != 'groupchat':
                LOGGER.debug("Ignoring non-groupchat message.")
                return

            # TODO: This is just a guess. I have no idea how to actually get the room. Test it!
            LOGGER.debug(message)
            room = Handle(message['room'])

            if message.get('to', None):
                addressees = [Handle(message['to'].bare)]
            else:
                addressees = None

            meta_data = SignalMetaData(
                identifier=SignalID(message['id']),
                origin=origin,
                addressees=addressees,
                visible_to=[origin, Handle(self._xmpp_connection_info.handle)],
                response_to=None,
                sent_at=None,
                received_at=datetime.datetime.now(),
                room=room
            )
            message = Message(meta_data, message['body'])
            self.receive(message)
        except Exception as exc:
            LOGGER.exception("Error in on_group_chat_message()")
            self._notify_thread_error(exc)

    # noinspection PyUnusedLocal
    def on_failed_authentication(self, event):
        try:
            LOGGER.critical("Authentication failed.")
            self.close()
        except Exception as exc:
            LOGGER.exception("Error in on_failed_authentication()")
            self._notify_thread_error(exc)

    # noinspection PyMethodMayBeStatic
    def on_error(self, event):
        LOGGER.error("XMPP error event: %s" % event)


def make_xmpp_client(connection_info: LoginConfig):
    client = ClientXMPP('%s@%s' % (connection_info.user, connection_info.host), connection_info.password)
    client.use_signals()
    client.register_plugin('xep_0030')  # Service Discovery
    client.register_plugin('xep_0045')  # Multi-User Chat
    client.register_plugin('xep_0199')  # XMPP Ping

    # TODO: Use XEP 0079 to add delivery failure notifications once the sleekxmpp plugin for this XEP is released.
    # client.register_plugin('xep_0079')  # Advanced Message Processing

    return client
