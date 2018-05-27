import datetime
import logging
import time

from chatty.sessions.interface import Session
from chatty.signals.interface import Signal
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData
from chatty.types import Handle, SignalID

import tkinter


LOGGER = logging.getLogger(__name__)


class TkChatSession(Session):

    def __init__(self, user_handle: str = None):
        super().__init__()

        self.user_handle = user_handle or 'User'

        window = tkinter.Tk()
        window.title('Chat')
        # window.resizable(0, 0)
        window.minsize(40, 20)
        self._window = window

        upper_frame = tkinter.Frame(window)
        self._upper_frame = upper_frame

        history = tkinter.Text(upper_frame, width=40, height=20)
        scroller = tkinter.Scrollbar(upper_frame)
        history.config(yscrollcommand=scroller.set)
        scroller.config(command=history.yview)
        self._history = history
        self._scroller = scroller

        lower_frame = tkinter.Frame(window)
        self._lower_frame = lower_frame

        input_field = tkinter.Entry(lower_frame)
        input_field.bind("<Return>", self.on_submit)
        self._input_field = input_field

        button = tkinter.Button(lower_frame, text='Send', command=self.on_submit)
        self._button = button

        history.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)
        scroller.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        upper_frame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

        button.pack(side=tkinter.RIGHT, fill=tkinter.NONE)
        input_field.pack(fill=tkinter.BOTH, expand=1)

        lower_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)

    def close(self):
        self._window.quit()

    def show(self, text):
        self._history.insert(tkinter.END, text + '\n')
        self._history.see(tkinter.END)

    def send(self, signal: Signal) -> None:
        """Send a signal on behalf of the bot."""
        if isinstance(signal, Message):
            self.show('%s: %s' % (signal.meta_data.origin, signal.content))
        else:
            LOGGER.warning("Unhandled signal in send(): %s" % signal)

    # noinspection PyUnusedLocal
    def on_submit(self, event=None):
        text = self._input_field.get().strip()
        self._input_field.delete(0, tkinter.END)
        if text:
            self.show(self.user_handle + ': ' + text)
            meta_data = SignalMetaData(
                identifier=SignalID(self.user_handle + str(time.time())),
                origin=Handle(self.user_handle),
                sent_at=datetime.datetime.now(),
            )
            signal = Message(meta_data=meta_data, content=text)
            self.receive(signal)

    def run(self):
        """You MUST call this method from the main thread after setting everything up."""
        try:
            # I'm not sure why it's necessary to update first, but this
            # ensures that the text input field really does get the focus.
            self._window.update()
            self._input_field.focus()

            self._window.mainloop()
        finally:
            self.close()
