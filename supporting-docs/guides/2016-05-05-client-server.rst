---
layout: post
title: Client Server API
categories: guides
---


.. TODO kegan
  Room config (specifically: message history,
  public rooms). 

How to use the client-server API
================================

.. NOTE::
  The git version of this document is ``{% project_version %}``

This guide focuses on how the client-server APIs *provided by the reference 
homeserver* can be used. Since this is specific to a homeserver 
implementation, there may be variations in relation to registering/logging in
which are not covered in extensive detail in this guide.

If you haven't already, get a homeserver up and running on 
``https://localhost:8448``.


Accounts
========
Before you can send and receive messages, you must **register** for an account. 
If you already have an account, you must **login** into it.

.. NOTE::
  `Try out the fiddle`__

  .. __: http://jsfiddle.net/gh/get/jquery/1.8.3/matrix-org/matrix-doc/tree/master/supporting-docs/howtos/jsfiddles/register_login

Registration
------------
The aim of registration is to get a user ID and access token which you will need
when accessing other APIs::

    curl -XPOST -d '{"username":"example", "password":"wordpass", "auth": {"type":"m.login.dummy"}}' "https://localhost:8448/_matrix/client/r0/register"

    {
        "access_token": "QGV4YW1wbGU6bG9jYWxob3N0.AqdSzFmFYrLrTmteXc", 
        "home_server": "localhost", 
        "user_id": "@example:localhost"
    }

NB: If a ``user`` is not specified, one will be randomly generated for you. 
If you do not specify a ``password``, you will be unable to login to the account
if you forget the ``access_token``.

Implementation note: The matrix specification does not enforce how users 
register with a server. It just specifies the URL path and absolute minimum 
keys. The reference homeserver uses a username/password to authenticate user,
but other homeservers may use different methods. This is why you need to
specify the ``type`` of method.

Login
-----
The aim when logging in is to get an access token for your existing user ID::

    curl -XGET "https://localhost:8448/_matrix/client/r0/login"

    {
        "flows": [
            {
                "type": "m.login.password"
            }
        ]
    }

    curl -XPOST -d '{"type":"m.login.password", "user":"example", "password":"wordpass"}' "https://localhost:8448/_matrix/client/r0/login"

    {
        "access_token": "QGV4YW1wbGU6bG9jYWxob3N0.vRDLTgxefmKWQEtgGd", 
        "home_server": "localhost", 
        "user_id": "@example:localhost"
    }
    
Implementation note: Different homeservers may implement different methods for 
logging in to an existing account. In order to check that you know how to login 
to this homeserver, you must perform a ``GET`` first and make sure you 
recognise the login type. If you do not know how to login, you can 
``GET /login/fallback`` which will return a basic webpage which you can use to 
login. The reference homeserver implementation support username/password login,
but other homeservers may support different login methods (e.g. OAuth2).


Communicating
=============

In order to communicate with another user, you must **create a room** with that 
user and **send a message** to that room. 

.. NOTE::
  `Try out the fiddle`__

  .. __: http://jsfiddle.net/gh/get/jquery/1.8.3/matrix-org/matrix-doc/tree/master/supporting-docs/howtos/jsfiddles/create_room_send_msg

Creating a room
---------------
If you want to send a message to someone, you have to be in a room with them. To
create a room::

    curl -XPOST -d '{"room_alias_name":"tutorial"}' "https://localhost:8448/_matrix/client/r0/createRoom?access_token=YOUR_ACCESS_TOKEN"

    {
        "room_alias": "#tutorial:localhost", 
        "room_id": "!asfLdzLnOdGRkdPZWu:localhost"
    }
    
The "room alias" is a human-readable string which can be shared with other users
so they can join a room, rather than the room ID which is a randomly generated
string. You can have multiple room aliases per room.

.. TODO(kegan)
  How to add/remove aliases from an existing room.
    

Sending messages
----------------
You can now send messages to this room::

    curl -XPOST -d '{"msgtype":"m.text", "body":"hello"}' "https://localhost:8448/_matrix/client/r0/rooms/%21asfLdzLnOdGRkdPZWu:localhost/send/m.room.message?access_token=YOUR_ACCESS_TOKEN"
    
    {
        "event_id": "YUwRidLecu"
    }
    
