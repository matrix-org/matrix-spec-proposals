.. Copyright 2016 OpenMarket Ltd
.. Copyright 2017 Kamax.io
.. Copyright 2017 New Vector Ltd
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

Identity Service API
====================

The Matrix client-server and server-server APIs are largely expressed in Matrix
user identifiers. From time to time, it is useful to refer to users by other
("third-party") identifiers, or "3pid"s, e.g. their email address or phone
number. This identity service specification describes how mappings between
third-party identifiers and Matrix user identifiers can be established,
validated, and used. This description technically may apply to any 3pid, but in
practice has only been applied specifically to email addresses.

.. contents:: Table of Contents
.. sectnum::

Specification version
---------------------

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

General principles
------------------

The purpose of an identity service is to validate, store, and answer questions
about the identities of users. In particular, it stores associations of the form
"identifier X represents the same user as identifier Y", where identities may
exist on different systems (such as email addresses, phone numbers,
Matrix user IDs, etc).

The identity service has some private-public keypairs. When asked about an
association, it will sign details of the association with its private key.
Clients may validate the assertions about associations by verifying the signature
with the public key of the identity service.

In general, identity services are treated as reliable oracles. They do not
necessarily provide evidence that they have validated associations, but claim to
have done so. Establishing the trustworthiness of an individual identity service
is left as an exercise for the client.

3PID types are described in `3PID Types`_ Appendix.

Privacy
-------

Identity is a privacy-sensitive issue. While the identity service exists to
provide identity information, access should be restricted to avoid leaking
potentially sensitive data. In particular, being able to construct large-scale
connections between identities should be avoided. To this end, in general APIs
should allow a 3pid to be mapped to a Matrix user identity, but not in the other
direction (i.e. one should not be able to get all 3pids associated with a Matrix
user ID, or get all 3pids associated with a 3pid).

Status check
------------

{{ping_is_http_api}}

Key management
--------------

An identity service has some long-term public-private keypairs. These are named
in a scheme ``algorithm:identifier``, e.g. ``ed25519:0``. When signing an
association, the Matrix standard JSON signing format is used, as specified in
the server-server API specification under the heading "Signing Events".

In the event of key compromise, the identity service may revoke any of its keys.
An HTTP API is offered to get public keys, and check whether a particular key is
valid.

The identity server may also keep track of some short-term public-private
keypairs, which may have different usage and lifetime characteristics than the
service's long-term keys.

{{pubkey_is_http_api}}

Association Lookup
------------------

{{lookup_is_http_api}}

Establishing Associations
-------------------------

The flow for creating an association is session-based.

Within a session, one may prove that one has ownership of a 3pid.
Once this has been established, the user can form an association between that
3pid and a Matrix user ID. Note that this association is only proved one way;
a user can associate *any* Matrix user ID with a validated 3pid,
i.e. I can claim that any email address I own is associated with
@billg:microsoft.com.

Sessions are time-limited; a session is considered to have been modified when
it was created, and then when a validation is performed within it. A session can
only be checked for validation, and validation can only be performed within a
session, within a 24 hour period since its most recent modification. Any
attempts to perform these actions after the expiry will be rejected, and a new
session should be created and used instead.

Email associations
~~~~~~~~~~~~~~~~~~

{{email_associations_is_http_api}}

Phone number associations
~~~~~~~~~~~~~~~~~~~~~~~~~

{{phone_associations_is_http_api}}

General
~~~~~~~

{{associations_is_http_api}}

Invitation Storage
------------------

An identity service can store pending invitations to a user's 3pid, which will
be retrieved and can be either notified on or look up when the 3pid is
associated with a Matrix user ID.

At a later point, if the owner of that particular 3pid binds it with a Matrix user ID, the identity server will attempt to make an HTTP POST to the Matrix user's homeserver which looks roughly as below::

 POST https://bar.com:8448/_matrix/federation/v1/3pid/onbind
 Content-Type: application/json

 {
  "medium": "email",
  "address": "foo@bar.baz",
  "mxid": "@alice:example.tld",
  "invites": [
    {
      "medium": "email",
      "address": "foo@bar.baz",
      "mxid": "@alice:example.tld",
      "room_id": "!something:example.tld",
      "sender": "@bob:example.tld",
      "signed": {
        "mxid": "@alice:example.tld",
        "signatures": {
          "vector.im": {
            "ed25519:0": "somesignature"
          }
        },
        "token": "sometoken"
      }
    }
  ]
 }

Where the signature is produced using a long-term private key.

{{store_invite_is_http_api}}

Ephemeral invitation signing
----------------------------

To aid clients who may not be able to perform crypto themselves, the identity service offers some crypto functionality to help in accepting invitations.
This is less secure than the client doing it itself, but may be useful where this isn't possible.

{{invitation_signing_is_http_api}}

.. _`Unpadded Base64`:  ../appendices.html#unpadded-base64
.. _`3PID Types`:  ../appendices.html#pid-types
