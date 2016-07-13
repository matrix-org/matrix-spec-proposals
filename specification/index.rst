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

Matrix Specification
====================

.. Note that this file is specifically unversioned because we don't want to
.. have to add Yet Another version number, and the commentary on what specs we
.. have should hopefully not get complex enough that we need to worry about
.. versioning it.

Matrix defines a set of open APIs for decentralised communication, suitable for
securely publishing, persisting and subscribing to data over a global open
federation of servers with no single point of control.  Uses include Instant Messaging (IM),
Voice over IP (VoIP) signalling, Internet of Things (IoT) communication, and bridging
together existing communication silos - providing the basis of a new open real-time
communication ecosystem.

`Introduction to Matrix <intro.html>`_ provides a full introduction to Matrix and the spec.

Matrix APIs
-----------

The following APIs are documented in this specification:

{{apis}}

`Appendices <appendices.html>`_ with supplemental information not specific to
one of the above APIs are also available.

Specification Versions
----------------------

The specification for each API is versioned in the form ``rX.Y.Z``.
 * A change to ``X`` reflects a breaking change: a client implemented against
   ``r1.0.0`` may need changes to work with a server which supports (only)
   ``r2.0.0``.
 * A change to ``Y`` represents a change which is backwards-compatible for
   existing clients, but not necessarily existing servers: a client implemented
   against ``r1.1.0`` will work without changes against a server which supports
   ``r1.2.0``; but a client which requires ``r1.2.0`` may not work correctly
   with a server which implements only ``r1.1.0``.
 * A change to ``Z`` represents a change which is backwards-compatible on both
   sides. Typically this implies a clarification to the specification, rather
   than a change which must be implemented.
