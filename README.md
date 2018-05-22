# Chat

This is a revamp of the server/client chat model from the NPC
package, modified to be chat bot-agnostic and fully generic.


## Requirements

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
