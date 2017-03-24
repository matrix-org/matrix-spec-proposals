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

Privacy
-------

Identity is a privacy-sensitive issue. While the identity service exists to
provide identity information, access should be restricted to avoid leaking
potentially sensitive data. In particular, being able to construct large-scale
connections between identities should be avoided. To this end, in general APIs
should allow a 3pid to be mapped to a Matrix user identity, but not in the other
direction (i.e. one should not be able to get all 3pids associated with a Matrix
user ID, or get all 3pids associated with a 3pid).

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

Creating a session
~~~~~~~~~~~~~~~~~~

A client makes a call to::

 POST https://my.id.server:8090/_matrix/identity/api/v1/validate/email/requestToken

 client_secret=monkeys_are_GREAT&
 email=foo@bar.com&
 send_attempt=1

It may also optionally specify next_link. If next_link is specified, when the
validation is completed, the identity service will redirect the user to that
URL.

This will create a new "session" on the identity service, identified by an
``sid``.

The identity service will send an email containing a token. If that token is
presented to the identity service in the future, it indicates that that user was
able to read the email for that email address, and so we validate ownership of
the email address.

We return the ``sid`` generated for this session to the caller, in a JSON object
containing the ``sid`` key.

If a send_attempt is specified, the server will only send an email if the
send_attempt is a number greater than the most recent one which it has seen (or
if it has never seen one), scoped to that email address + client_secret pair.
This is to avoid repeatedly sending the same email in the case of request
retries between the POSTing user and the identity service. The client should
increment this value if they desire a new email (e.g. a reminder) to be sent.

Note that Home Servers offer APIs that proxy this API, adding additional
behaviour on top, for example, ``/register/email/requestToken`` is designed
specifically for use when registering an account and therefore will inform
the user if the email address given is already registered on the server.

Validating ownership of an email
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A user may make either a ``GET`` or a ``POST`` request to
``/_matrix/identity/api/v1/validate/email/submitToken`` with the following
parameters (either as query parameters or URL-encoded POST parameters):
- ``sid`` the sid for the session, generated by the ``requestToken`` call.
- ``client_secret`` the client secret which was supplied to the ``requestToken`` call.
- ``token`` the token generated by the ``requestToken`` call, and emailed to the user.

If these three values are consistent with a set generated by a ``requestToken``
call, ownership of the email address is considered to have been validated. This
does not publish any information publicly, or associate the email address with
any Matrix user ID. Specifically, calls to ``/lookup`` will not show a binding.

Otherwise, an error will be returned.

Checking non-published 3pid ownership
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A client can check whether ownership of a 3pid was validated by making an
HTTP GET request to ``/_matrix/identity/api/v1/3pid/getValidated3pid``, passing
the ``sid`` and ``client_secret`` as query parameters from the ``requestToken``
call.

It will return something of either the form::

 {"medium": "email", "validated_at": 1457622739026, "address": "foo@bar.com"}

or::

 {"errcode": "M_SESSION_NOT_VALIDATED", "error": "This validation session has not yet been completed"}

If the ``sid`` and ``client_secret`` were not recognised, or were not correct,
an error will be returned.

Publishing a validated association
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An association between a session and a Matrix user ID can be published by making
a URL-encoded HTTP POST request to ``/_matrix/identity/api/v1/3pid/bind`` with
the following parameters::

 sid=sid&
 client_secret=monkeys_are_GREAT&
 mxid=@foo:bar.com

If the session is still valid, this will publish an association between the
3pids validated on that session and the passed Matrix user ID. Future calls
to ``/lookup`` for any of the session's 3pids will return this association.

If the 3pid has not yet been validated, the HTTP request will be rejected, and
the association will not be established.

If the ``sid`` and ``client_secret`` were not recognised, or were not correct,
an error will be returned.

Invitation Storage
------------------

An identity service can store pending invitations to a user's 3pid, which will
be retrieved and can be either notified on or look up when the 3pid is
associated with a Matrix user ID.

If one makes a ``POST`` request to ``/_matrix/identity/api/v1/store-invite`` with the following URL-encoded POST parameters:

- ``medium`` (string, required): The literal string ``email``.
- ``address`` (string, required): The email address of the invited user.
- ``room_id`` (string, required): The Matrix room ID to which the user is invited.
- ``sender`` (string, required): The matrix user ID of the inviting user.

An arbitrary number of other parameters may also be specified. These may be used in the email generation described below.

The service will look up whether the 3pid is bound to a Matrix user ID. If it is, the request will be rejected with a 400 status code.

If the medium is something other than the literal string ``email``, the request will be rejected with a 400 status code.

Otherwise, the service will then generate a random string called ``token``, and an ephemeral public key.

The service also generates a ``display_name`` for the inviter, which is a redacted version of ``address`` which does not leak the full contents of the ``address``.

The service records persistently all of the above information.

It also generates an email containing all of this data, sent to the ``address`` parameter, notifying them of the invitation.

The response body is then populated as the JSON-encoded dictionary containing the following fields:
- ``token`` (string): The generated token.
- ``public_keys`` ([string]): A list of [server's long-term public key, generated ephemeral public key].
- ``display_name`` (string): The generated (redacted) display_name.

At a later point, if the owner of that particular 3pid binds it with a Matrix user ID, the identity server will attempt to make an HTTP POST to the Matrix user's homeserver which looks roughly as below::

 POST https://bar.com:8448/_matrix/federation/v1/3pid/onbind
 Content-Type: application/json

 {
   "invites": [{
     "mxid": "@foo:bar.com",
     "token": "abc123",
     "signatures": {
       "my.id.server": {
         "ed25519:0": "def987"
       }
     }
   }],

   "medium": "email",
   "address": "foo@bar.com",
   "mxid": "@foo:bar.com"
 }

Where the signature is produced using a long-term private key.

Also, the generated ephemeral public key will be listed as valid on requests to ``/_matrix/identity/api/v1/pubkey/ephemeral/isvalid``.

Ephemeral invitation signing
----------------------------

To aid clients who may not be able to perform crypto themselves, the identity service offers some crypto functionality to help in accepting invitations.
This is less secure than the client doing it itself, but may be useful where this isn't possible.

The identity service will happily sign invitation details with a request-specified ed25519 private key for you, if you want it to. It takes URL-encoded POST parameters:
- mxid (string, required)
- token (string, required)
- private_key (string, required): The private key, encoded as `Unpadded base64`_.

It will look up ``token`` which was stored in a call to ``store-invite``, and fetch the sender of the invite. It will then respond with JSON which looks something like::

 {
   "mxid": "@foo:bar.com",
   "sender": "@baz:bar.com",
   "signatures" {
     "my.id.server": {
       "ed25519:0": "def987"
     }
   },
   "token": "abc123"
 }

.. _`Unpadded Base64`:  ../appendices.html#unpadded-base64
