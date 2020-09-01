.. Copyright 2020 The Matrix.org Foundation C.I.C.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Widgets
=======

{{unstable_warning_block_WIDGETS_RELEASE_LABEL}}

Widgets are client-side embedded applications which can communicate with Matrix clients. Widgets
are often used to present information to users and allow them to more interactively collaborate.

Due to platform constraints, unreasonable implementation effort, and client-specific design choices,
widgets are optional in Matrix. Clients are encouraged to support widgets if possible and reasonable,
though degraded behaviour, such as "open in browser" links, is considered acceptable by this
specification.

.. contents:: Table of Contents
.. sectnum::

Changelog
---------

.. topic:: Version: %WIDGETS_RELEASE_LABEL%
{{widgets_changelog}}

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

For the full historical changelog, see
https://github.com/matrix-org/matrix-doc/blob/master/changelogs/widgets.rst

Other versions of this specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following other versions are also available, in reverse chronological order:

- `HEAD <https://matrix.org/docs/spec/widgets/unstable.html>`_: Includes all changes since the latest versioned release.

API Standards
~~~~~~~~~~~~~

Throughout this specification, a "client" is referred to as something which is rendering/supporting
("hosting") widgets. Widgets are unique in that they can be considered a client when referred to in
a typical network setting, though this specification ensures that a widget is always referred to as
a "widget" and the term "client" is solely reserved for the widget's host application. Note that
widgets can be hosts to widgets - deciphering which role is which in this context is left as an
exercise for the reader.

The mandatory baseline for a widget is a typical website with the optional communication protocol
described here. When communicating with a Matrix client, the mandatory baseline is the `JavaScript
postMessage API <https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage>`_ using the
protocol described by this specification. In the future more accessible transports for clients will
be considered as optional extensions, such as using operating system-specific hooks.

All objects exchanged over the Widget (``postMessage``) API are JSON objects.

In essence, widgets are typically iframes or the platform equivilant to a website which are accessible
in the client.

Widget Kinds
------------

Widgets currently can exist in the following places:

* Within rooms, accessible by members/observers of the room.
* For a particular user, accessible only by that user.

{{definition_widgets_shared_props}}

Room Widgets
~~~~~~~~~~~~

Room widgets are defined by state events in the room, and are as such accessible to anyone who is
able to see the state of the room. Widgets can individually apply additional access restrictions
such as preventing non-joined members of the room from accessing the widget's functionality.

Clients MUST NOT show room widgets to the user unless the user is viewing that room or unless the
widget has set an appropriate always-on-screen request through the Widget API.

The ``state_key`` for a room widget MUST match the widget's ``id``. Due to this association, new
widgets in the room must use a unique ``state_key`` (and therefore ``id``). Widgets can be
updated by sending a new state event for the widget's ``state_key``.

Invalid room widgets MUST NOT be shown to users. This is also how widgets are removed from a room:
send a new state event for the same widget ID with at least the ``url`` and/or ``type`` missing
from the event content. Once Matrix allows for state events to be properly deleted then doing so
to the widget state event will be just as valid to remove it from the room.

.. WARNING::
    Do not store sensitive information such as tokens, secrets, or passwords
    in the widget data as it can be viewed by anyone who can see the room state.

{{m_widget_event}}

Account Widgets
~~~~~~~~~~~~~~~

Account widgets are defined in the user's account data, and are as such only visible to them.
Widgets can individually apply additional access restrictions as needed. Account widgets are
not linked to any particular room.

Account widgets are represented under the ``m.widgets`` account data event as a map of widget ID
to definition. As such, the widget's ``id`` must be unique within this object's properties. The
definition for an account widget is nearly equivilant to a room widget's state event representation,
using the ``type``, ``state_key``, ``sender``, and ``content`` fields of the state event.

Account widgets can be added by adding a new key to the ``m.widgets`` account data, edited by
modifying the appropriate ``AccountWidget`` definition, or deleted by simply removing the appropriate
property from the ``m.widgets`` acount data.

.. WARNING::
    Do not store sensitive information such as tokens, secrets, or passwords
    in the widget data as it is not secure or encrypted.

{{m_widgets_event}}


Rendering
---------

Widgets SHOULD be rendered using an iframe or platform equivilant. Clients can use platform-specific
rendering for widgets if they are confident in being able to do so, such as in the case of most
video conference widgets.

Clients SHOULD ask for permission to load a widget from the user prior to presenting the widget. If
the user was the last ``sender`` of a widget (not the ``creatorUserId``), the prompt can be skipped.
This prompt is strongly encouraged to ensure that users do not inadvertently send their information
to a third party.

URL Templating
~~~~~~~~~~~~~~

The widget's URL is a template of what the client should render and should never be parsed by the
client to determine what the parameters are. All widgets make use of the ``data`` object to store
configuration-like values, which is also where clients should inspect for values needed to render
any UI.

Variable names for the template are the keys of the ``data`` object, with the values being the same
values of the object. Variables are included unencoded in the URL for population by the client, which
MUST use appropriate escaping to ensure the URL will be as valid as possible.

For example, given a ``data`` object like this::

  {
    "hello": "world",
    "answer": 42
  }

and a ``url`` of ``https://example.com?var1=$hello&answer=$answer`` the client MUST come up with
a URL of ``https://example.com?var1=world&answer=42`` to render. Complex types, such as objects and
arrays, for variable values do not have defined behaviour - widget creators are encouraged to stick
to "simple" types like numbers, strings, and booleans. Template variables can appear anywhere in the
URL.

Nested variables are not supported, and as such clients should be careful in their templating
approach. For example, if ``hello`` in the above example ``data`` was set to ``$answer``, the literal
value ``$answer`` would be included in the widget URL rather than ``42``.

