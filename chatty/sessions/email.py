from email import message_from_bytes
# noinspection PyProtectedMember
from email.message import EmailMessage, MIMEPart
from email.utils import parsedate_to_datetime
from typing import Callable, Type
import datetime
import imaplib
import logging
import smtplib
import threading
import time

import tzlocal

from chatty.exceptions import OperationNotSupported, SignalTypeNotSupported
from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.delivery_failure import DeliveryFailure
from chatty.signals.metadata import SignalMetaData
from chatty.types import LoginConfig


LOGGER = logging.getLogger(__name__)


def parse_email_address_list(value):
    if not value or not value.strip():
        return None
    return [address.strip() for address in value.split(';') if address.strip()]


def parse_email_datetime(value, default=None):
    if value is None:
        return default
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        pass
    result = None
    for piece in value.split(';'):
        try:
            parsed = parsedate_to_datetime(piece)
        except (TypeError, ValueError):
            pass
        else:
            if result is None or result < parsed:
                result = parsed
    if result is None:
        result = default
    return result


def is_delivery_status_notification(message: EmailMessage) -> bool:
    # noinspection SpellCheckingInspection
    """See https://stackoverflow.com/questions/5298285/""" \
        """detecting-if-an-email-is-a-delivery-status-notification-and-extract-informatio
    for details on how to detect delivery status notifications.
    """
    # https://stackoverflow.com/questions/5298285/detecting-if-an-email-is-a-delivery-status-notification-and-extract-informatio
    return bool('mailer-daemon@' in message['from'].lower() or message['x-failed-recipients'] or
                'multipart/report' in message.get_content_type() or 'delivery-status' in message.get_content_type() or
                (message['action'] or '').lower() == 'failed' or
                (message['subject'] or '').lower().startswith('delivery status notification') or
                any('delivery-status' in part.get_content_type() for part in message.get_payload()
                    if not isinstance(part, str)))


class EmailSession(Session):
    """
    An SMTP/IMAP4 email session. The smtp_factory and imap_factory arguments should be functions which
    take no arguments and return fully initialized SMTP and IMAP4 connections, respectively. Connections should
    already be authenticated before being returned, and the IMAP4 connection should have the appropriate folder
    selected.
    """

    @classmethod
    def email_to_signal(cls, message: EmailMessage) -> 'Signal':
        meta_data = SignalMetaData(
            identifier=message['message-id'],
            origin=message['from'],
            addressees=parse_email_address_list(message['to']),
            visible_to=parse_email_address_list(message['cc']),
            response_to=message['in-reply-to'],
            sent_at=parse_email_datetime(message['date']),
            received_at=parse_email_datetime(message['received'])
        )

        # Check if it's a delivery failure notification.
        if is_delivery_status_notification(message):
            return DeliveryFailure(meta_data, content=message)

        return Message(meta_data, message)

    def __init__(self, smtp_factory: Callable[[], smtplib.SMTP], imap_factory: Callable[[], imaplib.IMAP4],
                 starting: datetime.datetime = None, rate: float = 300):
        super().__init__()
        self._smtp_factory = smtp_factory
        self._imap_factory = imap_factory
        self._starting = datetime.datetime.now(tzlocal.get_localzone()) if starting is None else starting
        self._rate = rate
        self._imap_thread = threading.Thread(target=self._imap_thread_main, daemon=True)
        self._alive = True
        self._imap_thread.start()

    def close(self):
        self._alive = False
        self._imap_thread.join(timeout=1)

    def send(self, signal: Signal) -> None:
        if not isinstance(signal, Signal):
            raise TypeError(type(signal))
        if not isinstance(signal, Message):
            raise SignalTypeNotSupported(type(signal))

        meta_data = signal.meta_data
        content = signal.content

        if isinstance(content, str):
            content_string = content
            content = MIMEPart()
            content.set_payload(content_string)

        if meta_data.room:
            raise OperationNotSupported("Chat rooms are not supported for email sessions.")

        if meta_data.identifier:
            content['message-id'] = meta_data.identifier
        if meta_data.origin:
            content['from'] = meta_data.origin
        if meta_data.addressees:
            content['to'] = ';'.join(meta_data.addressees)
        if meta_data.visible_to:
            content['cc'] = ';'.join(meta_data.visible_to)
        if meta_data.response_to:
            content['reply-to'] = meta_data.response_to

        with self._smtp_factory() as connection:
            connection.send_message(content)

    def _imap_thread_main(self):
        seen = set()
        while self._alive:
            # noinspection PyBroadException
            try:
                with self._imap_factory() as connection:
                    while self._alive:
                        where = '(SENTSINCE {date:%d-%b-%Y})'.format(date=self._starting - datetime.timedelta(1))
                        result, data = connection.uid('search', None, where)
                        if result != 'OK':
                            raise RuntimeError("Unexpected response to search command: %s" % result)
                        if data[0] is None:
                            message_ids = []
                        else:
                            message_ids = data[0].split()
                        for message_id in message_ids:
                            if message_id in seen:
                                continue
                            result, data = connection.uid('fetch', message_id, '(RFC822)')
                            if result != 'OK':
                                raise RuntimeError("Unexpected response to fetch command: %s" % result)
                            email_message = message_from_bytes(data[0][1])
                            sent_date = parse_email_datetime(email_message['date'], self._starting)
                            if sent_date >= self._starting:
                                seen.add(message_id)
                                self.receive(self.email_to_signal(email_message))
                        time.sleep(self._rate)
            except Exception:
                LOGGER.exception("Error while trying to read email.")
                time.sleep(self._rate)


class SMTPFactory:
    """Convenience class for creating"""

    def __init__(self, connection_info: LoginConfig, connection_type: Type[smtplib.SMTP] = smtplib.SMTP_SSL):
        self.connection_info = connection_info
        self.connection_type = connection_type

    def __call__(self) -> smtplib.SMTP:
        connection = self.connection_type(host=self.connection_info.host, port=self.connection_info.port)
        connection.connect(host=self.connection_info.host, port=self.connection_info.port)
        connection.ehlo()

        try:
            connection.login(self.connection_info.user, self.connection_info.password)
        except smtplib.SMTPNotSupportedError:
            LOGGER.critical("Login not supported for %s on %s:%s." %
                            (self.connection_type.__name__, self.connection_info.host, self.connection_info.port))

        return connection


class IMAPFactory:

    def __init__(self, connection_info: LoginConfig, mailbox: str = 'inbox',
                 connection_type: Type[imaplib.IMAP4] = imaplib.IMAP4_SSL):
        assert isinstance(connection_info, LoginConfig)
        self.connection_info = connection_info
        self.mailbox = mailbox
        self.connection_type = connection_type

    def __call__(self) -> imaplib.IMAP4:
        connection = self.connection_type(host=self.connection_info.host, port=self.connection_info.port)
        connection.login(self.connection_info.user, self.connection_info.password)
        connection.select(self.mailbox)
        return connection
