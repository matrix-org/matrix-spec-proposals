# MSC4026: Allow /versions to optionally accept authentication

## Introduction

Synapse is implementing the ability to turn some unstable features on per-user. Once this is 
implemented, certain experimental features will be available to be enabled per-user via the [Admin API](https://matrix-org.github.io/synapse/latest/usage/administration/admin_api/index.html).
The intention is to allow certain users to test the experimental feature without making it available to
all users before it is stable.
This is in addition to the current ability to toggle on/off those features system-wide in the configuration.

However, this poses a problem when considering how to advertise that those features are enabled to clients. 
Traditionally, to determine what unstable features were available from a server clients checked the [`/_matrix/client/versions`](https://spec.matrix.org/v1.7/client-server-api/#get_matrixclientversions)
endpoint, which in turn checked the Synapse configuration to determine what experimental features were enabled. With the
changes being implemented this is no longer possible, as some experimental features may be enabled per-user. As the 
`/_matrix/client/versions` endpoint does not require authentication there is no way to know which experimental features 
are enabled - there is no access token that we can extract user info from to determine which unstable features are 
currently enabled (as they may only be enabled for some users) - and thus there is no way to correctly communicate to 
clients which experimental features are enabled.

## Proposal

The proposal to remedy this is to make `/_matrix/client/versions` optionally accept authentication, and ask clients
to use the authenticated version when determining which experimental features are enabled. 

## Potential issues

This does raise the question of what the non-authenticated version of `/_matrix/client/versions` should return with 
regard to unstable features if the proposal is accepted.

## Alternatives

An alternative to the proposal would be to move advertising the unstable features to the [`/_matrix/client/v3/capabilities`](https://spec.matrix.org/v1.7/client-server-api/#get_matrixclientv3capabilities) 
endpoint, which does require authentication. However, the spec is clear that `/_matrix/client/v3/capabilities` "should 
not be used to advertise unstable or experimental features - this is better done by the `/versions` endpoint." Thus, 
this seems like a less desirable option than the proposed solution. 

## Security considerations

None that I am currently aware of. 