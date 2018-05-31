from collections import deque
from typing import Union, Optional
import datetime
import logging
import threading
import time

import tzlocal

from slackclient import SlackClient
from slackclient.server import SlackConnectionError
from slackclient.channel import Channel
from slackclient.user import User

from chatty.exceptions import AuthenticationFailure, OperationNotSupported
from chatty.sessions.interface import Session
from chatty.signals.delivery_failure import DeliveryFailure
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.signals.status_change import StatusChange
from chatty.types import Handle, SignalID, Password, StatusTypes, TypingStatusValues


LOGGER = logging.getLogger(__name__)


class SlackSession(Session):
    """
    A Slack chat session interface.
    """

    # TODO: Accept a factory function which returns new SlackClients, similar to how EmailSession works.
    def __init__(self, slack_client: Union[Password, SlackClient], starting: datetime.datetime = None,
                 rate_limit: float = 1):
        super().__init__()

        if isinstance(slack_client, str):
            slack_client = SlackClient(token=slack_client)

        self._slack_client = slack_client
        self._starting = datetime.datetime.now(tzlocal.get_localzone()) if starting is None else starting

        if not self._slack_client.rtm_connect():
            raise AuthenticationFailure()

        self._handle = self._slack_client.server.login_data['self']['id']
        self._nickname = self._slack_client.server.login_data['self']['name']

        self._main_thread = threading.current_thread()
        self._thread_error = None
        self._outbound_queue = deque()
        self._rate_limit = rate_limit

        self._slack_thread = threading.Thread(target=self._slack_thread_main, daemon=True)
        self._alive = True
        self._slack_thread.start()
        self._check_for_thread_errors()

    def _check_for_thread_errors(self):
        if self._thread_error and threading.current_thread() == self._main_thread:
            thread_error, self._thread_error = self._thread_error, None
            raise thread_error

    def _notify_thread_error(self, exc: Exception):
        LOGGER.exception("Error in thread: %s" % exc)
        self._thread_error = exc

    def close(self):
        self._alive = False
        self._slack_thread.join(timeout=5)
        self._check_for_thread_errors()

    def join(self, timeout=None):
        self._slack_thread.join(timeout)

    def send(self, signal: Signal) -> None:
        if not isinstance(signal, Message):
            raise TypeError(signal)

        if signal.meta_data.visible_to:
            raise OperationNotSupported("Slack interface does not support carbon-copying.")

        self._outbound_queue.append(signal)
        self._check_for_thread_errors()

    def _handle_outbound_message(self, message: Message):
        content = str(message.content)
        if message.meta_data.room:
            self._slack_client.rtm_send_message(message.meta_data.room, content)
            time.sleep(self._rate_limit)
        for handle in message.meta_data.addressees:
            self._slack_client.rtm_send_message(handle, content)
            time.sleep(self._rate_limit)

    def _get_user_info(self, user_id) -> Optional[User]:
        return self._slack_client.server.users.get(user_id, None)

    def _get_channel_info(self, channel_id) -> Optional[Channel]:
        return self._slack_client.server.channels.find(channel_id)

    def _get_event_meta_data(self, event):
        room = event['channel']

        origin = event['user']
        user = self._get_user_info(origin)
        if user:
            origin = user.name

        time_stamp = event.get('ts', None)
        if time_stamp is None:
            sent_time = None
        else:
            sent_time = datetime.datetime.fromtimestamp(float(time_stamp))

        visible_to = []
        channel = self._get_channel_info(room)
        if channel:
            room = channel.name
            for member in channel.members:
                user = self._get_user_info(member)
                visible_to.append(Handle(user.name if user else member))

        bot = Handle(self._slack_client.server.username)
        if visible_to:
            addressees = None  # We can't know.
        else:
            # This only happens when we're in a private channel, so the addressee is clear.
            addressees = [bot]

        if origin not in visible_to:
            visible_to.append(Handle(origin))
        if bot not in visible_to:
            visible_to.append(bot)

        return SignalMetaData(
            identifier=SignalID('/'.join([room, origin, time_stamp])),
            origin=Handle(origin),
            addressees=addressees,
            visible_to=visible_to,
            response_to=None,
            sent_at=sent_time,
            received_at=datetime.datetime.now(),
            room=Handle(room)
        )

    def _handle_inbound_message(self, event):
        # Make sure it's an ordinary message.
        if (event.get('subtype') or not event.get('text') or not event.get('channel') or event.get('hidden') or
                float(event.get('ts', 0)) < self._starting.timestamp()):
            # TODO: Convert these to the appropriate MIME representation and pass them on to receive().
            LOGGER.warning("Ignoring non-standard message: %s" % event)
            return

        # Keys: type, ts (time stamp string), team, user, channel, text
        content = event['text']
        meta_data = self._get_event_meta_data(event)
        message = Message(meta_data, content)
        self.receive(message)

    # noinspection PyMethodMayBeStatic
    def _handle_inbound_presence_change(self, event):
        # TODO: Handle these once we can get the server to generate one as an example.
        LOGGER.warning("Ignoring presence change event: %s" % event)

    def _handle_inbound_user_typing(self, event):
        LOGGER.info("Received user typing event: %s" % event)
        meta_data = self._get_event_meta_data(event)
        signal = StatusChange(meta_data, StatusTypes.TYPING, TypingStatusValues.STARTED)
        self.receive(signal)

    # noinspection PyMethodMayBeStatic
    def _handle_inbound_hello(self, event):
        LOGGER.info("Server says hello: %s" % event)

    # noinspection PyMethodMayBeStatic
    def _handle_inbound_reconnect_url(self, event):
        LOGGER.info("Received reconnect url event: %s" % event)

    def _handle_inbound_error(self, event):
        error = event['error']
        if error['msg'] in ('invalid channel id', 'channel not found'):
            meta_data = SignalMetaData(received_at=datetime.datetime.now())
            self.receive(DeliveryFailure(meta_data, error['msg'], error['code']))
        else:
            # TODO: Handle these.
            LOGGER.warning("Ignoring inbound error event: %s" % event)

    # noinspection PyUnusedLocal
    @staticmethod
    def _handle_pong(event):
        LOGGER.info("Server responded to ping.")

    def _slack_thread_main(self):
        # TODO: dnd_updated_user, channel_joined Are there others? Also, why isn't presence_change getting triggered?
        inbound_event_handlers = {
            'message': self._handle_inbound_message,
            'presence_change': self._handle_inbound_presence_change,
            'user_typing': self._handle_inbound_user_typing,
            'hello': self._handle_inbound_hello,
            'reconnect_url': self._handle_inbound_reconnect_url,
            'error': self._handle_inbound_error,
            'pong': self._handle_pong,
            'desktop_notification': lambda e: None,  # Just ignore these. We don't even need to log them.
        }
        while self._alive:
            # noinspection PyBroadException
            try:
                if self._outbound_queue:
                    message = self._outbound_queue.popleft()
                    self._handle_outbound_message(message)
                else:
                    for event in self._slack_client.rtm_read():
                        event_type = event.get('type')
                        if not event_type:
                            # It's an acknowledgement.
                            # Keys: ok, reply_to, ts, and text
                            continue
                        handler = inbound_event_handlers.get(event_type, None)
                        if handler is None:
                            LOGGER.warning("Unhandled Slack event: %s", event)
                        else:
                            handler(event)
                    time.sleep(self._rate_limit)
            except SlackConnectionError:
                # TODO: If we have a SlackClient factory function, call it to get a new connection instead of dying.
                LOGGER.exception("Fatal error in Slack thread.")
                self._alive = False
                return
            except Exception:
                LOGGER.exception("Error in Slack thread.")
                time.sleep(self._rate_limit)
