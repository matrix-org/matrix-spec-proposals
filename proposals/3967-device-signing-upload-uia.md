# MSC3967: Do not require UIA when first uploading cross signing keys

When a user first sets up end-to-end encryption cross-signing, their client
uploads their cross-signing keys to the server.

This [upload operation](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3keysdevice_signingupload)
requires a higher level of security by applying User-Interactive Auth (UIA) to
the endpoint.

This creates a usability issue at the point of user registration where a client
will typically want to immediately set up cross-signing for a new user.

The issue is that the client will immediately need the user to re-authenticate
even though the user just authenticated.

This usability issue has given rise to workarounds such as a
[configurable grace period](https://matrix-org.github.io/synapse/v1.98/usage/configuration/config_documentation.html#ui_auth)
(`ui_auth`.`session_timeout`) in Synapse whereby UIA will not be required for
uploading cross-signing keys where authentication has taken place recently.

This proposal aims to provide for a standard way to address this UIA usability
issue with respect to setting up cross-signing.

## Proposal

For the `POST /_matrix/client/v3/keys/device_signing/upload` endpoint, the
Homeserver MUST require User-Interactive Authentication (UIA) _unless_:
 - there is no existing cross-signing master key uploaded to the Homeserver, OR
 - there is an existing cross-signing master key and it exactly matches the
   cross-signing master key provided in the request body. If there are any additional
   keys provided in the request (self signing key, user signing key) they MUST also
   match the existing keys stored on the server. In other words, the request contains
   no new keys. If there are new keys, UIA MUST be performed.

In these scenarios, this endpoint is not protected by UIA. This means the client does not
need to send an `auth` JSON object with their request.

This change allows clients to freely upload 1 set of keys, but not modify/overwrite keys if
they already exist. By allowing clients to upload the same set of keys more than once, this
makes this endpoint idempotent in the case where the response is lost over the network, which
would otherwise cause a UIA challenge upon retry.

## Potential issues

See security considerations below.


## Alternatives

There has been some discussion around how to improve the usability of
cross-signing more generally. It may be that an alternative solution is to
provide a way to set up cross-signing in a single request.

## Security considerations

This change could be viewed as a degradation of security at the point of setting
up cross-signing in that it requires less authentication to upload cross-signing
keys on first use.

However, this degradation needs to be weighed against the typical real world
situation where a Homeserver will be applying a grace period and so allow a
malicious actor to bypass UIA for a period of time after each authentication.

### Existing users without E2EE keys

Existing user accounts who do not already have cross-signing keys set up will
now be able to upload keys without UIA. If such a user has their access token
compromised, an attacker will be able to upload a `master_key`, `self_signing_key`
and `user_signing_key`. This is a similar threat model to a malicious server admin
replacing these keys in the homeserver database.

This does not mean:
 - the attacker can "take over the account". Device login/logout endpoints are
   still protected via UIA.
 - the device will appear as verified. This requires out-of-band verification e.g
   emoji comparison, which will correctly detect the MITM'd key.

The main usability issue around this endpoint is requiring UIA, so it is critical
that we only require UIA when absolutely necessary for the security of the account.
In practice, this means requiring UIA when keys are _replaced_. There have been
suggestions to reintroduce a grace period (e.g after initial device login) or just
mandate it entirely for these old existing accounts. This would negatively impact
usability because:
 - it introduces temporal variability which becomes difficult to debug.
 - it introduces configuration variability which becomes difficult to debug. It's not
   clear what the grace period should actually be. Anything less than 1 hour risks
   catching initial x-signing requests from users who are on particularly awful networks.
   However, even increasing this to 1 hour poses the risk that we incorrectly catch the
   initial upload (e.g the client logs in on a bad GSM connection, then give up waiting
   for it to login and close the app, only reopening it the next day). This becomes
   difficult to debug in bug reports, as they just report HTTP 401s and it is unknown what
   the HS configuration is for the time delay. This is seen already due to the use (or non-use)
   of `ui_auth.session_timeout`.

## Unstable prefix

Not applicable as client behaviour need not change.

## Dependencies

None.
