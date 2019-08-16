# Unauthenticated Capabilities API

## Introduction

The existing [Capabilities
API](https://matrix.org/docs/spec/client_server/r0.5.0#get-matrix-client-r0-capabilities)
is an authenticated endpoint that allows a Matrix server to advertise which
services it does and does not provide. The authentication is due to the
possibility of suggesting that some capabilities are supported for some
users, while the same may not be supported for others (imagine a regular user
querying this endpoint, and then an application service doing the same).

While the ability to scope the capabilities to the requesting user is very
useful, there are use cases that could benefit from this API being called
from an unauthenticated user as well. For instance, information that a user
would like to know about a server before they sign up, such as whether the
server sends message content through a media-scanner, or whether the server
allows E2EE session key backup. A client could query this information before
they sign up. Another usecase is websites that lists public Matrix servers
could automatically query whether each server supports features that may be
important to users, without having to authenticate to the server to do so.


## Proposal

Add two new API endpoints:

* `GET /_matrix/client/r0/capabilities/server`
* `GET /_matrix/client/r0/capabilities/user`

`/capabilities/user` would be exactly the same as the existing
`/capabilities` endpoint, which requires authentication as what it returns is
scoped to the user making the request.

`/capabilities/server` would not require authentication and should return
information about the server's capabilities that would be pertinent to
non-authenticated users.

The existing `/capabilities` API would be replaced by `/capabilities/user`.

## Backwards compatibility

Servers supporting older versions of the Client Server API should continue to
answer `/capabilities` requests as if they were `/capabilities/user`. They
MUST NOT redirect the request to `/capabilities/user`, as this may confuse
older clients.

## Tradeoffs

The various features could have their own unauthenticated endpoints to check
whether or not the server supports them, but consolidating them into a single
API potentially reduces our API surface significantly.

Another solution to this problem is to have the existing `/capabilities`
endpoint return public information when no authentication is attempted, and
user-specific information when authentication is provided. This is certainly
functionally valid, however conceptually it's a little complicated to have an
API return different success states based on whether you've authenticated
yourself or not. In addition, none of the rest of the Matrix API currently
does this, so it may not be the best idea to introduce here.

## Conclusion

Adding an unauthenticated version of the `/capabilities` API gives servers
the flexibility to inform the general public about what features they
support, rather than only those that already have an account with them.
