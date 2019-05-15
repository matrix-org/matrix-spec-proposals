# MSC 2000: Proposal for server-side password policies

Some server administrators may want to ensure their users use passwords that
comply with a given policy. This is specifically relevant to companies and big
organisations which usually want to be able to apply a standardised password
policy across all services.

This proposal aims to define a way for servers to enforce a configurable
password policy and for clients to be aware of it so they can provide users with
an appropriate UX.

## Proposal

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

This proposal adds new error codes to the existing list:

* `M_PASSWORD_TOO_SHORT`: the provided password's length is shorter than the
  minimum length required by the server.
* `M_PASSWORD_NO_DIGITS`: the password doesn't contain any digit but the server
  requires at least one.
* `M_PASSWORD_NO_UPPERCASE`: the password doesn't contain any uppercase letter
  but the server requires at least one.
* `M_PASSWORD_NO_LOWERCASE`: the password doesn't contain any lowercase letter
  but the server requires at least one.
* `M_PASSWORD_NO_SYMBOLS`: the password doesn't contain any symbol but the
  server requires at least one.
* `M_PASSWORD_IN_DICTIONNARY`: the password was found in a dictionnary.

Finally, this proposal changes the following routes:

* `POST /_matrix/client/r0/register`
* `POST /_matrix/client/r0/account/password`

By adding new response formats with a 400 status code following this format:

```json
{
    "errcode": "<error code>",
    "error": "<text further describing the error>"
}
```

This response would be returned by the server following a request to any of
these routes that contains a password that doesn't comply with the password
policy configured by the server's administrator.

In this response, `<error code>` is one of the error code described above, or
`M_WEAK_PASSWORD` if the reason the password has been refused doesn't fall into
one of these categories.

## Tradeoffs

A less flexible way to define a password policy (e.g. limiting a policy's
definition to the params for `m.default_policy`) would have been simpler,
however some clients are already implementing their own passowrd complexity
policy (Riot Web, for example, uses zxcvbn), and this solution would improve the
compatibility of the proposed solution with existing software.
