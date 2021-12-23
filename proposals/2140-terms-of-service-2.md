# MSC2140: Terms of Service API for Identity Servers and Integration Managers

*Note*: This MSC was added to in [MSC2264](https://github.com/matrix-org/matrix-doc/pull/2264)

[MSC1692](https://github.com/matrix-org/matrix-doc/issues/1692) introduces a
method for homeservers to require that users read and agree to certain
documents before being permitted to use the service. This proposal introduces a
corresponding method that can be used with Identity Servers and Integration
Managers.

Requirements for this proposal are:
 * ISes and IMs should be able to give multiple documents a user must agree to
   abide by
 * Each document should be versioned
 * ISes and IMs must, for each request that they handle, know that the user
   making the request has agreed to their data being used. This need not be
   absolute proof (we will always have to trust that the client actually
   showed the document to the user) but it must be reasonably demonstrable that
   the user has given informed consent for the client to use that service.
 * ISes and IMs must be able to prevent users from using the service if they
   have not provided agreement.
 * A user should only have to agree to each version of each document once for
   their Matrix ID, ie. having agreed to a set of terms in one client, they
   should not have to agree to them again when using a different client.
 * Documents should be de-duplicated between services. If two or more services
   are hosted by the same organisation, the organisation should have the
   option to give their users a single document that encompasses both services
   (bearing in mind that the user must be able to opt-out of components of a
   service whilst still being able to use the service without that component).

Identity Servers do not currently require any kind of user login to access the
service and so are unable to track what users have agreed to what terms in the
way that Homeservers do.

## Proposal

Throuhgout this proposal, $prefix will be used to refer to the prefix of the
API in question, ie. `/_matrix/identity/v2` for the IS API and
`/_matrix/integrations/v1` for the IM API.

Note the removal of the `/api` prefix and migration to v2 in the IS API
following convention from
[MSC2134](https://github.com/matrix-org/matrix-doc/issues/2134).

This proposal introduces:
 * A v2 API prefix, with authentication, for the Identity Service
 * The `$prefix/terms` endpoint
 * The `m.accepted_terms` section in account data
 * `POST /_matrix/client/r0/account/3pid/unbind` endpoints on the client/server
   API

This proposal removes:
 * The `bind_email` and `bind_msisdn` on the Homeserver `/register` endpoint

This proposal relies on both Integration Managers and Identity Servers being
able to identify users by their MXID and store the fact that a given MXID has
indicated that they accept the terms given. Integration Managers already
identify users in this way by authenticating them using the OpenID endpoint on
the Homeserver. This proposal introduces the same mechanism to Identity Servers
and adds authentication across the Identity Service API.

### IS API Authentication

All current endpoints within `/_matrix/identity/api/v1/` will be duplicated
into `/_matrix/identity/v2`, noting that MSC2134 changes the behaviour of
lookups. Authentication is still expected on MSC2134's proposed endpoints.
Support for `application/x-form-www-urlencoded` parameters in requests will
be dropped from all endpoints.

Any request to any endpoint within `/_matrix/identity/v2`, with the exception
of:
 * `/_matrix/identity/v2`
 * `/_matrix/identity/v2/pubkey/*`
 * The new `$prefix/account/register` endpoint
 * The new `GET /_matrix/identity/v2/terms`
 * `$prefix/account/logout`

...may return an error with `M_UNAUTHORIZED` errcode with HTTP status code 401.
This indicates that the user must authenticate with OpenID and supply a valid
`access_token`.

Clients authenticate either via an `Authorization` header with a `Bearer` token
or an `access_token` query parameter.

The existing endpoints under `/_matrix/identity/api/v1/` continue to be
unauthenticated but will be deprecated.  ISes may support the old v1 API for as
long as they wish. Once ISes remove support for the old APIs, those endpoints
must return HTTP Status 404. Clients must update to use the v2 API as soon as
possible.

OpenID authentication in the IS API will work the same as in the Integration Manager
API, as specified in [MSC1961](https://github.com/matrix-org/matrix-doc/issues/1961).

When clients supply an identity server to the Homeserver in order for the
Homeserver to make calls to the IS on its behalf, it must also supply its
access token for the Identity Server alongside in the `id_access_token` key of
the same JSON object. That is, in the main request object for `requestToken`
and `/_matrix/client/r0/rooms/{roomId}/invite` requests and in the
`threepidCreds` object when supplying 3PID credentials (eg.  in the
`m.email.identity` UI auth stage). The server must also relay
`M_TERMS_NOT_SIGNED` errors back to the client. Exceptions to this are any
requests where the only IS operation the Homeserver may perform is unbinding,
ie.  `/_matrix/client/r0/account/deactivate` and
`/_matrix/client/r0/account/3pid/delete`, in which case the unbind will be
authenticated by a signed request from the Homeserver.

### HS Register API

The `bind_email` and `bind_msisdn` options to `/_matrix/client/r0/register` in
the client/server API will be removed. Due to the fact that
`/_matrix/identity/v2/3pid/bind` requires authentication, it will no longer be
possible for the Homeserver to bind 3PIDs as part of the registration process.

### IS Register API

The following new APIs will be introduced to support OpenID auth as per
[MSC1961](https://github.com/matrix-org/matrix-doc/issues/1961):

 * `/_matrix/identity/v2/account/register`
 * `/_matrix/identity/v2/account`
 * `/_matrix/identity/v2/account/logout`

Note again the removal of the `/api` prefix and migration to v2 following
convention from
[MSC2134](https://github.com/matrix-org/matrix-doc/issues/2134).

### Terms API

New API endpoints will be introduced:

#### `GET $prefix/terms`:
This returns a set of documents that the user must agree to abide by in order
to use the service. Its response is similar to the structure used in the
`m.terms` UI auth flow of the Client/Server API:

```json
{
    "policies": {
        "terms_of_service": {
            "version": "2.0",
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-2.0-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-2.0-fr.html"
            }
        },
        "privacy_policy": {
            "version": "1.2",
            "en": {
                "name": "Privacy Policy",
                "url": "https://example.org/somewhere/privacy-1.2-en.html"
            },
            "fr": {
                "name": "Politique de confidentialité",
                "url": "https://example.org/somewhere/privacy-1.2-fr.html"
            }
        }
    }
}
```

Each document (ie. key/value pair in the 'policies' object) MUST be
uniquely identified by its URL. It is therefore strongly recommended
that the URL contains the version number of the document. The name
and version keys, however, are used only to provide a human-readable
description of the document to the user.

This endpoint does *not* require authentication.

#### `POST $prefix/terms`:
Requests to this endpoint have a single key, `user_accepts` whose value is
a list of URLs (given by the `url` field in the GET response) of documents that
the user has agreed to:

```json
{
    "user_accepts": ["https://example.org/somewhere/terms-2.0-en.html"]
}
```

This endpoint requires authentication.

The clients MUST include the correct URL for the language of the document that
was presented to the user and they agreed to. Servers should accept agreement
of any one language of each document as sufficient, regardless of what language
a client is operating in: users should not have to re-consent to documents if
they change their client to a different language.

The server responds with an empty JSON object. The server must not assume that
the client will agree to all documents in a single request.

### Accepted Terms Account Data

This proposal also defines the `m.accepted_terms` section in User Account
Data in the client/server API that clients SHOULD use to track what sets of
terms the user has consented to. This has an array of URLs under the 'accepted'
key to which the user has agreed to.

An `m.accepted_terms` section therefore resembles the following:

```json
{
    "accepted": [
        "https://example.org/somewhere/terms-1.2-en.html",
        "https://example.org/somewhere/privacy-1.2-en.html"
    ]
}
```

Whenever a client submits a `POST $prefix/terms` request to an IS or IM or
completes an `m.terms` flow on the HS (or as soon as possible afterwards, ie.
after registration is complete), it SHOULD update this account data section
adding any the URLs of any additional documents that the user agreed to to this
list.

### Terms Acceptance in the API

Before any requests are made to an Identity Server or Integration Manager,
the client must use the `GET $prefix/terms` endpoint to fetch the set of
documents that the user must agree to in order to use the service.

It then cross-references this set of documents against the `m.accepted_terms`
account data and presents to the user any documents that they have not already
agreed to, along with UI for them to indicate their agreement. If there are no
such documents (ie. if the `policies` dict is empty or the user has already
agreed to all documents) the client proceeds to perform the OpenID
registration. If there are new terms documents, the client prompts the user for
agreement, then once the user has indicated their agreement, it adds these URLs
to `m.accepted_terms` account data and then proceeds with OpenID
authentication, getting a token from the Homeserver and submitting this to the
service using the `register` endpoint.

Having done this, if the user agreed to any new documents, it performs a `POST
$prefix/terms` request to signal to the server the set of documents that the
user has agreed to.

Any request to any endpoint in the IM API, and the `/_matrix/identity/v2/`
namespace of the IS API, with the exception of `/_matrix/identity/v2` itself,
may return:

 * `M_UNAUTHORIZED` errcode with HTTP status code 401. This indicates that
   the user must authenticate with OpenID and supply a valid `access_token`.
 * `M_TERMS_NOT_SIGNED` errcode with HTTP status code 403. This indicates
   that the user must agree to (new) terms in order to use or continue to
   use the service.

The `/_matrix/identity/v2/3pid/unbind` endpoint must not return either of these
errors if the request has a valid signature from a Homeserver, and is being authenticated as such.

In summary, the process for using a service that has not previously been used
in the current login session is:

 * `GET $prefix/terms`
 * Compare result with `m.accepted_terms` account data, get set of documents
   pending agreement.
 * If non-empty, show this set of documents to the user and wait for the user
   to indicate their agreement.
 * Add the newly agreed documents to `m.accepted_terms`.
 * On success, or if there were no documents pending agreement, get an OpenID
   token from the Homeserver and submit this token to the `register` endpoint.
   Store the resulting access token.
 * If the set of documents pending agreement was non-empty, Perform a
   `POST $prefix/terms` request to the service with these documents.

### `POST /_matrix/client/r0/account/3pid/unbind`

A client uses this client/server API endpoint to request that the Homeserver
removes the given 3PID from the given Identity Server, or all Identity Servers.
Takes the same parameters as
`POST /_matrix/client/r0/account/3pid/delete`, ie. `id_server`, `medium`,
`address`. Similar to the other unbind endpoints, this endpoint does not
require an `id_access_token` because the homeserver can only unbind.

Returns the same as `POST /_matrix/client/r0/account/3pid/delete`.

Clients may add IS bindings for 3PIDs that already exist on the user's
Homeserver account by using the `POST /_matrix/client/r0/account/3pid`
to re-add the 3PID.

### Unstable feature flag for transition

In order to allow client implementations to determine if the homeserver they are developed
against supports `id_access_token`, an unstable feature flag of `m.id_access_token`
is to be added to `/versions`. When the flag is `false` or not present, clients must assume
that the homeserver does not support being given `id_access_token` and may receive an error
for doing so. Clients are expected to use the supported specification versions the homeserver
advertises instead of the feature flag's presence once this proposal is included in a release
of the specification.

## Tradeoffs

The Identity Service API previously did not require authentication, and OpenID
is reasonably complex, adding a significant burden to both clients and servers.
A custom HTTP header was also considered that could be added to assert that the
client agrees to a particular set of terms. We decided against this in favour
of re-using existing primitives that already exist in the Matrix ecosystem.
Custom HTTP headers are not used anywhere else within Matrix. This also gives a
very simple and natural way for ISes to enforce that users may only bind 3PIDs
to their own MXIDs.

This introduces a different way of accepting terms from the client/server API
which uses User-Interactive Authentication. In the client/server API, the use
of UI auth allows terms acceptance to be integrated into the registration flow
in a simple and backwards-compatible way. Another option here would be to use
UI Auth on the register endpoint. This would also not allow users to register
before accepting the terms. However, this would then make the OpenID
registration process different and non-standard.

The `m.accepted_terms` section contains only URLs of the documents that
have been agreed to. This loses information like the name and version of
the document, but:
 * It would be up to the clients to copy this information correctly into
   account data.
 * Having just the URLs makes it much easier for clients to make a list
   of URLs and find documents not already agreed to.

## Potential issues

This change deprecates all v1 endpoints and so will require clients to update
to continue working.

## Security considerations

Requiring authentication on the IS API means it will no longer be possible to
use it anonymously.

It is assumed that once servers publish a given version of a document at a
given URL, the contents of that URL will not change. This could be mitigated by
identifying documents based on a hash of their contents rather than their URLs.
Agreement to terms in the client/server API makes this assumption, so this
proposal aims to be consistent.


## Conclusion

This proposal adds an error response to all endpoints on the API and a custom
HTTP header on all requests that is used to signal agreement to a set of terms
and conditions. The use of the header is only necessary if the server has no
other means of tracking acceptance of terms per-user. The IS API is not
authenticated so ISes will have no choice but to use the header. The IM API is
authenticated so IMs may either use the header or store acceptance per-user.

A separate endpoint is specified with a GET request for retrieving the set
of terms required and a POST to indicate that the user consents to those
terms.