The event ID returned is a unique ID which identifies this message.
    
NB: There are no limitations to the types of messages which can be exchanged.
The only requirement is that ``"msgtype"`` is specified. The Matrix 
specification outlines the following standard types: ``m.text``, ``m.image``,
``m.audio``, ``m.video``, ``m.location``, ``m.emote``. See the specification for
more information on these types.

Users and rooms
===============

Each room can be configured to allow or disallow certain rules. In particular,
these rules may specify if you require an **invitation** from someone already in
the room in order to **join the room**. In addition, you may also be able to 
join a room **via a room alias** if one was set up.

.. NOTE::
  `Try out the fiddle`__

  .. __: http://jsfiddle.net/gh/get/jquery/1.8.3/matrix-org/matrix-doc/tree/master/supporting-docs/howtos/jsfiddles/room_memberships

Inviting a user to a room
-------------------------
You can directly invite a user to a room like so::

    curl -XPOST -d '{"user_id":"@myfriend:localhost"}' "https://localhost:8448/_matrix/client/r0/rooms/%21asfLdzLnOdGRkdPZWu:localhost/invite?access_token=YOUR_ACCESS_TOKEN"
    
This informs ``@myfriend:localhost`` of the room ID 
``!CvcvRuDYDzTOzfKKgh:localhost`` and allows them to join the room.

Joining a room via an invite
----------------------------
If you receive an invite, you can join the room::

    curl -XPOST -d '{}' "https://localhost:8448/_matrix/client/r0/rooms/%21asfLdzLnOdGRkdPZWu:localhost/join?access_token=YOUR_ACCESS_TOKEN"
    
NB: Only the person invited (``@myfriend:localhost``) can change the membership
state to ``"join"``. Repeatedly joining a room does nothing.

Joining a room via an alias
---------------------------
Alternatively, if you know the room alias for this room and the room config 
allows it, you can directly join a room via the alias::

    curl -XPOST -d '{}' "https://localhost:8448/_matrix/client/r0/join/%21asfLdzLnOdGRkdPZWu:localhost?access_token=YOUR_ACCESS_TOKEN"
    
    {
        "room_id": "!CvcvRuDYDzTOzfKKgh:localhost"
    }
    
You will need to use the room ID when sending messages, not the room alias.

NB: If the room is configured to be an invite-only room, you will still require
an invite in order to join the room even though you know the room alias. As a
result, it is more common to see a room alias in relation to a public room, 
which do not require invitations.

Getting events
==============
An event is some interesting piece of data that a client may be interested in. 
It can be a message in a room, a room invite, etc. There are many different ways
of getting events, depending on what the client already knows.

.. NOTE::
  `Try out the fiddle`__

  .. __: http://jsfiddle.net/gh/get/jquery/1.8.3/matrix-org/matrix-doc/tree/master/supporting-docs/howtos/jsfiddles/event_stream

Getting all state
-----------------
If the client doesn't know any information on the rooms the user is 
invited/joined on, they can get all the user's state for all rooms::

    curl -XGET "https://localhost:8448/_matrix/client/r0/sync?access_token=YOUR_ACCESS_TOKEN"
    
    {
        "account_data": {
            "events": [
                {
                    ...
                }
            ]
        },
        "next_batch": "s9_3_0_1_1_1",
        "presence": {
            "events": [
                {
                    "content": {
                        "currently_active": true,
                        "last_active_ago": 19,
                        "presence": "online"
                    },
                    "sender": "@example:localhost",
                    "type": "m.presence"
                }
            ]
        },
        "rooms": {
            "invite": {},
            "join": {
                "!asfLdzLnOdGRkdPZWu:localhost": {
                    "account_data": {
                        "events": []
                    },
                    "ephemeral": {
                        "events": []
                    },
                    "state": {
                        "events": []
                    },
                    "timeline": {
                        "events": [
                            {
                                "content": {
                                    "creator": "@example:localhost"
                                },
                                "event_id": "$14606534990LhqHt:localhost",
                                "origin_server_ts": 1460653499699,
                                "sender": "@example:localhost",
                                "state_key": "",
                                "type": "m.room.create",
                                "unsigned": {
                                    "age": 239192
                                }
                            },
                            {
                                "content": {
                                    "avatar_url": null,
                                    "displayname": null,
                                    "membership": "join"
                                },
                                "event_id": "$14606534991nsZKk:localhost",
                                "membership": "join",
                                "origin_server_ts": 1460653499727,
                                "sender": "@example:localhost",
                                "state_key": "@example:localhost",
                                "type": "m.room.member",
                                "unsigned": {
                                    "age": 239164
                                }
                            },
                            ...
                        ],
                        "limited": false,
                        "prev_batch": "s9_3_0_1_1_1"
                    },
                    "unread_notifications": {}
                }
            },
            "leave": {}
        }
    }

