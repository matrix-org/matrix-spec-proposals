.. Copyright 2016 OpenMarket Ltd
.. Copyright 2019 The Matrix.org Foundation C.I.C.
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

Modules
=======

Modules are parts of the Client-Server API which are not universal to all
endpoints and are accessible to all clients. Modules are strictly defined
within this specification and should not be mistaken for XEP or equivalent
extensions from other protocols - in order for an implementation to be
compliant with the Client-Server specification it MUST support all modules
and supporting specification. The exception being clients, which are governed
by `Feature Profiles <#feature-profiles>`_.
