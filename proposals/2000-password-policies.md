# MSC 2000: Proposal for server-side password policies

Some server administrators may want to ensure their users use passwords that
comply with a given policy. This is specifically relevant to companies and big
organisations which usually want to be able to apply a standardised password
policy across all services.

This proposal aims to define a way for servers to enforce a configurable
password policy and for clients to be aware of it so they can provide users with
an appropriate UX.

## Proposal

This proposal changes the following routes:

* `POST /_matrix/client/r0/register`
* `POST /_matrix/client/r0/account/password`

By adding a new error response with a 400 status code:

```json
{
    "errcode": "M_WEAK_PASSWORD",
    "error": "<text explaining why the password has been refused>"
}
```

This response would be returned by the server following a request to any of
these routes that contains a password that doesn't comply with the password
policy configured by the server's administrator.

This proposal also adds a new route, `GET /_matrix/client/r0/password_policy`,
which would return the following response with a 200 status code:

```json
{
    "type": "<policy type>",
    "params": {
        // Parameters
    }
}
```

This response format is intentionnally generic so that it allows server
administrators to rely on a custom solution, for example Dropbox's
[zxcvbn](https://github.com/dropbox/zxcvbn) tool (in which case the `params`
object could contain a `complexity` metric with a minimum complexity score the
password must reach).

This proposal also specifies a default policy type, named `m.default_policy`,
which `params` have the form:

```json
{
    "minimum_length": 20,
    "require_digits": true,
    "require_uppercase": true,
    "require_lowercase": true,
    "require_symbols": true
}
```

## Tradeoffs

A less flexible way to define a password policy (e.g. limiting a policy's
definition to the params for `m.default_policy`) would have been simpler,
however some clients are already implementing their own passowrd complexity
policy (Riot Web, for example, uses zxcvbn), and this solution would improve the
compatibility of the proposed solution with existing software.

Another point is that the localisation of the weak password message is here left
to the server's responsibility. This is not optimal, and there's an argument for
more detailed error codes (as opposed to a catch-all `M_WEAK_PASSWORD`).
However, this isn't really feasible with the approach described in this proposal
which allows for third-party solutions with their own criteria to evaluate a
password's complexity.
