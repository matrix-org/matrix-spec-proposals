Module Heading
==============

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
subsections. The section is intended to document the "common shared event
structure" between client and server. Deviations from this shared structure
should be documented in the relevant behaviour section.

example.event.type
~~~~~~~~~~~~~~~~~~
There should be JSON Schema docs for this event. You can insert a template like
so:

{{example_event_type_event}}

Client behaviour
----------------
List any new HTTP endpoints. List the steps the client needs to take to
correctly process this module. Listing what data structures the client should be
storing to aid implementation is recommended. 

Server behaviour
----------------
Does the server need to handle any of the new events in a special way (e.g.
typing timeouts, presence). Advice on how to persist events and/or requests are
recommended to aid implementation.

Security considerations
-----------------------
This includes privacy leaks: for example leaking presence info. How do
misbehaving clients or servers impact this module? This section should always be
included, if only to say "we've thought about it but there isn't anything to do
here".

