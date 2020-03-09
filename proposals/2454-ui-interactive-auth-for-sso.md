# User-Interactive Auth for SSO-backed homeserver

Certain endpoints, such as `DELETE /_matrix/client/r0/devices/{deviceId}` and
`POST /_matrix/client/r0/account/3pid/add`, require the user to reconfirm their
identity, as a guard against a leaked access token being used to take over an
entire account.

On a normal homeserver, this is done by prompting the user to enter their
password. However, on a homeserver where users authenticate via a single-sign-on
system, the user doesn't have a password registered with the homeserver. Instead
we need to delegate that check to the SSO system.

At the protocol level, this means adding support for SSO to
[user-interactive auth](https://matrix.org/docs/spec/client_server/r0.6.0#user-interactive-authentication-api).

In theory, any clients that already implement the fallback process for unknown
authentication types will work fine without modification. It is unknown whether
this is widely supported among clients.

### UI Auth Overview

When the client calls one of the protected endpoints, it initially returns a 401
response. For example:

```
POST /_matrix/client/r0/delete_devices HTTP/1.1
Content-Type: application/json

{
    "devices": ["FSVVTZRRAA"]
}

HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
    "flows": [
        {
            "stages": [
                "m.login.password"
            ]
        }
    ],
    "params": {},
    "session": "dTKfsLHSAJeAhqfxUsvrIVJd"
}
```

The client:

* inspects the "flows" list
* discovers there is a flow it knows how to follow
* carries out the first "stage" of that flow (m.login.password)

In this example, the client prompts the user to enter a password.

The client then resubmits with an additional 'auth' param, with "type" giving
the name of the authentication type it has just carried out. That completes the
authentication flow, so the server is now happy, and returns a 200:

```
POST /_matrix/client/r0/delete_devices HTTP/1.1
Content-Type: application/json

{
  "devices": ["FSVVTZRRAA"],
  "auth": {
    "session":"dTKfsLHSAJeAhqfxUsvrIVJd",
    "type":"m.login.password",
    "identifier":{"type":"m.id.user", "user":"@userid:matrix.org"},
    "password":"<password>"
  }
}


HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 179

{}
```

## Proposal

We add an `m.login.sso` authentication type to the UI auth spec. There are no
additional params as part of this auth type.

1.  If the client wants to complete that authentication type, it opens a browser
    window for `/_matrix/client/r0/auth/m.login.sso/fallback/web?session=<...>`
    with session set to the UI-Auth session id (from the "auth" dict).

    The homeserver returns a page which asks for the user's confirmation before
    proceeding. See the security considerations section below for why this is
    necessary. For example, the page could say words to the effect of:

    > A client is trying to remove a device/add an email address/take over your
    > account. To confirm this action, **re-authenticate with single sign-on**.
    > If you did not expect this, your account may be compromised!
2.  The link, once the user clicks on it, goes to the SSO provider's page.
3.  The SSO provider validates the user, and redirects the browser back to the
    homeserver.
4.  The homeserver validates the response from the SSO provider, updates the
    user-interactive auth session to show that the SSO has completed,
    [serves the fallback auth completion page as specced](https://matrix.org/docs/spec/client_server/r0.6.0#fallback).
5.  The client resubmits its original request, with its original session id,
    which now should complete.

Note that the post-SSO URL on the homeserver is left up to the homeserver
implementation rather than forming part of the specification, choices might be
limited by the chosen SSO implementation, for example:

*   SAML2 servers typically only support one URL per service provider, so in
    practice it will need to be the same as that already used for the login flow
    (for synapse, it's /_matrix/saml2/authn_response) - and the server needs to
    be able to figure out if it's doing SSO for a login attempt or an SSO
    attempt.
*   CAS doesn't have the same restriction.

### Example flow:

0.  Client submits the request, which the server says requires SSO:

    ```
    POST /_matrix/client/r0/delete_devices HTTP/1.1
    Content-Type: application/json
    Authorization: Bearer xyzzy

    {
        "devices": ["FSVVTZRRAA"]
    }

    HTTP/1.1 401 Unauthorized
    Content-Type: application/json

    {
        "flows": [
            {
                "stages": [
                    "m.login.sso"
                ]
            }
        ],
        "params": {},
        "session": "dTKfsLHSAJeAhqfxUsvrIVJd"
    }
    ```

1.  Client opens a browser window for the fallback endpoint:

    ```
    GET /_matrix/client/r0/auth/m.login.sso/fallback/web
        ?session=dTKfsLHSAJeAhqfxUsvrIVJd HTTP/1.1

    HTTP/1.1 200 OK

    <body>
    can delete device pls?
    <a href="https://sso_provider/validate?SAMLRequest=...">clicky</a>
    </body>
    ```

2.  The user clicks the confirmation link which goes to the SSO provider's site:

    ```
    GET https://sso_provider/validate?SAMLRequest=<etc> HTTP/1.1

    ... SAML/CAS stuff
    ```

3.  The SSO provider validates the user and ends up redirecting the browser back
    to the homeserver. (The example below shows a 302 for simplicity but SAML normally uses a 200 with an html <form>, with javascript to automatically submit it.)

    ```
    HTTP/1.1 302 Moved
    Location: https://homeserver/_matrix/saml2/authn_response?
        SAMLResponse=<etc>
    ```

4.  The browser sends the SSO response to the homeserver, which validates it and
    shows the fallback auth completion page:

    ```
    GET /_matrix/saml2/authn_response?SAMLResponse=<etc>


    HTTP/1.1 200 OK

    <script>
    if (window.onAuthDone) {
        window.onAuthDone();
    } else if (window.opener && window.opener.postMessage) {
         window.opener.postMessage("authDone", "*");
    }
    </script>

    <p>Thank you.</p>
    <p>You may now close this window and return to the application.</p>
    ```

5.  The client closes the browser popup if it is still open, and resubmits its
    original request, which now succeeds:

    ```
    POST /_matrix/client/r0/delete_devices HTTP/1.1
    Content-Type: application/json
    Authorization: Bearer xyzzy

    {
        "auth": {
          "session": "dTKfsLHSAJeAhqfxUsvrIVJd"
        }
    }

    HTTP/1.1 200 OK
    Content-Type: application/json

    {}
    ```

## Alternatives

An alternative client flow where the fallback auth ends up redirecting to a
given URI, instead of doing JavaScript postMessage foo could be considered.
This is probably an orthogonal change to the fallback auth though.

## Security considerations

### Why we need user to confirm before the SSO flow

Recall that the thing we are trying to guard against here is a single leaked
access-token being used to take over an entire account. So let's assume the
attacker has got hold of an access token for your account. What happens if the
confirmation step is skipped?

The attacker, who has your access token, starts a UI Authentication session to
add their email address to your account.

They then sends you a link "hey, check out this cool video!"; the link leads (via
an innocent-looking URL shortener or some other phishing technique) to
`/_matrix/client/r0/auth/m.login.sso/fallback/web?session=<...>`, with the ID of
the session that he just created.

Since there is no confirmation step, the server redirects directly to the SSO
provider.

It's common for SSO providers to redirect straight back to the app if you've
recently authenticated with them; even in the best case, the SSO provider shows
an innocent message along the lines of "Confirm that you want to sign in to
<your Matrix homeserver>".

After redirecting back to the homeserver, the SSO is completed and the
attacker's session is validated. They are now able to make their malicious
change to your account.

This problem can be mitigated by clearly telling the user what is about to happen.

### Reusing UI-Auth sessions

The security of this relies on UI-Auth sessions only being used for the same
request as they were initiated for. It is not believed that this is currently
enforced.

## Unstable prefix

A vendor prefix of `org.matrix.login.sso` (instead of `m.login.sso` is proposed
until this is part of the specification.
