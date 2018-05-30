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

In order to aid widget and asset sharing and discovery, sticker events can
specify an ``integration_manager_url`` property under ``StickerpackInfo``.

This URL should be rendered by matrix clients as a button or similar control.
This control should initiate opening an appropriate page within the relevant
Integration Manager to enable addition (and purchase where relevant) of an
integration or integration asset (e.g. a stickerpicker widget, or stickerpack).

The ``integration_manager_url`` should have the following format::

  https://<hostname>/<integration manager base path>/integration/<integration_type>/<asset_id>

Where:

* The ``hostname`` and ``integration manager base path`` should point to the
  Integration Manager that the stickerpack or associated asset can be purchased
  from.
* ``integration_type`` is the type of the widget or integration (e.g.
  'm.stickerpicker').
* Optionally, ``asset_id`` can be set to a unique identifier for an asset to
  be used with the specified widget. For example, this could be set to *'rabbits123'*
  to direct the user to a page to add (and optionally purchase) a specific
  stickerpack (of rabbit stickers).

The ``integration_manager_url`` should be specified by the
stickerpicker widget when sending a sticker event to the matrix client.

Query parameters may optionally be added to the URL by Matrix clients in
order to aid referral tracking and promotional codes (depending on the terms of
service of the integration manager).

The following parameters should be supported by integration managers and
added to the URL by Matrix clients, where available:

* ``utm_source`` - The referral source (E.g. 'matrix.org'). This should be the
  domain name of the website or application hosting or sending the
  ``integration_manager_url`` link.
* ``utm_medium`` - The referral medium. Should be one of *'matrix_client'*,
  *'email'*, *'sms'*, *'website'* or *'other'*.
* ``utm_campaign`` - The referral campaign. This can be any string value (e.g.
  *'january_newsletter'*). However, for Matrix clients this should be
  set to the client name (e.g. *'riot-web'*).
* ``promotional_code`` - An optional promotional code to be applied to the
  purchase. For example, *'discount20'* could be passed to denote that a 20%
  promotional discount should be applied to a product purchase. The integration
  manager should perform validation that the code is valid and applicable to the
  specified product.


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
