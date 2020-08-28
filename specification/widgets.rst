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

URL Templating
--------------

TODO
