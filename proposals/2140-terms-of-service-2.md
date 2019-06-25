# MSC2140: Terms of Service API for Identity Servers and Integration Managers

[MSC1692](https://github.com/matrix-org/matrix-doc/issues/1692) introduces a
method for homeservers to require that users read and agree to certain
documents before being permitted to use the service. This proposal introduces a
corresponding method that can be used with Identity Servers and Integration
Managers.

The challenge here is that Identity Servers do not require any kind of user
login to access the service and so are unable to track what users have agreed
to what terms in the way that Homeservers do. We thereforce cannot re-use the
same method for Identity Servers without fundamentally changing the Identity
Service API.

Requirements for this proposal are:
 * ISs and IMs should be able to give multiple documents a user must agree to
   abide by
 * Each document shoud be versioned
 * ISs and IMs must be able to prevent users from using the service if they
   have not provided agreement.
 * A user should only have to agree to each version of each document once for
   their Matrix ID, ie. having agreed to a set of terms in one client, they
   should not have to agree to them again when using a different client.
 * Documents should be de-duplicated between services. If two or more services
   are hosted by the same organisation, the organistation should have the
   option to give their users a single document that encompasses both services
   (bearing in mind that the user must be able to opt-out of components of a
   service whilst still being able to use the service without that component).

## Proposal

Throuhgout this proposal, $prefix will be used to refer to the prefix of the
API in question, ie. `/_matrix/identity/api/v1` for the IS API and
`/_matrix/integrations/v1` for the IM API.

This proposal introduces:
 * The `$prefix/terms` endpoint
 * The `m.accepted_terms` section in account data
 * The `X-TERMS-TOKEN` HTTP header

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
        }
    }
}
```

Each document (ie. key/value pair in the 'policies' object) MUST be
uniquely identified by its URL. It is therefore strongly recommended
that the URL contains the version number of the document. The name
and version keys, however, are used only to provide a human-readable
description of the document to the user.

In the IM API, the client should provide authentication for this endpoint.

#### `POST $prefix/terms`:
Requests to this endpoint have a single key, `user_accepts` whose value is
a list of URLs (given by the `url` field in the GET response) of documents that 
the user has agreed to:

```json
{
    "user_accepts": ["https://example.org/somewhere/terms-2.0-en.html"]
}
```

In the IM API, the client should provide authentication for this endpoint.

The clients MUST include the correct URL for the language of the document that
was presented to the user and they agreed to. How servers store or serialise
acceptance into the `acceptance_token` is not defined, eg. they may internally
transform all URLs to the URL of the English-language version of each document
if the server deems it appropriate to do so. Servers should accept agreement of
any one language of each document as sufficient, regardless of what language a
client is operating in: users should not have to re-consent to documents if
they change their client to a different language.

The response MAY contain a `acceptance_token` which, if given, is an
opaque string that the client must store for use in subsequent requests
to any endpoint to the same server.

If the server has stored the fact that the user has agreed to these terms,
(which implies the user is authenticated) it can supply no `acceptance_token`.
The server may instead choose to supply an `acceptance_token`, for example if,
as in the IS API, the user is unauthenticated and therefore the server is
unable to store the fact a user has agreed to a set of terms.

The `acceptance_token` is an opaque string contining characters
`[a-zA-Z0-9._-]`. It is up to the server how it computes it, but the server
must be able to, given an `acceptance_token`, compute whether it constitutes
agreement to a given set of terms. For example, the simplest (but most verbose)
implemenation would be to make the `acceptance_token` the JSON array of
documents as provided in the request. A smarter implementation may be a simple
hash, or even cryptograhic hash if desired.

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
completes an `m.terms` flow on the HS, it SHOULD update this account data
section adding any the URLs of any additional documents that the user agreed to
to this list.

### Terms Acceptance in the API

Any request to any endpoint in the IS and IM APIs, with the exception of
`/_matrix/identity/api/v1` may return a `M_TERMS_NOT_SIGNED` errcode. This
indicates that the user must agree to (new) terms in order to use or continue
to use the service. The `_matrix/identity/api/v1/3pid/unbind` must also not
return the `M_TERMS_NOT_SIGNED` if the request has a valid signature from a
Homeserver.

The client uses the `GET $prefix/terms` endpoint to get the latest set of terms
that must be agreed to. It then cross-references this set of documents against
the `m.accepted_terms` account data and presents to the user any documents
that they have not already agreed to, along with UI for them to indicate their
agreement. Once the user has indicated their agreement, then, and only then,
must the client use the `POST $prefix/terms` API to signal to the server the
set of documents that the user has agreed to.

If the server returns an `acceptance_token`, the client should include this
token in the `X-TERMS-TOKEN` HTTP header in all subsequent requests to an
endpoint on the API with the exception of `/_matrix/identity/api/v1`.

The client must also include the X-TERMS-TOKEN on any request to the Homeserver
where it specifies an Identity Server to be used by the Homeserver. Homeservers
must read this header from the request headers of any such endpoint and add it
to the request headers of any request it makes to the Identity Server.

Both making the `POST $prefix/terms` request and providing an `X-TERMS-TOKEN`
header signal that the user consents to the terms contained within the
corresponding documents. That is to say, if a client or user obtains an
acceptance token via means other than a response to the `POST $prefix/terms`
API, inclusion of the acceptance token in an `X-TERMS-TOKEN` header in a
request still constitutes agreement to the terms in the corresponding
documents.

## Tradeoffs

This introduces a different way of accepting terms from the client/server API
which uses User-Interactive Authentication. In the client/server API, the use
of UI auth allows terms acceptance to be integrated into the registration flow
in a simple and backwards-compatible way. Indtroducing the UI Auth mechanism
into these other APIs would add significant complexity, so this functionality
has been provided with simpler, dedicated endpoints.

The `m.accepted_terms` section contains only URLs of the documents that
have been agreed to. This loses information like the name and version of
the document, but:
 * It would be up to the clients to copy this information correctly into
   account data.
 * Having just the URLs makes it much easier for clients to make a list
   of URLs and find documents not already agreed to.

## Potential issues

If the server does not authentcate users, some mechanism is required to track
users agreement to terms. The introduction of an extra HTTP header on all
requests adds overhead to every request and complexity to the client to add a
custom header.


## Security considerations

The `acceptance_token` is, in effect, a cookie and could be used to identify
users of the service.  Users of the Integration manager must be authenticated
anyway, so this is irrelevant for the IM API. It could allow an Identity Server
to identify users where it may otherwise not be able to do so (if a client was
careful to mask other identifying HTTP headers). Given most requests to the IS
API, by their nature, include 3pids which, even if hashed, will make users
easily identifiable, this probably does not add any significant concern.

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
