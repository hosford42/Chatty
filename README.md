# Chatty

*A multi-platform chat bot framework*

## Description

Chatty is a Python 3 package designed to map any chat platform to the same
standardized interface. The goal is to allow a chat bot to be remapped 
from one platform or protocol to another, or even to multiple platforms
at the same time, with nothing more than a change to a configuration file.


## Current Development Status

Chatty is brand new, and has currently only been tested for basic message
delivery using email (imap & smtp, but not pop3 yet) and xmpp. Support for
Slack is underway. See the [TODO list] for a list of platforms & protocols 
that will (hopefully) eventually be added.


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
agree, as per standard practice, and also the [GitHub terms of service] to 
make your code available under the [license] governing this project.


## Design Requirements

### Signalling

* Asynchronous inbound signal stream
* Synchronous inbound signal queue
* Supported inbound/outbound signal types:
    * Message (I/O)
        * Subject
        * Multimedia content
        * Attachments
    * File (I/O)
        * File name
        * Content or download URL
    * Send failure (I)
        * Error type
        * Error message 
    * Status change (I/O)
        * Status type (on/offline, available/busy, present in room, typing in room)
        * Status message
    * User-defined (I/O)
  Additionally, I/O signal types have the following metadata:
    * Unique ID
    * Response to signal ID
    * Sent time
    * Received time
    * Origin address ("from" for email, "sender" for IMs)
    * Addressee addresses ("to" for email, direct IMs)
    * Visible to addresses ("to" for room IMs, "cc" for email)
* Supported internal signal types:
    * Connection error
    * Session started
    * Initiate session end
    * Session about to end
    * Session ended
    * Download file
    * System error
    * Unsupported signal

### Queries

* Address type (individual, group, channel)
* Components of address (other addresses this group/channel currently contains)
* Current status of any address
* Signals previously received from an address
* Signals previously sent to an address
* Delivery status of a signal
* Current status of an individual address with respect to a channel 
* Current status of the bot with respect to a channel
* Which signals are supported by an address
* Which message types/features are supported by an address


### Structure

* Bot interface
    * Determines standard interface for all chat bots    
* Synchronizer
    * Decorates the bot interface with a synchronized signal queue,
      allowing asynchronous interaction with a synchronous bot
* Logger
    * Decorates the bot interface with interaction logging
* Session
    * Interfaces a bot to a messaging protocol such as SMTP or XMPP
    * Multiple servers may interact with the same bot
* Proxy
    * Maps a remotely operating bot (or person), accessed via a messaging 
      protocol such as SMTP or XMPP, to the bot interface
* Direct chat connection
    * Links two or more bots together for local, direct interaction 
* Client
    * Maps a user interface (i.e. a chat window) to the bot interface


[chatty/sessions]: https://github.com/hosford42/Chatty/tree/master/chatty/sessions
[GitHub terms of service]: https://help.github.com/articles/github-terms-of-service/#6-contributions-under-repository-license
[license]: https://github.com/hosford42/Chatty/blob/master/LICENSE
[pep8 guidelines]: https://www.python.org/dev/peps/pep-0008/
[setup.py]: https://github.com/hosford42/Chatty/blob/master/setup.py
[test_chatty]: https://github.com/hosford42/Chatty/tree/master/test_chatty 
[TODO list]: https://github.com/hosford42/Chatty/blob/master/TODO.md
