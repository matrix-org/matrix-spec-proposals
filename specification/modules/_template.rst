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

Module Heading
==============

.. NOTE: Prefer to identify-modules-with-dashes despite historical examples.
.. _module:short-name:

A short summary of the module. What features does this module provide? An anchor
should be specified at the top of the module using the format ``module:name``.

Complicated modules may wish to have architecture diagrams or event flows
(e.g. VoIP call flows) here. Custom subsections can be included but they should
be used *sparingly* to reduce the risk of putting client or server behaviour
information in these custom sections.

Events
------
List the new event types introduced by this module, if any. If there are no
new events, this section can be omitted. Event types should be done as
subsections. This section is intended to document the "common shared event
structure" between client and server. Deviations from this shared structure
should be documented in the relevant behaviour section.

``m.example.event.type``
~~~~~~~~~~~~~~~~~~~~~~~~
There should be JSON Schema docs for this event. Once there is JSON schema,
there will be a template variable with dots in the event type replaced with
underscores and the suffix ``_event``. You can insert a template like so:

{{m_example_event_type_event}}

Client behaviour
----------------
List any new HTTP endpoints. These endpoints should be documented using Swagger.
Once there is Swagger, there will be a template variable based on the name of
the YAML file with the suffix ``_cs_http_api``. You can insert a template for
swagger docs like so:

{{name-of-yaml-file-without-file-ext_cs_http_api}}

List the steps the client needs to take to
correctly process this module. List what data structures the client should be
storing in order to aid implementation.

Server behaviour
----------------
Does the server need to handle any of the new events in a special way (e.g.
typing timeouts, presence). Advice on how to persist events and/or requests are
recommended to aid implementation. Federation-specific logic should be included
here.

Security considerations
-----------------------
This includes privacy leaks: for example leaking presence info. How do
misbehaving clients or servers impact this module? This section should always be
included, if only to say "we've thought about it but there isn't anything to do
here".
