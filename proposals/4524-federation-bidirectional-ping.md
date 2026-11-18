# MSC4524: Federation Bi-directional Ping

As it stands, Matrix has a very limited toolset to assist in troubleshooting federation problems.
A lot of problems can be discovered simply by trying to
[discover the faulty server][s2s-well-known], which will reveal misconfigurations,
[requesting the server's signing keys][s2s-keys], and then finally,
[requesting the server's version information][s2s-version]. This is done because all three of these
endpoints are unauthenticated, and are simple ways to immediately reveal misconfigurations (such as
incorrect well-known data, or a bad reverse proxy). However, there are distinct problems here:

* These endpoints are not intended for debugging.
* This methodology only reveals *simple* problems (and more complex problems may be misleading).
* This *only* tests that the remote server can *receive* data.

[s2s-well-known]: https://spec.matrix.org/v1.19/server-server-api/#getwell-knownmatrixserver
[s2s-keys]: https://spec.matrix.org/v1.19/server-server-api/#get_matrixkeyv2server
[s2s-version]: https://spec.matrix.org/v1.19/server-server-api/#get_matrixfederationv1version

Notably, there is distinctly no way to test for more complex issues, such as:

* Inbound signature verification failing due to a reverse proxy canonicalising request URIs (e.g.
  adding a trailing forward slash).
* Inbound signature verification failing as the remote cannot find a key for the origin.
  * This is typically an outbound connectivity issue that prevents A asking B for their keys.
* Implementation bugs that prevent outbound requests being valid in some way.
* A being unable to reach B (e.g. can resolve but not connect).

Doing these checks often requires spending hours troubleshooting federation issues, and Matrix does
not really present much protocol level tooling to assist in tracing this. This proposal will attempt
to narrow that gap with a simple "ping" and "pong" mechanism.

## Proposal

### Ping endpoint

A new, optionally authenticated, rate-limited federation endpoint is created:
`POST /_matrix/federation/v1/ping`.

The body for this endpoint is defined as follows:

|     Key    |       Type        | Purpose                                                         |
| ---------- | ---------------   | --------------------------------------------------------------- |
| `origin`   | optional `string` | The server name of the origin asking this question.             |
| `question` | `string`          | A random string that uniquely identifies this specific request. |

`origin` MUST be omitted if the request is authenticated. It is ignored if it is provided alongside
an X-Matrix authentication header from which an origin can be extracted.

The `question` MUST be between 6 and 255 characters. Invalid questions will be rejected with
`400 / M_INVALID_PARAM`.

The response body (200 OK) is as follows:

|   Key      |   Type              | Purpose                                                      |
| ---------- | ------------------- | ------------------------------------------------------------ |
| `answer`   | `string`            | A unique string that represents the answer to this question. |
| `details`  | optional `[string]` | Any information the target server believes the origin will be interested in. |

`details` SHOULD contain humanised messages that may be informational for the origin. For example,
if the remote cannot find signing keys for the origin, it may include a message like
`"Could not find signing keys for (origin): no DNS records for (origin)"`. Servers SHOULD NOT
reveal unsanitised error messages to avoid leaking sensitive information.

All requests, authenticated or not, SHOULD be rate-limited. Authenticated requests MAY use a less
strict bucket. A recommended rate-limit is 1 ping every 30 seconds (2 pings a minute)
per requesting origin, as more is unlikely to be necessary.

If a request is ratelimited, a standard `429 / M_LIMIT_EXCEEDED` response is returned.

If request authentication is provided, but the signature cannot be verified,
a standard `401 / M_UNAUTHORIZED` is returned.

Servers SHOULD allow this endpoint to be enabled or disabled, to prevent abuse if the server
is not expecting to be troubleshooting. If the endpoint is disabled, `404 / M_UNRECOGNIZED`
SHOULD be returned, to make the remote back off or degrade to prior ad-hoc methodologies. The
server MAY choose to return another, more distinct error code instead (such as `403 / M_FORBIDDEN`).

### Pong endpoint

Another authenticated, NOT rate-limited endpoint is introduced to accompany the former:
`POST /_matrix/federation/v1/pong`.

The request body for this endpoint is defined as follows:

| Key        | Type                | Purpose                                                        |
| ---------- | ------------------- | -------------------------------------------------------------- |
| `question` | `string`            | Identifies the `answer` provided to the associated `question`. |
| `details`  | optional `[string]` | Any information the remote server believes the target will be interested in. |

`details` SHOULD contain humanised messages that may be informational for the target. Servers
SHOULD NOT reveal unsanitised error messages to avoid leaking sensitive information.

The response body (200 OK) is an empty object (`{}`).

If authentication fails, the standard `401 / M_UNAUTHORIZED` is returned. There is no
unauthenticated fallback here.
<!-- TODO: why not? -->

If the question is unrecognized, `404 / M_NOT_FOUND` is returned. This is purely informational.

This endpoint is not rate-limited as it is solely listening for an incoming request with a specific
key, not creating any new data or requests.

### Running a ping

To initiate a ping, a server first generates a "question". This is a unique random string that will
identify a ping request. A server SHOULD NOT re-transmit the same question
(to avoid a stale answer).

Server A then sends a question to server B:

```plain
POST /_matrix/federation/v1/ping
Authorization: X-Matrix ...
Content-Type: application/json
Host: b.example

{"question": "f47930a1-50d1-43e4-8d63-555940988a7d"}
```

Server B then receives the request, and verifies the authentication signature.
If signature authentication fails, server B then responds with `401 M_UNAUTHORIZED`. Server A SHOULD
then retry the request (keeping the same question) without authentication. This enables B to perform
further diagnostics, potentially revealing why the signature could not be verified.

If the signature check succeeds (or there is none), and this question is new
(i.e. not a retransmission), server B then generates an "answer". This is just another
unique string. Server B then responds with this "answer":

```plain
HTTP/1.1 200 OK
Content-Type: application/json

{"answer": "eb473ab3-98a8-408e-a055-c6e1090e9066"}
```

Server B then follows this up with a request to A, confirming the answer:

```plain
POST /_matrix/federation/v1/pong
Authorization: X-Matrix ...
Content-Type: application/json
Host: a.example

{
  "question": "eb473ab3-98a8-408e-a055-c6e1090e9066"
}
```

Upon receipt, server A sees if it is expecting any answers with the remote's `question`. If it
is not, `404 / M_NOT_FOUND` is returned. The remote server might then wish to log that it could
not answer a question. This might also happen before B took too long to answer A.

Otherwise, servers A and B are confirmed to have established functional bi-directional
federation communication. If there were any problems in the process, more information for the users
performing these pings may be attached in the appropriate `details` keys.

### Fallback behaviour

Servers that do not implement (or enable) this debug functionality will return `404 / M_UNRECOGNIZED`.
Servers that want to initiate pings encountering this condition MAY then fall back to using the
previous, less reliable behaviours mentioned in this proposal's opening statement. This ensures
backwards compatibility is maintained, and the endpoints remain optional.

### Appropriate use

Servers MUST NOT use this endpoint to determine the "aliveness" of a remote server for routine
operation. This means pings should NOT be used to determine if a destination has been resolved
correctly, or if it is online before attempting to send it further requests.

## Potential issues

See: [security considerations](#security-considerations)

* This mechanism is still affected by the connectivity issues it aims to highlight. For example,
  servers may not be able to handle pings/pongs with malformed signatures due to their
  infrastructure (e.g. intercepted by middleware).
* This mechanism *aids* in troubleshooting, but is not a silver bullet, and may itself result
  in equally cryptic errors to the ones it tries to demystify.

### Does this belong in the specification?

This is a question that plagues similar ideas that never end up being formulated into formal
proposals. It is the author's firm belief that, while it would be uncharacteristic and a first for
this sort of proposal to be accepted into the specification, it belongs.

There is a clear desire for a mechanism like this - `conduwuit` implemented a system that allows
administrators to "ping" a remote server, querying their version info, which can reveal
common connectivity issues. This has then been retained in descendent software. There are also
several non-server tools that exist for troubleshooting federation problems, including:

* [matrix.org's `matrix-federation-tester`](https://github.com/matrix-org/matrix-federation-tester)
* [mtrnord's `connectivity tester`](https://phorge.mtrnord.blog/source/mcte/)
* [spaetz' `testmatrix`](https://pypi.org/project/testmatrix/)
* [continuwuity's maubot plugin][c1]

[c1]: https://forgejo.ellis.link/continuwuation/continuwuitybot/src/commit/b525dac0/continuwuitybot/bot.py#L307-L387

And more less-known/home-grown tools that achieve similar things. And outside of dedicated tooling,
there are several troubleshooting guides with sections dedicated to diagnosing federation problems.
Connectivity issues are one of the most common problems presented in homeserver support rooms[^1].

Even if such a mechanism does not fit directly into the specification, it is clear that some
formalised connectivity test is desired.

## Alternatives

*This is where alternative solutions could be listed. There's almost always another way to do things
and this section gives you the opportunity to highlight why those ways are not as desirable. The
argument made in this example is that all of the text provided by the template could be integrated
into the proposals introduction, although with some risk of losing clarity.*

Instead of adding a template to the repository, the assistance it provides could be integrated into
the proposal process itself. There is an argument to be had that the proposal process should be as
descriptive as possible, although having even more detail in the proposals introduction could lead to
some confusion or lack of understanding. Not to mention if the document is too large then potential
authors could be scared off as the process suddenly looks a lot more complicated than it is. For those
reasons, this proposal does not consider integrating the template in the proposals introduction a good
idea.

## Security considerations

Servers may receive pings when they are not anticipating engaging in troubleshooting. Servers SHOULD
provide deployments with the ability to disable the endpoints when not in use.

Unauthenticated pings can be abused to make the receiving server attempt to perform arbitrary
requests. This both enables amplification attacks (attacker can ask several remotes in parallel to
pong a single origin) and also DoS (attacker can ask the server to pong too many remotes at once,
some of which may be invalid, leading to situations like socket exhaustion). As such, servers should
apply stricter rate-limiting to unauthenticated requests, and should additionally rate-limit based
on client IP for unauthenticated pings.

To combat the amplification attack, servers receiving ping requests SHOULD apply an arbitrary delay
before issuing a pong.

Servers MAY apply further validation to unauthenticated requests, by utilising reverse DNS. Doing
so, a server receiving an unauthenticated ping MAY perform a reverse DNS lookup on the incoming IP,
and compare the result against the claimed `origin`. DNSSEC is recommended in this scenario, but is
out of scope for this proposal. Mismatched origins (or no rDNS record)
MAY result in the ping request being rejected with a `403 / M_FORBIDDEN` or otherwise,
but SHOULD log a warning regardless.

Servers SHOULD cache questions and answers to prevent retransmissions causing additional requests.

Servers implementing the ping/pong mechanism will inherently reveal their public IP address when
issuing ping/pong requests. This is a natural consequence of federation, but is highlighted as many
deployments forget their origin IP is revealed when federating, even if their reverse proxy is
on a different host (such as Cloudflare).

## Unstable prefix

`uk.timedout.msc4524.tabletennis` should be used as an unstable version:

|            Stable            |                               Unstable                              |
| ---------------------------- | ------------------------------------------------------------------- |
| `/_matrix/federation/v1/ping | `/_matrix/federation/unstable/uk.timedout.msc4524.tabletennis/ping` |
| `/_matrix/federation/v1/pong | `/_matrix/federation/unstable/uk.timedout.msc4524.tabletennis/pong` |

## Dependencies

None
