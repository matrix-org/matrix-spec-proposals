Abstract
========

The specification does not define an extensible way to attach data to an
``m.room.message`` event. Whilst we freely say that keys can be "anything you
want", this does not ensure interoperability between client implementations
which may have subtly different ways to express the same data. This proposal
defines a set of **guidelines** which client SHOULD use when attaching data to
``m.room.message`` events.

Proposal
========

All custom data SHOULD be grouped under a ``data`` key. All subsequent keys
mentioned are assumed to be contained under this key.

Messages may be linked to an HTTP URL. This URL SHOULD be represented as a
string under a ``link`` key. This link applies to the entire message (as if
the message was wrapped in an ``<a>`` tag). Clients MAY choose to clobber this
if URLs are present in the message body.

Similarly, if a message contains an entity which can be represented as a URI
(e.g. ``mailto``, ``irc``, ``xmpp``) it SHOULD be represented under a ``uri``
key.

Contextual data for this message SHOULD be contained under a ``context`` key.
If the message data is related to a website (Github, Google, Facebook, etc) then
a ``domain`` should be specified within ``context``. Likewise, if the message
data involves an entity (a Facebook user, a Github user, etc) then an ``entity``
should be specified within ``context``. Extra data which only makes sense within
the given context should be added as keys within the ``context`` object.


::

  type: "m.room.message",
  content: {
    msgtype: "m.text",
    body: "[matrix-org/matrix-ios-sdk] manuroe pushed 4 commits to develop",
    data: {
        "context": {
            "domain": "github.com",
            "entity": "manuroe",
            "commits": ["fe34764", "4cdd8ae", "528da705", "56bfc717"]
        }
        "link": "https://github.com/matrix-org/matrix-ios-sdk/commit/56bfc717",
        "uri": "https://github.com/matrix-org/matrix-ios-sdk.git"
    }
  }


Rationale
=========

Extensible data is inserted under the ``data`` key to avoid polluting the
top-level ``body`` namespace. The intention of ``link`` is to allow an entire
message to be clickable (e.g. git commits )

- why under data key
- why link AND uri keys
- 

Clients may wish to display messages which can be linkified. A standard way to
represent this is desirable beyond manually parsing the ``body`` looking for
"http-like" links. This also allows any text to be linked even if it doesn't
look like a URL.
