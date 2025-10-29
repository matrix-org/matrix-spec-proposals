# MSC4198: Usage of OIDC login_hint

This proposal builds on the [OAuth 2.0 API](https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api) that was
added in v1.15 of the spec.

There are times when a client already knows or has asked for the user's identity before redirecting them to the homeserver's
account management interface to log in or to manage their devices. It would be useful to pass this information along to
the homeserver with these requests.

[OpenID Connect Core 1.0] specifies an optional `login_hint` authorization request parameter which is perfect for this
purpose but it leaves the contents of the parameter vague and "to the OP's discretion".

This MSC aims to define a format for this parameter for use in the context of Matrix for interoperability.


## Proposal

### Format

In order to futureproof for new new types of hints in the future and to be able to identify and parse them easily,
we introduce a format that contains a prefix before the value, separated by a colon.

The ABNF syntax for it is as follows:
```
login-hint = prefix ":" value

prefix = 1*prefix-char

prefix-char = %x21-39 / %x3B-7E ; VCHAR excluding ":"

value = 1*VCHAR
```

### The `mxid` hint

This MSC specifies a hint that contains the user's [MXID].
The prefix for this hint is `mxid` (all lowercase) and the value is the Matrix user ID as specified in the
[User Identifiers][MXID] section.

Example valid hint value: `mxid:@example-user:example.com`

### Usage in authorization requests

A client MAY start the login flow by asking the user for their MXID.
It SHOULD then parse the domain, discover the homeserver and its auth metadata ([OAuth 2.0 API Server metadata discovery]),
register itself with the homeserver ([OAuth 2.0 API Client registration])
and send the user to the authorization endpoint ([OAuth 2.0 API Login flow]), all in one step.

Alternatively, this MAY also be used when the user is already logged in and the client is requesting additional scopes
(when more granular scopes are defined in a future proposal).

To improve the UX of this flow, the MXID MAY be sent to the homeserver with the authorization request in the OPTIONAL
`login_hint` query parameter from [OpenID Connect Core 1.0], following the format specified above using the `mxid` hint
type.

Despite the `login_hint` parameter being defined in the OpenID Connect specification, homeservers supporting this proposal
MUST handle the parameter even without the `openid` scope.

The homeserver SHOULD then assist the user to complete the login flow with the correct account.

The client MUST be prepared to handle a case where the account that the user signs into will not be the one that was
initially suggested, especially if the homeserver does not support the `login_hint` parameter and/or the user mistakenly
uses the wrong credentials.
The client MAY inform the user about ending up on a different account than intended and present an option to try again.

#### Example authorization request

Expanding on the example authorization request shown in [OAuth 2.0 API Login flow] (broken down into multiple lines for
readability),
with the following additional parameters:

- `login_hint` set to `mxid:@example-user:example.com`

```
https://account.example.com/oauth2/auth?
    client_id             = s6BhdRkqt3 &
    response_type         = code &
    response_mode         = fragment &
    redirect_uri          = https://app.example.com/oauth2-callback &
    scope                 = urn:matrix:client:api:* urn:matrix:client:device:AAABBBCCCDDD &
    state                 = ewubooN9weezeewah9fol4oothohroh3 &
    code_challenge        = 72xySjpngTcCxgbPfFmkPHjMvVDl2jW1aWP7-J6rmwU &
    code_challenge_method = S256 &
    login_hint            = mxid:@example-user:example.com
```

With the line breaks removed and values properly encoded:
```
https://account.example.com/oauth2/auth?client_id=s6BhdRkqt3&response_type=code&response_mode=fragment&redirect_uri=https%3A%2F%2Fapp.example.com%2Foauth2-callback&scope=urn%3Amatrix%3Aclient%3Aapi%3A*+urn%3Amatrix%3Aclient%3Adevice%3AAAABBBCCCDDD&state=ewubooN9weezeewah9fol4oothohroh3&code_challenge=72xySjpngTcCxgbPfFmkPHjMvVDl2jW1aWP7-J6rmwU&code_challenge_method=S256&login_hint=mxid%3A%40example-user%3Aexample.com
```

### Usage in [MSC4191] account management

We also add the `login_hint` query parameter for the [MSC4191] `account_management_uri` using the same format.

For example, if `@example-user:example.com` wishes to delete the device `ABCDEFGH` where the advertised
`account_management_uri` was `https://account.example.com/myaccount` the client could open a link to
`https://account.example.com/myaccount?action=org.matrix.device_delete&device_id=ABCDEFGH&login_hint=mxid%3A%40example-user%3Aexample.com`.

Similarly to the authorization request, the homeserver SHOULD assist the user to the account the action was intended for.

### Examples of homeserver assistance

These are just some examples of what the homeserver could do. None of these are required.

#### Prefilling the username

The simplest method is to prefill the username in the username & password form.
Implementing this is recommended, as it makes sure the user doesn't have to type their username multiple times.

A more visually appealing method would be to replace the username field entirely with a preview of the user's profile
including avatar and display name.

#### Filtering login methods

The homeserver could filter the login methods presented to only the ones the user has available to them.
This can help if the user has forgotten if they set a password or used a social login.

**Note:** See security consideration #1.

#### Passing a `login_hint` to upstream providers

To take full advantage of the benefits of `login_hint`, a suitable value that the upstream provider expects could be
supplied when logging in with one.
Since this proposal only covers the Matrix protocol, upstream providers likely won't follow the format laid out in this
proposal and any upstream hint value would have to be configured on a per provider basis by the administrator of the
homeserver.

**Note:** See security consideration #2.

#### Session management

If there is already an active session with a different user, the homeserver could decide to log out and take the user to
the login screen instead of showing the consent screen or account management interface for the wrong account.

If multiple concurrent sessions are supported, the homeserver could automatically switch to the correct session before
showing the consent screen or account management interface.

## Potential issues

TBD


## Alternatives

One alternative would be to only include the localpart (e.g. `login_hint=example-user`),
as the domain is redundant information for the homeserver itself.
However, the lack of a prefix has the potential to make adding and distinguishing additional future formats difficult
and using the full MXID builds on top of existing concepts within the spec.


## Security considerations

1. Filtering the available login methods has a risk of revealing too much information about the user and their security,
allowing malicious actors to focus their efforts.
However, other platforms have recently started being honest about the methods available to the user in their multi-step
flows, deciding that the UX benefit outweighs the security risks.
2. In the case an upstream provider wants some personally identifiable information as the value for the `login_hint`,
such as an email, providing it would leak that information during the login flow.
Therefore it is only recommended to provide such a value in an enterprise SSO situation where the value is predictable
and public like a work email.


## Unstable prefix

For the authorization request we are borrowing the existing OIDC parameter so an unstable prefix isn't necessary.

For the account management request, `org.matrix.msc4198.login_hint` should be used instead of `login_hint` while in
development.

## Dependencies

This MSC builds on [MSC4191] (which at the time of writing has not yet been accepted into the spec).

[OpenID Connect Core 1.0]: https://openid.net/specs/openid-connect-core-1_0.html
[MXID]: https://spec.matrix.org/v1.11/appendices/#user-identifiers
[OAuth 2.0 API Server metadata discovery]: https://spec.matrix.org/v1.15/client-server-api/#server-metadata-discovery
[OAuth 2.0 API Client registration]: https://spec.matrix.org/v1.15/client-server-api/#client-registration
[OAuth 2.0 API Login flow]: https://spec.matrix.org/v1.15/client-server-api/#login-flow
[MSC4191]: https://github.com/matrix-org/matrix-spec-proposals/pull/4191
