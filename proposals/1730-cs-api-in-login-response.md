# MSC1730: Mechanism for redirecting to an alternative server during login

Complex homeserver deployments may consist of several homeserver instances,
where the HS to be used depends on the individual user, and is determined at
login time.

It may therefore be useful to provide a mechanism to tell clients which
endpoint they should use for the client-server (C-S) API after login.

## Proposal

The response to `POST /_matrix/client/r0/login` currently includes the fields
`user_id`, `access_token`, `device_id`, and the deprecated `home_server`.

We should add to this an optional field `base_cs_url`, which gives a base URL
for the client-server API.

As with
[.well-known](https://matrix.org/docs/spec/client_server/r0.4.0.html#well-known-uri),
clients would then add `/_matrix/client/...` to this URL to form valid C-S
endpoints.

(Note that the deprecated `home_server` field gives the `server_name` of the
relevant homeserver, which may be quite different to the location of the C-S
API, so is not of use here. Further we cannot repurpose it, because (a) this
might break existing clients; (b) it spells homeserver wrong.)

A representative sequence diagram is shown below.

![Sequence diagram](images/1730-seq-diagram.svg)

### Potential issues

A significant problem with the proposed architecture is that the portal server
has to proxy the `/login` request, so that it can update the response. This
leads to the following concerns:

* The target homeserver sees the request coming from the portal server rather
  than the client, so that the wrong IP address will be recorded against the
  user's session. (This might be a problem for, for example, IP locking the
  session, and might affect the `last_seen_ip` field returned by `GET
  /_matrix/client/r0/devices`.)

  This can be mitigated to some extent via the use of an `X-Forwarded-For`
  header, but that then requires the portal server to authenticate itself with
  the target homeserver in some way.

* It causes additional complexity in the portal server, which must now be
  responsible for making outbound HTTP requests.

* It potentially leads to a privacy leak, since the portal server could snoop
  on the returned access token. (Given that the portal server must be trusted
  to some extent in this architecture, it is unclear how much of a concern this
  really is.)

An alternative implementation of the portal server would be for the portal
server to redirect the `/login` request with a 307 response. This solves the
above problems, but may reduce flexibility, or require more state to be managed
on the portal server [1].

## Tradeoffs

Alternative solutions might include:

### Proxy all C-S endpoints

It would be possible for the portal to proxy all C-S interaction, as well as
`/login`, directing requests to the right server for the user.

This is unsatisfactory due to the additional latency imposed, the load on the
portal server, and the fact that it makes the portal a single point of failure
for the entire system.

### Perform a .well-known lookup after login

Once clients know the server name of the homeserver they should be using
(having extracted it from the `/login` response), they could perform a
`.well-known` lookup on the target server to locate its C-S API.

This has the advantage of reusing existing mechanisms, but has the following
problems:

* Clients are currently required to do a `.well-known` lookup *before* login,
  so that they can find the correct endpoint for the `/login` API. That means
  they will have to do *two* `.well-known` lookups - one before and one after
  login.

  This adds latency and overhead, and complicates client implementations.

* It complicates deployment, since each target server has to support a
  `.well-known` lookup.

* Since the portal already has knowledge of the location of the C-S API for the
  target homeserver, and has mapped the login request onto the correct HS, it
  feels redundant to have a separate mechanism which repeats that mapping.

### Add an alternative redirection mechanism in the login flow

We could specify that the `/login` response could contain a `redirect` field
property instead of the existing `user_id`/`access_token`/`device_id`
properties. The `redirect` property would give the C-S API of the target
HS. The client would then repeat its `/login` request, and use the specified
endpoint for all future C-S interaction.

This approach would complicate client implementations.


[1] The reason more state is needed is as follows: because the portal is now
redirecting the login rather than proxying it, it cannot modify the login
dictionary. This is a problem for the single-sign-on flow, which culminates in
an `m.login.token` login. The only way that the portal can identify a given
user session - and thus know where to redirect to - is via the login token, and
of course, it cannot modify that token without making it invalid for the target
HS. It therefore has to use the login token as a session identifier, and store
session state..
