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

OpenID
======

.. _module:openid:

This module allows users to verify their identity with a third party service. The
third party service does need to be matrix-aware in that it will need to know to
resolve matrix homeservers to exchange the user's token for identity information.

{{openid_cs_http_api}}