This returns all the room information the user is invited/joined on, as well as
all of the presences relevant for these rooms. This can be a LOT of data. You
may just want the most recent event for each room. This can be achieved by 
applying a filter that asks for a limit of 1 timeline event per room::

    curl --globoff -XGET "https://localhost:8448/_matrix/client/r0/sync?filter={'room':{'timeline':{'limit':1}}}&access_token=YOUR_ACCESS_TOKEN"

    {
        ...
        "rooms": {
            "invite": {},
            "join": {
                "!asfLdzLnOdGRkdPZWu:localhost": {
                    ...
                    "timeline": {
                        "events": [
                            {
                                "content": {
                                    "body": "hello",
                                    "msgtype": "m.text"
                                },
                                "event_id": "$14606535757KCGXo:localhost",
                                "origin_server_ts": 1460653575105,
                                "sender": "@example:localhost",
                                "type": "m.room.message",
                                "unsigned": {
                                    "age": 800348
                                }
                            }
                        ],
                        "limited": true,
                        "prev_batch": "t8-8_7_0_1_1_1"
                    },
                    "unread_notifications": {}
                }
            },
            "leave": {}
        }
    }

(additionally we have to ask ``curl`` not to try to interpret any ``{}``
characters in the URL, which is what the ``--globoff`` option is for)

Getting live state
------------------
In the response to this ``sync`` request the server includes a token that can
be used to obtain updates since this point under the object key ``next_batch``.
To use this token, specify its value as the ``since`` parameter to another
``/sync`` request.::

    curl -XGET "https://localhost:8448/_matrix/client/r0/sync?since=s9_7_0_1_1_1&access_token=YOUR_ACCESS_TOKEN"
    
    {
        "account_data": {
            "events": []
        },
        "next_batch": "s9_9_0_1_1_1",
        "presence": {
            "events": [
                {
                    "content": {
                        "currently_active": true,
                        "last_active_ago": 12,
                        "presence": "online"
                    },
                    "sender": "@example:localhost",
                    "type": "m.presence"
                }
            ]
        },
        "rooms": {
            "invite": {},
            "join": {},
            "leave": {}
        }
    }
    
By default this request will not wait in the server, always returning a value
even if nothing interesting happened. However, by applying the ``timeout``
query parameter, which gives a duration in miliseconds, we can ask the server
to wait for up to that amount of time before it returns. If no interesting
events have happened since then, the response will be relatively empty.::

    curl -XGET "https://localhost:8448/_matrix/client/r0/sync?since=s9_13_0_1_1_1&access_token=YOUR_ACCESS_TOKEN"
    {
        "account_data": {
            "events": []
        },
        "next_batch": "s9_13_0_1_1_1",
        "presence": {
            "events": []
        },
        "rooms": {
            "invite": {},
            "join": {},
            "leave": {}
        }
    }

Example application
-------------------
The following example demonstrates registration and login, live event streaming,
creating and joining rooms, sending messages, getting member lists and getting 
historical messages for a room. This covers most functionality of a messaging
application.

.. NOTE::
  `Try out the fiddle`__

  .. __: http://jsfiddle.net/gh/get/jquery/1.8.3/matrix-org/matrix-doc/tree/master/supporting-docs/howtos/jsfiddles/example_app
