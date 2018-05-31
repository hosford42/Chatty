import datetime
import logging
import threading

import tzlocal

# See:
#   * http://sleekxmpp.com/getting_started/muc.html
#   * http://sleekxmpp.com/getting_started/echobot.html
#   * https://github.com/fritzy/SleekXMPP/wiki/Stanzas:-Message
from sleekxmpp import ClientXMPP

from chatty.exceptions import OperationNotSupported
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.signals.status_change import StatusChange
from chatty.types import LoginConfig, Handle, SignalID, StatusTypes, PresenceStatusValues, TypingStatusValues

LOGGER = logging.getLogger(__name__)


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

        # See https://xmpp.org/extensions/xep-0085.html#definitions
        self._xmpp_client.add_event_handler("chatstate_active", self.on_chatstate_active)
        self._xmpp_client.add_event_handler("chatstate_composing", self.on_chatstate_composing)
        self._xmpp_client.add_event_handler("chatstate_gone", self.on_chatstate_gone)
        self._xmpp_client.add_event_handler("chatstate_inactive", self.on_chatstate_inactive)
        self._xmpp_client.add_event_handler("chatstate_paused", self.on_chatstate_paused)

        self._main_thread = threading.current_thread()
        self._thread_error = None

        self._alive = True
        self._process_thread = threading.Thread(target=self._process_main, daemon=True)
        self._process_thread.start()

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
        self._alive = False
        self._process_thread.join()
        self._check_for_thread_errors()

    def join(self, timeout=None):
        self._process_thread.join(timeout)

    def send(self, signal: Signal) -> None:
        # TODO: Handle outbound presence & typing status changes.

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

    @staticmethod
    def _get_meta_data(event):
        origin = Handle(event['from'].bare)
        visible_to = [origin]

        if event.get('to', None):
            addressees = [Handle(event['to'].bare)]
            visible_to.extend(addressees)
        else:
            addressees = None

        if event.get('room', None):
            room = Handle(event['room'].bare)
            # TODO: Add everyone in the room to visible_to
        else:
            room = None

        return SignalMetaData(
            identifier=SignalID(event['id']),
            origin=origin,
            addressees=addressees,
            visible_to=visible_to,
            response_to=None,
            sent_at=None,
            received_at=datetime.datetime.now(),
            room=room
        )

    def on_message(self, message):
        try:
            LOGGER.info("Message received.")

            # Only handle regular chat messages
            if message['type'] not in ('chat', 'normal'):
                LOGGER.debug("Ignoring non-chat message.")
                return

            meta_data = self._get_meta_data(message)
            message = Message(meta_data, message['body'])
            self.receive(message)
        except Exception as exc:
            LOGGER.exception("Error in on_message()")
            self._notify_thread_error(exc)

    def on_group_chat_message(self, message):
        try:
            LOGGER.info("Group-chat message received.")

            # Only handle group chat messages
            if message['type'] != 'groupchat':
                LOGGER.debug("Ignoring non-groupchat message.")
                return

            meta_data = self._get_meta_data(message)
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

    def on_chatstate_active(self, event):
        try:
            LOGGER.info("Presence=present message received.")
            meta_data = self._get_meta_data(event)
            signal = StatusChange(meta_data, StatusTypes.PRESENCE, PresenceStatusValues.PRESENT)
            self.receive(signal)
        except Exception as exc:
            LOGGER.exception("Error in on_chatstate_active()")
            self._notify_thread_error(exc)

    def on_chatstate_inactive(self, event):
        try:
            LOGGER.info("Presence=inactive message received.")
            meta_data = self._get_meta_data(event)
            signal = StatusChange(meta_data, StatusTypes.PRESENCE, PresenceStatusValues.INACTIVE)
            self.receive(signal)
        except Exception as exc:
            LOGGER.exception("Error in on_chatstate_inactive()")
            self._notify_thread_error(exc)

    def on_chatstate_gone(self, event):
        try:
            LOGGER.info("Presence=away message received.")
            meta_data = self._get_meta_data(event)
            signal = StatusChange(meta_data, StatusTypes.PRESENCE, PresenceStatusValues.AWAY)
            self.receive(signal)
        except Exception as exc:
            LOGGER.exception("Error in on_chatstate_gone()")
            self._notify_thread_error(exc)

    def on_chatstate_composing(self, event):
        try:
            LOGGER.info("Typing=started message received.")
            meta_data = self._get_meta_data(event)
            signal = StatusChange(meta_data, StatusTypes.TYPING, TypingStatusValues.STARTED)
            self.receive(signal)
        except Exception as exc:
            LOGGER.exception("Error in on_chatstate_composing()")
            self._notify_thread_error(exc)

    def on_chatstate_paused(self, event):
        try:
            LOGGER.info("Typing=stopped message received.")
            meta_data = self._get_meta_data(event)
            signal = StatusChange(meta_data, StatusTypes.TYPING, TypingStatusValues.STOPPED)
            self.receive(signal)
        except Exception as exc:
            LOGGER.exception("Error in on_chatstate_paused()")
            self._notify_thread_error(exc)

    def _process_main(self):
        while self._alive:
            try:
                # Connect to the XMPP server and start processing XMPP stanzas.
                if self._xmpp_client.connect((self._xmpp_connection_info.host, self._xmpp_connection_info.port)):
                    self._xmpp_client.process(block=True)
                else:
                    raise ConnectionError()
            except Exception as exc:
                LOGGER.exception("Error in xmpp client.")
                self._thread_error = exc


def make_xmpp_client(connection_info: LoginConfig):
    client = ClientXMPP('%s@%s' % (connection_info.user, connection_info.host), connection_info.password)
    client.use_signals()

    # TODO: Make sure all events are handled, and check if we should support other XEPs.
    client.register_plugin('xep_0030')  # Service Discovery
    client.register_plugin('xep_0045')  # Multi-User Chat
    client.register_plugin('xep_0085')  # Chat State Notifications
    client.register_plugin('xep_0199')  # XMPP Ping

    # TODO: Use XEP 0079 to add delivery failure notifications once the sleekxmpp plugin for this XEP is released.
    # client.register_plugin('xep_0079')  # Advanced Message Processing

    return client
