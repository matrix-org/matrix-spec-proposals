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
TODO: link.

In the event of key compromise, the identity service may revoke any of its keys.
An HTTP API is offered to get public keys, and check whether a particular key is
valid.

The identity server may also keep track of some short-term public-private
keypairs, which may have different usage and lifetime characteristics than the
service's long-term keys.

{{pubkey_is_http_api}}
