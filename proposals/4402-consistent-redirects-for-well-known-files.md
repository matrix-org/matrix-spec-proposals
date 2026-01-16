# MSC4402: Consistent redirects for .well-known-files

The spec recommends to [follow a 30x
redirect](https://spec.matrix.org/v1.17/server-server-api/#getwell-knownmatrixserver) from
`/.well-known/matrix/server`. This MSC proposes the same behavior for `/.well-known/matrix/client`.
After initial setup, this change allows server admins to maintain and update matrix-related
`.well-known`-files on the subdomain they are hosting their matrix server on, without ever touching
files on the base domain, again. This simplifies maintenance in large organizations where webservers
behind different (sub-)domains are not necessarily maintained by the same people and any changes to
the base domain require coordination with a separate team.

## Proposal

Section 2.1 of [the Server-Server-API
spec](https://spec.matrix.org/v1.17/server-server-api/#getwell-knownmatrixserver) states the
following with respect to `/.well-known/matrix/server` requests:

> Servers should follow 30x redirects, carefully avoiding redirect loops, and use normal X.509
> certificate validation.

We propose to add a similar instruction to Section 3.1 of [the Client-Server-API
spec](https://spec.matrix.org/v1.17/client-server-api/#getwell-knownmatrixclient) regarding requests
to `/.well-known/matrix/client`:

> \[NEW\] Clients should follow 30x redirects, carefully avoiding redirect loops, and use normal
> X.509 certificate validation.

This information should be reflected in "The flow for auto-discovery" right above in Section 3.1. A
new step 3.1. should be added as such:

> 3.  Make a GET request to https://hostname/.well-known/matrix/client.
>     1.  \[NEW\] If the returned status code is 30x, follow redirects, carefully avoiding redirect
>         loops, and continue:
>     2.  If the returned status code is 404, then `IGNORE`.
>     3.  If the returned status code is not 200, or the response body is empty, then `FAIL_PROMPT`.

## Potential issues

This change breaks backwards compatibility between servers relying on 30x-redirects and old clients
that do not implement this MSC.

## Alternatives

Alternatively and without any changes to the spec, `.well-known`-files can be [reverse-proxied from
the base
domain](https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/configuring-well-known.md#option-2-setting-up-reverse-proxying-of-the-well-known-files-from-the-base-domains-server-to-the-matrix-server).
In corporate networks with strict firewall rules however, the reverse proxy might not necessarily be
able to access the source files on the matrix server.

## Security considerations

An attacker with the capability to setup or tamper with a redirect from the base domain, usually
already has gained access over the webserver or load balancer, which implies they are already able
to serve `.well-known`-files of their choice, anyway. In this regard, the author does not see any
new threats enabled by this MSC.

This MSC makes it somewhat more convenient to setup a `.well-known`-redirect to a separate
(sub)domain running a matrix server, abandon it at some point, and lose control over that domain.
This way, an attacker getting hold of the abandoned domain could operate a fake matrix server
claiming to represent the owner of the original base domain. Given that 30x-redirects are already
possible for the Server-Server-API, the security impact of this MSC, which only covers the
Client-Server-API, seems negligible.

## Unstable prefix

## Dependencies

This MSC is a narrowed down version of
[MSC2499](https://github.com/matrix-org/matrix-spec-proposals/pull/2499) that seems to be inactive.
Should MSC2499 be merged first, this MSC becomes obsolete.
