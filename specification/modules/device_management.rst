.. Copyright 2016 OpenMarket Ltd
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

Device Management
=================

.. _module:device-management:

This module provides a means for a user to manage their `devices`_.

Client behaviour
----------------
Clients that implement this module should offer the user a list of registered
devices, as well as the means to update their display names. Clients should
also allow users to delete disused devices.

{{device_management_cs_http_api}}

Security considerations
-----------------------

Deleting devices has security implications: it invalidates the access_token
assigned to the device, so an attacker could use it to log out the real user
(and do it repeatedly every time the real user tries to log in to block the
attacker). Servers should require additional authentication beyond the access
token when deleting devices (for example, requiring that the user resubmit
their password).

The display names of devices are publicly visible. Clients should consider
advising the user of this.
