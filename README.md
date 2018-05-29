# Chatty

*A multi-platform chat bot framework*


## Description

Chatty is a Python 3 package designed to map any chat platform to the same
standardized interface. The goal is to allow a chat bot to be remapped 
from one platform to another, or even to multiple platforms at the same time, 
with nothing more than a minor change in configuration.


Chatty is organized around 3 core abstractions:

* **Signals**: A signal is any single indivisible element of communication,
  such as a message or a notification, which may or may not contain
  content or data of some sort. Signals always come with certain attached
  *metadata* which indicates where the signal originated, who it was
  sent to, when it was sent, etc.
* **Bots**: A bot is an endpoint where inbound signals are handled, and
  outbound signals are generated.
* **Sessions**: A session is an open channel over which signals can be
  sent and/or received by a bot.


## Usage

```python
from chatty.bots.decorator import as_bot
from chatty.configuration import get_config
from chatty.sessions.slack import SlackSession
from chatty.signals.message import Message
from chatty.signals.metadata import SignalMetaData


# FRIENDLY REMINDER: Never store bot tokens or login passwords in your source
# code, and be careful that they aren't in a place where they could get picked 
# up by source control!

# Load the bot's handle and login token from the config file.
handle, token = get_config('Slack', '~/.chatty_config', ['handle'], ['token'])


@as_bot
def converse(session, signal):
    """Say 'hi!' back on the same channel whenever someone says 'hello'"""
    if isinstance(signal, Message) and 'hello' in str(signal.content).lower():
        meta_data = SignalMetaData(
            origin=handle,
            addressees=[signal.meta_data.room or signal.meta_data.origin],
            response_to=signal.meta_data.identifier
        )
        return Message(meta_data, 'hi!')


session = SlackSession(token)        # Create a new Slack session
session.add_bot(converse)            # Connect our bot to it
session.join(timeout=5 * 60)         # Hang out for 5 minutes
session.close()                      # Drop offline
```


## Current Development Status

Chatty is brand new, and has currently only been tested for basic messaging
via email (imap & smtp), xmpp, and Slack. See the [TODO list] for a list of 
other platforms that should eventually be supported.


## Contributing

If you have a need for a specific platform or protocol to be supported,
I'll be happy to accept pull requests. If you're looking to contribute 
but need a place to start, please see the [TODO list]. There are plenty of 
platforms and functionality yet to be added. Each supported platform has 
its own module in the [chatty/sessions] folder, and its dependencies 
should be added to the `extras_require` parameter in [setup.py]. Tests
go in the [test_chatty] folder and are named with `test_` prefixed to the 
name of the module being tested. 

Submitted code should adhere to [pep8 guidelines] and should, in general,
follow the conventions established elsewhere in the Chatty code base. For 
the sake of clarity, please note that by submitting a pull request, you 
agree, as per standard practice (and also the [GitHub terms of service]) 
to make your code available under the same [license] that governs this 
project.


[chatty/sessions]: https://github.com/hosford42/Chatty/tree/master/chatty/sessions
[GitHub terms of service]: https://help.github.com/articles/github-terms-of-service/#6-contributions-under-repository-license
[license]: https://github.com/hosford42/Chatty/blob/master/LICENSE
[pep8 guidelines]: https://www.python.org/dev/peps/pep-0008/
[setup.py]: https://github.com/hosford42/Chatty/blob/master/setup.py
[test_chatty]: https://github.com/hosford42/Chatty/tree/master/test_chatty 
[TODO list]: https://github.com/hosford42/Chatty/blob/master/TODO.md
