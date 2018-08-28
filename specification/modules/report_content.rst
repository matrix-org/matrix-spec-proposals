.. Copyright 2018 Travis Ralston
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

Reporting Content
=================

.. _module:report_content:

Users may encounter content which they find inappropriate and should be able
to report it to the server administrators or room moderators for review. This
module defines a way for users to report content.

Content is reported based upon a negative score, where -100 is "most offensive"
and 0 is "inoffensive".

Client behaviour
----------------
{{report_content_cs_http_api}}

Server behaviour
----------------
Servers are free to handle the reported content however they desire. This may
be a dedicated room to alert server administrators to the reported content or
some other mechanism for notifying the appropriate people.
