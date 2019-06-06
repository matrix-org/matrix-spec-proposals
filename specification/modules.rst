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
endpoints. Modules are strictly defined within this specification and
should not be mistaken for experimental extensions or optional features.
A compliant server implementation MUST support all modules and supporting
specification (unless the implementation only targets clients of certain
profiles, in which case only the required modules for those feature profiles
MUST be implemented). A compliant client implementation MUST support all
the required modules and supporting specification for the `Feature Profile <#feature-profiles>`_
it targets.
