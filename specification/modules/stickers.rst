.. Copyright 2018 New Vector Ltd.
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

Sticker Messages
================

.. _module:stickers:

This module allows users to send sticker messages in to rooms or direct
messaging sessions.

Sticker messages are specialised image messages that are displayed without
controls (e.g. no "download" link, or light-box view on click, as would be
displayed for for `m.image`_ events).

Sticker messages are intended to provide simple "reaction" events in the message
timeline. The matrix client should provide some mechanism to display the sticker
"body" e.g. as a tooltip on hover, or in a modal when the sticker image is
clicked.

Events
------
Sticker events are received as a single ``m.sticker`` event in the
``timeline`` section of a room, in a ``/sync``.

{{m_sticker_event}}

Integration manager referral URL
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

In order to aid widget or asset sharing and discovery, sticker events can
specify an ``integration_manager_url`` property under ``StickerpackInfo``.

This URL is intended to link the user to an appropriate page within the relevant
Integration Manager to enable them to add / purchase the associated integration
or integration asset (e.g. a stickerpicker widget, or stickerpack).

The ``integration manager referral URL`` should have the following format::

  https://<hostname>/<integration manager base path>/integration/<integration_type>/<asset_id>?utm_source=<utm_source>&utm_medium=<utm_medium>&utm_campaign=<utm_campaign>&promotional_code=<promotional_code>

Where:

* The ``hostname`` and ``integration manager base path`` should point to the
  Integration Manager that the stickerpack or associated asset can be purchased
  from.
* ``integration_type`` is the type name of the widget/integration (e.g.
  'stickerpicker'),
* Optionally ``asset_id`` can be set to a unique identifier for an asset to
  be used with the specified widget. E.g. This could be set to 'rabbits123'
  to direct the user to a page to purchase a specific stickerpack (of rabbit
  stickers).
* All query parameters are optional. They may be used for referral tracking and
  promotional codes (depending on the terms of service of the integration
  manager).
  For example:

  - ``utm_source`` - The referral source / website (E.g. 'matrix.org')
  - ``utm_medium`` - The referral medium (E.g. 'email')
  - ``utm_campaign`` - The referral campaign (E.g. 'january_newsletter')
  - ``promotional_code`` - A  promotional code to be applied to the purchase

Client behaviour
----------------

Clients supporting this message type should display the image content from the
event URL directly in the timeline.

A thumbnail image should be provided in the ``info`` object. This is
largely intended as a fallback for clients that do not fully support the
``m.sticker`` event type. In most cases it is fine to set the thumbnail URL to the
same URL as the main event content.

It is recommended that sticker image content should be 512x512 pixels in size
or smaller. The dimensions of the image file should be twice the intended
display size specified in the ``info`` object in order to assist
rendering sharp images on higher DPI screens.