As mentioned, clients must also encode values on behalf of the widget creator to maintain a valid
URL as much as possible. For example, ``test:value`` could become ``test%3Avalue`` when used as a
template variable value.

A few default variables, which MUST take priority over the same names in ``data``, are:

* ``matrix_user_id`` - The current user's ID.
* ``matrix_room_id`` - The room ID the user is currently viewing, or an empty string if none applicable.
* ``matrix_display_name`` - The current user's display name, or user ID if not set.
* ``matrix_avatar_url`` - The current user's avatar URL as reported in their profile, or and empty
  string if not present. This shouldn't be the ``mxc://`` form of the user's avatar, but instead the
  full HTTP URL to the ``/media/download`` endpoint for their avatar from the Client-Server API.

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~~

Clients SHOULD check to ensure that widgets are valid URLs *after* templating but *before* rendering
or asking for permission to load. Invalid URLs from the client's perspective should not be shown to
the user and can be treated as though no ``url`` was present (i.e.: a deleted/invalid widget).

Clients SHOULD limit which URL schemes are able to be rendered to ensure that they are not rendering
potentially dangerous files. Most widgets will have schemes of ``http`` or ``https``.

Clients SHOULD apply a sandbox to their iframe or platform equivilant to ensure the widget cannot
get access to the data stored by the client, such as access tokens or cryptographic keys. More
information on origin restrictions is in the Widget API's security considerations section.

Widget Types
------------

A widget's ``type`` can be one of the following specified types or a custom type which preferably
uses the Java package naming convention as a namespace. Types prefixed with the ``m.`` namespace
are reserved by this specification.

Besides the ``type`` itself, widget types influence the widget's ``data`` by requiring specified
keys to exist. It is expected that the widget will use these keys as variables for their URL, though
this specification does not require such behaviour. Clients SHOULD treat widgets without the
required ``data`` properties for the types specified here as invalid widgets, thus not rendering
them.

Clients MUST treat widgets of unknown types as ``m.custom``, unless it is impossible for the client
to render the widget kind in that way. For example, custom widgets at the per-user rather than
per-room level might not be possible and thus can be treated as invalid (ignored).

Clients are not required to support all of these widget types (with the implied exception of
``m.custom``) as they can all be safely represented as ``m.custom`` widgets.

Jitsi Meet Conferences
~~~~~~~~~~~~~~~~~~~~~~

`Jitsi Meet <https://jitsi.org/jitsi-meet/>`_ conferences can be held on a per-room basis with
a widget ``type`` of ``m.jitsi`` and ``data`` matching ``JitsiWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_jitsi_data}}

TradingView
~~~~~~~~~~~

`TradingView <https://www.tradingview.com/>`_ widgets can be addded on a per-room basis with
a widget ``type`` of ``m.tradingview`` and ``data`` matching ``TradingViewWidgetData``.

This widget type is meant to be used with TradingView's
`Advanced Real-Time Chart Widget <https://www.tradingview.com/widget/advanced-chart/>`_.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_tradingview_data}}

Spotify
~~~~~~~

`Spotify Widgets <https://developer.spotify.com/documentation/widgets/>`_ can be added on a
per-room basis with a widget ``type`` of ``m.spotify`` and ``data`` matching ``SpotifyWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_spotify_data}}

Videos
~~~~~~

Videos from video streaming sites can be added on a per-room basis with a widget ``type`` of
``m.video`` and ``data`` matching ``VideoWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_video_data}}

Google Docs
~~~~~~~~~~~

Documents from Google Docs, Sheets, and Slides can be added as widgets on a per-room basis with a
widget ``type`` of ``m.googledoc`` and ``data`` matching ``GoogleDocsWidgetData``.

.. Note::
   Documents typically need to be publicly accessible without authentication to be embedded. Most
   documents that would be shared by widgets are not publicly accessible and thus generally will
   refuse to embed properly.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_googledocs_data}}

Google Calendar
~~~~~~~~~~~~~~~

Calendars from Google Calendar can be added as widgets on a per-room basis with a widget ``type``
of ``m.googlecalendar`` and ``data`` matching ``GoogleCalendarWidgetData``.

.. Note::
   Calendars typically need to be publicly accessible without authentication to be embedded. Most
   calendars that would be shared by widgets are not publicly accessible and thus generally will
   refuse to embed properly.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_googlecalendar_data}}

Etherpad
~~~~~~~~

`Etherpad <https://etherpad.org/>`_ editors can be added on a per-room basis with a widget ``type``
of ``m.etherpad`` and ``data`` matching ``EtherpadWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_etherpad_data}}

Grafana
~~~~~~~

`Embedded Grafana Panels <https://grafana.com/docs/grafana/latest/reference/share_panel/>`_ can
be added on a per-room basis with a widget ``type`` of ``m.grafana`` and ``data`` matching
``GrafanaWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_grafana_data}}

Stickerpicker
~~~~~~~~~~~~~

Stickerpickers are user widgets which allow the user to send ``m.sticker`` events to the current
room using the Widget API described by this specification. They have a widget ``type`` of
``m.stickerpicker`` and ``data`` which matches ``StickerpickerWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of user widgets.

{{definition_widgets_stickerpicker_data}}

Custom Widgets
~~~~~~~~~~~~~~

Custom widgets are the most basic form of widget possible, and represent teh default behaviour
for all widgets. They have an explicit widget ``type`` of ``m.custom``, though any
unknown/unsupported widget type for the client will be treated as a custom widget. They have
``data`` matching ``CustomWidgetData``.

{{definition_widgets_custom_data}}
