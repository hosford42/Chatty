from collections import deque
import datetime
import logging
import threading
import time

import tzlocal

from slackclient import SlackClient

from chatty.exceptions import AuthenticationFailure, OperationNotSupported
from chatty.sessions.interface import Session
from chatty.signals.delivery_failure import DeliveryFailure
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.types import Handle, SignalID


LOGGER = logging.getLogger(__name__)


class SlackSession(Session):
    """
    A Slack chat session interface.
    """

    def __init__(self, slack_client: SlackClient, starting: datetime.datetime = None, rate_limit: float = 1):
        super().__init__()

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

        self._slack_thread = threading.Thread(target=self._slack_thread_main)
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

    def _handle_inbound_message(self, event):
        # Make sure it's an ordinary message.
        if (event.get('subtype') or not event.get('text') or not event.get('channel') or event.get('hidden') or
                float(event.get('ts', 0)) < self._starting.timestamp()):
            # TODO: Handle these.
            LOGGER.warning("Ignoring non-standard message: %s" % event)
            return

        # Keys: type, ts (time stamp string), team, user, channel, text
        room = Handle(event['channel'])
        origin = Handle(event['user'])
        content = event['text']
        time_stamp = event['ts']
        sent_time = datetime.datetime.fromtimestamp(float(time_stamp))
        meta_data = SignalMetaData(
            identifier=SignalID('/'.join([room, origin, time_stamp])),
            origin=origin,
            addressees=None,
            visible_to=None,  # TODO: List all user on the channel
            response_to=None,
            sent_at=sent_time,
            received_at=datetime.datetime.now(),
            room=room
        )
        message = Message(meta_data, content)
        self.receive(message)

    # noinspection PyMethodMayBeStatic
    def _handle_inbound_presence_change(self, event):
        # TODO: Handle these.
        LOGGER.warning("Ignoring presence change event: %s" % event)

    # noinspection PyMethodMayBeStatic
    def _handle_inbound_user_typing(self, event):
        # TODO: Handle these.
        LOGGER.warning("Ignoring user typing event: %s" % event)

    # noinspection PyMethodMayBeStatic
    def _handle_inbound_hello(self, event):
        LOGGER.info("Server says hello: %s" % event)

    # noinspection PyMethodMayBeStatic
    def _handle_inbound_reconnect_url(self, event):
        # TODO: Handle these.
        LOGGER.warning("Ignoring reconnect url event: %s" % event)

    def _handle_inbound_error(self, event):
        error = event['error']
        if error['msg'] in ('invalid channel id', 'channel not found'):
            meta_data = SignalMetaData(received_at=datetime.datetime.now())
            self.receive(DeliveryFailure(meta_data, error['msg'], error['code']))
        else:
            # TODO: Handle these.
            LOGGER.warning("Ignoring inbound error event: %s" % event)

    def _slack_thread_main(self):
        inbound_event_handlers = {
            'message': self._handle_inbound_message,
            'presence_change': self._handle_inbound_presence_change,
            'user_typing': self._handle_inbound_user_typing,
            'hello': self._handle_inbound_hello,
            'reconnect_url': self._handle_inbound_reconnect_url,
            'error': self._handle_inbound_error,
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
                            # TODO: Handle these.
                            LOGGER.warning("Unhandled Slack event: %s", event)
                        else:
                            handler(event)
            except Exception:
                LOGGER.exception("Error in Slack thread.")
                time.sleep(self._rate_limit)
