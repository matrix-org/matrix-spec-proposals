# Extensible events in Matrix
## Problem

 1. There is no formal mechanism of extending events with additional structured metadata.
 2. New events tend to reinvent the wheel rather than being able to reuse existing types.
 3. Clients don’t know how to render unknown event types.

This is seriously hindering uptake of new event types in Matrix - whether that’s
richer data types (stickers, location, calendaring, etc) or IOT-style use cases.
It also means we are currently using an underspecified solution for rich
messaging, as there has never been a previous agreed way of a jury rig solution
for rich messaging as we never previously agreed a way of expressing alternate
formats of displaying the same event.

## Solution

We group the keys of an event's contents together into different types. This lets
us address the problem by:

 1. Making it easy to extend events by adding new types into contents alongside existing ones.
 2. Making it easy to reuse existing types by adding new ones alongside existing ones.
 3. Letting clients render unknown event types by falling back to types in the event that they *do* recognise.

Events still have a primary type, which is used when sending them in Matrix.

The names of the keys in contents are now expected to be namespaced, given they
typically refer to types of events.  However, for compatibility, we can keep using
some of the original fields too.

Certain types (e.g. `m.message`, `m.caption`, `m.thumbnail`) which can contain
multiple alternative payloads in different formats express the alternatives as
an ordered list; most preferred first.

We provide short-form types (`m.text` and `m.html`) for the most common scenarios
of an event requiring a plain-text or HTML-formatted representation.

For convenience and compatibility, we keep "body" and "formatted_body" as
shorthand for plain-text and html-formatted fallback for events.

Here are proposals for different types of events:

### m.text and m.html

For compactness for this super-common case, we define a short form which is
equivalent to the longer form `m.message` example below:

```json
{
    "type": "m.message",
    "content": {
        "m.text": "i am a *fish*",
        "m.html": "i am a <b>fish</b>"
    }
}
```

### m.message

m.message describes a simple textual instant message.

```json
{
    "type": "m.message",
    "content": {
        "m.message": [
            {
                "mimetype": "text/html",
                "body": "i am a <b>fish</b>"
            },
            {
                "mimetype": "text/plain",
                "body": "i am a *fish*"
            }
        ],
    }
}
```

### m.file

```json
{
    "type": "m.file",
    "content": {
        "m.text": "foo.dat (12KB)",
        "m.file": {
            "url": "mxc://matrix.org/asdjkhcsd",
            "name": "foo.dat",
            "mimetype": "application/octet-stream",
            "size": 12345
        }
    }
}
```

### m.image

```json
{
    "type": "m.image",
    "content": {
        "m.text": "matrix logo (640x480, 12KB)",
        "m.image": {
            "width": 640,
            "height": 480,
        },
        "m.file": {
            "url": "mxc://matrix.org/asdjkhcsd",
            "mimetype": "image/jpeg",
            "name": "logo.jpg",
            "size": 12345
        },
        "m.caption": [
            {
                "body": "matrix logo"
            }
        ],
        "m.thumbnail": [
            {
                "url": "mxc://matrix.org/thumb",
                "mimetype": "image/jpeg",
                "width": 160,
                "height": 120,
                "size": 123
            }
        ],
    }
}
```

### m.message containing original source text, to allow future edits:

```json
{
    "type": "m.message",
    "content": {
        "m.message": [
            {
                "mimetype": "text/html",
                "body": "I am a <a href=\"http://www.reddwarf.co.uk\">fish</a>",
            },
            {
                "mimetype": "text/markdown",
                "original": true,
                "body": "I am a [fish](http://www.reddwarf.co.uk)",
            },
            {
                "mimetype": "text/plain",
                "body": "I am a fish < http://www.reddwarf.co.uk/ >",
            },
        ]
    }
}
```

### m.message interationalised

```json
{
    "type": "m.message",
    "content": {
        "m.message": [
            {
                "body": "Je suis un poisson",
                "lang": "fr",
            },
            {
                "body": "I am a fish",
                "lang": "en_EN",
            }
        ]
    }
}
```

