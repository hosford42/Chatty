# TODO

* Figure out how to make the sleekxmpp process thread a daemon, so tests don't
  hang when they fail.
* Query types:
    * Supported features/operations/message types
    * Address type (individual, group, channel)
    * Group/channel membership
    * Current presence/status associated with an address
    * User profile info
    * Message history
    * Delivery status of a signal
* Signal types:
    * Message **WIP**
        * Text
        * MIME
        * User mentions
        * Hash tags
        * Other content types
    * Arrival/departure
    * Status change
    * Started/stopped typing notification
    * Delivery failure
    * Delivery receipt
    * Ping/keep alive
* Session types:
    * Direct user-to-bot
    * Direct bot-to-bot  **DONE** (needs tests)
    * IMAP/smtp email (imaplib/smtplib, builtin) **DONE**
    * Slack ([slackclient](https://github.com/slackapi/python-slackclient), MIT) **DONE**
    * Discord ([discord.py](https://github.com/Rapptz/discord.py), MIT)
    * Reddit ([praw](https://praw.readthedocs.io/en/latest/), BSD)
    * Twitter ([twitter](https://github.com/sixohsix/twitter), MIT)
    * Facebook ([facebook-sdk](http://facebook-sdk.readthedocs.io/en/latest/), Apache)
    * Facebook Messenger ([fbchat](https://github.com/carpedm20/fbchat), BSD)
    * Kik ([kik-python](https://github.com/kikinteractive/kik-python), MIT)
    * LINE ([line](https://carpedm20.github.io/line/), BSD)
    * Viber ([viberbot](https://developers.viber.com/docs/api/python-bot-api/), Apache)
    * HipChat ([ac-flask-hipchat](https://bitbucket.org/atlassianlabs/ac-flask-hipchat), 
        Apache)
    * Google Hangouts ([google-api-python-client](
        https://developers.google.com/api-client-library/python/apis/chat/v1), Apache)
    * WeChat ([pywxclient](https://github.com/justdoit0823/pywxclient), Apache)
    * Pop3/smtp email (poplib/smtplib, builtin)
    * Telegram ([python-telegram-bot](
        https://github.com/python-telegram-bot/python-telegram-bot), **GPL or LGPL, unclear**)
    * WhatsApp ([yowsup](https://github.com/tgalal/yowsup), **GPL**)
    * Skype ([SkPy](https://pypi.org/project/SkPy/), **no defined license at this time**)
    * QQ Mobile
    * Mattermost
    * Rocket.Chat
    * Let's Chat (appears to support XMPP, meaning it's already covered)
    * SnapChat (these guys actively sabotage any library accessing their API. skip it)
    * Others? (see [this chart](
        https://www.statista.com/statistics/258749/most-popular-global-mobile-messenger-apps/))
