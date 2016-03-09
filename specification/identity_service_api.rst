Identity Service API
====================

The Matrix client-server and server-server APIs are largely expressed in Matrix
user identifiers. From time to time, it is useful to refer to users by other
("third-party") identifiers, or "3pid"s, e.g. their email address or phone
number. This identity service specification describes how mappings between
third-party identifiers and Matrix user identifiers can be established,
verified, and used.

.. contents:: Table of Contents
.. sectnum::

General principles
------------------

The purpose of an identity service is to verify, store, and answer questions
about the identities of users. In particular, it stores associations of the form
"identifier X represents the same user as identifier Y", where identities may
exist on different systems (such as email addresses, phone numbers,
Matrix user IDs, etc).

The identity service has some private-public keypairs. When asked about an
association, it will sign details of the association with its private key.
Clients may verify the assertions about associations by verifying the signature
with the public key of the identity service.

In general, identity services are treated as reliable oracles. They do not
necessarily provide evidence that they have verified associations, but claim to
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

Also, the generated ephemeral public key will be listed as valid on requests to ``/_matrix/identity/v1/api/pubkey/ephemeral/isvalid``.