The french text is preferred and comes next, and a non-i18n aware client would
use it.  A smarter i18n-aware client would realise the user can't speak french
and fall through to the next one.

### m.video

```json
{
    "type": "m.video",
    "content": {
        "m.text": "animated matrix logo (logo.mp4, 1280x720, 1m30s, 23.6MB)",
        "m.video": {
            "width": 1280,
            "height": 720,
            "duration": 90000,
        },
        "m.file": {
            "url": "mxc://matrix.org/v1d30",
            "mimetype": "video/mp4",
            "name": "logo.mp4",
            "size": 23654321
        },
        "m.caption": [
            {
                "body": "animated matrix logo"
            }
        ],
        "m.thumbnail": [
            {
                "url": "mxc://matrix.org/videothumb",
                "mimetype": "video/mp4",
                "animated": true,
                "width": 128,
                "height": 72,
                "size": 12300
            },
            {
                "url": "mxc://matrix.org/thumb",
                "mimetype": "image/jpeg",
                "width": 128,
                "height": 72,
                "size": 123
            }
        ],
    }
}
```

### IOT events (e.g. net.arasphere.temperature)

with text fallback:

```json
{
    "type": "net.arasphere.temperature",
    "content": {
        "m.text": "The temperature is 37C",
        "m.html": "The temperature is <font color='#f00'>37C</font>",
        "net.arasphere.temperature": {
            "temperature": 37.0
        }
    }
}
```

### m.calendar.request

This is a deliberately chunky event designed to show a geotagged calendar request.

(In practice we should probably use the IETF jsCalendar format rather than inventing a
new one here, and to ensure interop with the JMAP folks.
https://tools.ietf.org/html/draft-ietf-calext-jscalendar-11)

```json
{
    "type": "m.calendar.request",
    "content": {
        "m.text": "Invite to Party at Bob's House on Feb 7th, 3pm",
        "m.html": "Invite to Party at <i>Bob's house</i> on Feb 7th, 3pm",
        "m.calendar.request": {
            "version": "2.0",
            "summary": "Party at Bob's house",
            "vEvent": {
                "dtStart": {
                    "date": "20180207T150000",
                    "tzId": "Europe/London"
                },
                "dtEnd": {
                    "date": "20180207T180000",
                    "tzId": "Europe/London"
                }
            }
        },
        "m.file": {
            "uri": "mxc://matrix.org/auiheiuh1eqwd",
            "mimetype": "text/calendar",
            "name": "bobs-party.ics",
            "size": 1246
        },
        "m.location": {
            "uri": "geo:37.786971,-122.399677;u=35",
            "description": "123 Fake Street"
        },
        "m.thumbnail": [
            {
               "uri": "mxc://localhost/JWEIFJgwEIhweiWJE",
               "width": 256,
               "height": 256,
               "mimetype": "image/jpeg",
               "size": 1024000
            }
        ],
    }
}
```

This would be nicer with displayhints support, but still works pretty well.


## Tradeoffs

It's a bit ugly to not know whether a given key will take a string, hash or array.

It's a bit arbitrary as to which fields are allowed lists of fallbacks.

We're skipping over defining rules for which fallback combinations to display
(i.e. "display hints") for now; these can be added in a future MSC if needed.
MSC1225 contains a proposal for this.

## Security considerations

We can't apply ACLs serverside to the types embedded in the event contents.
However, this is inevitable given the existence of E2E, so we have no choice but
for clients to apply ACLs clientside (e.g. refuse to render an m.image contents
on an event if the sender doesn't have enough PL to send an m.image event).

## Availability

Given the disruption of migrating clients & bridges to the new event shape, this
should probably land after S2S r0.

## Migration

Currently visible events are `m.room.message` with a `msgtype` to distinguish
between `m.text`, `m.image`, `m.file`, etc.

...?

