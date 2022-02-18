---
title: "Identity Service API"
weight: 40
type: docs
---

The Matrix client-server and server-server APIs are largely expressed in
Matrix user identifiers. From time to time, it is useful to refer to
users by other ("third-party") identifiers, or "3PID"s, e.g. their email
address or phone number. This Identity Service Specification describes
how mappings between third-party identifiers and Matrix user identifiers
can be established, validated, and used. This description technically
may apply to any 3PID, but in practice has only been applied
specifically to email addresses and phone numbers.

## General principles

The purpose of an identity server is to validate, store, and answer
questions about the identities of users. In particular, it stores
associations of the form "identifier X represents the same user as
identifier Y", where identities may exist on different systems (such as
email addresses, phone numbers, Matrix user IDs, etc).

The identity server has some private-public keypairs. When asked about
an association, it will sign details of the association with its private
key. Clients may validate the assertions about associations by verifying
the signature with the public key of the identity server.

In general, identity servers are treated as reliable oracles. They do
not necessarily provide evidence that they have validated associations,
but claim to have done so. Establishing the trustworthiness of an
individual identity server is left as an exercise for the client.

3PID types are described in [3PID Types](/appendices#pid-types)
Appendix.

## API standards

The mandatory baseline for identity server communication in Matrix is
exchanging JSON objects over HTTP APIs. HTTPS is required for
communication, and all API calls use a Content-Type of
`application/json`. In addition, strings MUST be encoded as UTF-8.

Any errors which occur at the Matrix API level MUST return a "standard
error response". This is a JSON object which looks like:

```json
{
  "errcode": "<error code>",
  "error": "<error message>"
}
```

The `error` string will be a human-readable error message, usually a
sentence explaining what went wrong. The `errcode` string will be a
unique string which can be used to handle an error message e.g.
`M_FORBIDDEN`. There may be additional keys depending on the error, but
the keys `error` and `errcode` MUST always be present.

Some standard error codes are below:

`M_NOT_FOUND`
The resource requested could not be located.

`M_MISSING_PARAMS`
The request was missing one or more parameters.

`M_INVALID_PARAM`
The request contained one or more invalid parameters.

`M_SESSION_NOT_VALIDATED`
The session has not been validated.

`M_NO_VALID_SESSION`
A session could not be located for the given parameters.

`M_SESSION_EXPIRED`
The session has expired and must be renewed.

`M_INVALID_EMAIL`
The email address provided was not valid.

`M_EMAIL_SEND_ERROR`
There was an error sending an email. Typically seen when attempting to
verify ownership of a given email address.

`M_INVALID_ADDRESS`
The provided third party address was not valid.

`M_SEND_ERROR`
There was an error sending a notification. Typically seen when
attempting to verify ownership of a given third party address.

`M_UNRECOGNIZED`
The request contained an unrecognised value, such as an unknown token or
medium.

`M_THREEPID_IN_USE`
The third party identifier is already in use by another user. Typically
this error will have an additional `mxid` property to indicate who owns
the third party identifier.

`M_UNKNOWN`
An unknown error has occurred.

{{% http-api spec="identity" api="versions" %}}

## Privacy

Identity is a privacy-sensitive issue. While the identity server exists
to provide identity information, access should be restricted to avoid
leaking potentially sensitive data. In particular, being able to
construct large-scale connections between identities should be avoided.
To this end, in general APIs should allow a 3PID to be mapped to a
Matrix user identity, but not in the other direction (i.e. one should
not be able to get all 3PIDs associated with a Matrix user ID, or get
all 3PIDs associated with a 3PID).

## Web browser clients

It is realistic to expect that some clients will be written to be run
within a web browser or similar environment. In these cases, the
identity server should respond to pre-flight requests and supply
Cross-Origin Resource Sharing (CORS) headers on all requests.

When a client approaches the server with a pre-flight (OPTIONS) request,
the server should respond with the CORS headers for that route. The
recommended CORS headers to be returned by servers on all requests are:

    Access-Control-Allow-Origin: *
    Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
    Access-Control-Allow-Headers: Origin, X-Requested-With, Content-Type, Accept, Authorization

## Authentication

Most endpoints in the Identity Service API require authentication
in order to ensure that the requesting user has accepted all relevant
policies and is otherwise permitted to make the request.

Identity Servers use a scheme similar to the Client-Server API's concept
of access tokens to authenticate users. The access tokens provided by an
Identity Server cannot be used to authenticate Client-Server API
requests.

An access token is provided to an endpoint in one of two ways:

1.  Via a query string parameter, `access_token=TheTokenHere`.
2.  Via a request header, `Authorization: Bearer TheTokenHere`.

Clients are encouraged to the use the `Authorization` header where
possible to prevent the access token being leaked in access/HTTP logs.
The query string should only be used in cases where the `Authorization`
header is inaccessible for the client.

When credentials are required but missing or invalid, the HTTP call will
return with a status of 401 and the error code `M_UNAUTHORIZED`.

{{% http-api spec="identity" api="v2_auth" %}}

## Terms of service

Identity Servers are encouraged to have terms of service (or similar
policies) to ensure that users have agreed to their data being processed
by the server. To facilitate this, an identity server can respond to
almost any authenticated API endpoint with an HTTP 403 and the error
code `M_TERMS_NOT_SIGNED`. The error code is used to indicate that the
user must accept new terms of service before being able to continue.

All endpoints which support authentication can return the
`M_TERMS_NOT_SIGNED` error. When clients receive the error, they are
expected to make a call to `GET /terms` to find out what terms the
server offers. The client compares this to the `m.accepted_terms`
account data for the user (described later) and presents the user with
option to accept the still-missing terms of service. After the user has
made their selection, if applicable, the client sends a request to
`POST /terms` to indicate the user's acceptance. The server cannot
expect that the client will send acceptance for all pending terms, and
the client should not expect that the server will not respond with
another `M_TERMS_NOT_SIGNED` on their next request. The terms the user
has just accepted are appended to `m.accepted_terms`.

{{% event event="m.accepted_terms" %}}

{{% http-api spec="identity" api="v2_terms" %}}

## Status check

{{% http-api spec="identity" api="v2_ping" %}}

## Key management

An identity server has some long-term public-private keypairs. These are
named in a scheme `algorithm:identifier`, e.g. `ed25519:0`. When signing
an association, the standard [Signing
JSON](/appendices#signing-json) algorithm applies.

The identity server may also keep track of some short-term
public-private keypairs, which may have different usage and lifetime
characteristics than the service's long-term keys.

{{% http-api spec="identity" api="v2_pubkey" %}}

## Association lookup

{{% http-api spec="identity" api="v2_lookup" %}}

### Client behaviour

Prior to performing a lookup clients SHOULD make a request to the
`/hash_details` endpoint to determine what algorithms the server
supports (described in more detail below). The client then uses this
information to form a `/lookup` request and receive known bindings from
the server.

Clients MUST support at least the `sha256` algorithm.

### Server behaviour

Servers, upon receipt of a `/lookup` request, will compare the query
against known bindings it has, hashing the identifiers it knows about as
needed to verify exact matches to the request.

Servers MUST support at least the `sha256` algorithm.

### Algorithms

Some algorithms are defined as part of the specification, however other
formats can be negotiated between the client and server using
`/hash_details`.

#### `sha256`

This algorithm MUST be supported by clients and servers at a minimum. It
is additionally the preferred algorithm for lookups.

When using this algorithm, the client converts the query first into
strings separated by spaces in the format `<address> <medium> <pepper>`.
The `<pepper>` is retrieved from `/hash_details`, the `<medium>` is
typically `email` or `msisdn` (both lowercase), and the `<address>` is
the 3PID to search for. For example, if the client wanted to know about
`alice@example.org`'s bindings, it would first format the query as
`alice@example.org email ThePepperGoesHere`.

{{% boxes/rationale %}}
Mediums and peppers are appended to the address to prevent a common
prefix for each 3PID, helping prevent attackers from pre-computing the
internal state of the hash function.
{{% /boxes/rationale %}}

After formatting each query, the string is run through SHA-256 as
defined by [RFC 4634](https://tools.ietf.org/html/rfc4634). The
resulting bytes are then encoded using URL-Safe [Unpadded
Base64](/appendices#unpadded-base64) (similar to [room version
4's event ID format](/rooms/v4#event-ids)).

An example set of queries when using the pepper `matrixrocks` would be:

    "alice@example.com email matrixrocks" -> "4kenr7N9drpCJ4AfalmlGQVsOn3o2RHjkADUpXJWZUc"
    "bob@example.com email matrixrocks"   -> "LJwSazmv46n0hlMlsb_iYxI0_HXEqy_yj6Jm636cdT8"
    "18005552067 msisdn matrixrocks"      -> "nlo35_T5fzSGZzJApqu8lgIudJvmOQtDaHtr-I4rU7I"

The set of hashes is then given as the `addresses` array in `/lookup`.
Note that the pepper used MUST be supplied as `pepper` in the `/lookup`
request.

#### `none`

This algorithm performs plaintext lookups on the identity server.
Typically this algorithm should not be used due to the security concerns
of unhashed identifiers, however some scenarios (such as LDAP-backed
identity servers) prevent the use of hashed identifiers. Identity
servers (and optionally clients) can use this algorithm to perform those
kinds of lookups.

Similar to the `sha256` algorithm, the client converts the queries into
strings separated by spaces in the format `<address> <medium>` - note
the lack of `<pepper>`. For example, if the client wanted to know about
`alice@example.org`'s bindings, it would format the query as
`alice@example.org email`.

The formatted strings are then given as the `addresses` in `/lookup`.
Note that the `pepper` is still required, and must be provided to ensure
the client has made an appropriate request to `/hash_details` first.

### Security considerations

{{% boxes/note %}}
[MSC2134](https://github.com/matrix-org/matrix-doc/pull/2134) has much
more information about the security considerations made for this section
of the specification. This section covers the high-level details for why
the specification is the way it is.
{{% /boxes/note %}}

Typically the lookup endpoint is used when a client has an unknown 3PID
it wants to find a Matrix User ID for. Clients normally do this kind of
lookup when inviting new users to a room or searching a user's address
book to find any Matrix users they may not have discovered yet. Rogue or
malicious identity servers could harvest this unknown information and do
nefarious things with it if it were sent in plain text. In order to
protect the privacy of users who might not have a Matrix identifier
bound to their 3PID addresses, the specification attempts to make it
difficult to harvest 3PIDs.

{{% boxes/rationale %}}
Hashing identifiers, while not perfect, helps make the effort required
to harvest identifiers significantly higher. Phone numbers in particular
are still difficult to protect with hashing, however hashing is
objectively better than not.

An alternative to hashing would be using bcrypt or similar with many
rounds, however by nature of needing to serve mobile clients and clients
on limited hardware the solution needs be kept relatively lightweight.
{{% /boxes/rationale %}}

Clients should be cautious of servers not rotating their pepper very
often, and potentially of servers which use a weak pepper - these
servers may be attempting to brute force the identifiers or use rainbow
tables to mine the addresses. Similarly, clients which support the
`none` algorithm should consider at least warning the user of the risks
in sending identifiers in plain text to the identity server.

Addresses are still potentially reversible using a calculated rainbow
table given some identifiers, such as phone numbers, common email
address domains, and leaked addresses are easily calculated. For
example, phone numbers can have roughly 12 digits to them, making them
an easier target for attack than email addresses.

## Establishing associations

The flow for creating an association is session-based.

Within a session, one may prove that one has ownership of a 3PID. Once
this has been established, the user can form an association between that
3PID and a Matrix user ID. Note that this association is only proved one
way; a user can associate *any* Matrix user ID with a validated 3PID,
i.e. I can claim that any email address I own is associated with
@billg:microsoft.com.

Sessions are time-limited; a session is considered to have been modified
when it was created, and then when a validation is performed within it.
A session can only be checked for validation, and validation can only be
performed within a session, within a 24-hour period since its most
recent modification. Any attempts to perform these actions after the
expiry will be rejected, and a new session should be created and used
instead.

To start a session, the client makes a request to the appropriate
`/requestToken` endpoint. The identity server then sends a validation
token to the user, and the user provides the token to the client. The
client then provides the token to the appropriate `/submitToken`
endpoint, completing the session. At this point, the client should
`/bind` the third party identifier or leave it for another entity to
bind.

### Format of a validation token

The format of the validation token is left up to the identity server: it
should choose one appropriate to the 3PID type. (For example, it would
be inappropriate to expect a user to copy a long passphrase including
punctuation from an SMS message into a client.)

Whatever format the identity server uses, the validation token must
consist of at most 255 Unicode codepoints. Clients must pass the token
through without modification.

### Email associations

{{% http-api spec="identity" api="v2_email_associations" %}}

### Phone number associations

{{% http-api spec="identity" api="v2_phone_associations" %}}

### General

{{% http-api spec="identity" api="v2_associations" %}}

## Invitation storage

An identity server can store pending invitations to a user's 3PID, which
will be retrieved and can be either notified on or look up when the 3PID
is associated with a Matrix user ID.

At a later point, if the owner of that particular 3PID binds it with a
Matrix user ID, the identity server will attempt to make an HTTP POST to
the Matrix user's homeserver via the
[/3pid/onbind](/server-server-api#put_matrixfederationv13pidonbind)
endpoint. The request MUST be signed with a long-term private key for
the identity server.

{{% http-api spec="identity" api="v2_store_invite" %}}

## Ephemeral invitation signing

To aid clients who may not be able to perform crypto themselves, the
identity server offers some crypto functionality to help in accepting
invitations. This is less secure than the client doing it itself, but
may be useful where this isn't possible.

{{% http-api spec="identity" api="v2_invitation_signing" %}}
