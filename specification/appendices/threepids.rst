.. Copyright 2017 Kamax.io
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

3PID Types
----------
Third Party Identifiers (3PIDs) represent identifiers on other namespaces that
might be associated with a particular person. They comprise a tuple of ``medium``
which is a string that identifies the namespace in which the identifier exists,
and an ``address``: a string representing the identifier in that namespace. This
must be a canonical form of the identifier, *i.e.* if multiple strings could
represent the same identifier, only one of these strings must be used in a 3PID
address, in a well-defined manner.

For example, for e-mail, the ``medium`` is 'email' and the ``address`` would be the
email address, *e.g.* the string ``bob@example.com``. Since domain resolution is
case-insensitive, the email address ``bob@Example.com`` is also has the 3PID address
of ``bob@example.com`` (without the capital 'e') rather than ``bob@Example.com``.

The namespaces defined by this specification are listed below. More namespaces
may be defined in future versions of this specification.

E-Mail
~~~~~~
Medium: ``email``

Represents E-Mail addresses. The ``address`` is the raw email address in
``user@domain`` form with the domain in lowercase. It must not contain other text
such as real name, angle brackets or a mailto: prefix.

PSTN Phone numbers
~~~~~~~~~~~~~~~~~~
Medium: ``msisdn``

Represents telephone numbers on the public switched telephone network.  The
``address`` is the telephone number represented as a MSISDN (Mobile Station
International Subscriber Directory Number) as defined by the E.164 numbering
plan. Note that MSISDNs do not include a leading '+'.
