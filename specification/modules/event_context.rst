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

Event Context
=============

.. _module:event-context:

This API returns a number of events that happened just before and after the
specified event. This allows clients to get the context surrounding an event.

Client behaviour
----------------

There is a single HTTP API for retrieving event context, documented below.

{{event_context_cs_http_api}}

Security considerations
-----------------------

The server must only return results that the user has permission to see.
