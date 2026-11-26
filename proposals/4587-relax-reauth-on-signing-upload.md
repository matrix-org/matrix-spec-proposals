# MSC4587: Relaxing requirements for reauthentication on cross-signing-key upload

The current specification has this to say about uploading public cross-signing keys
via [`POST /_matrix/client/v3/keys/device_signing/upload`]:

[`POST /_matrix/client/v3/keys/device_signing/upload`]: https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3keysdevice_signingupload

> User-Interactive Authentication MUST be performed for regular clients, except in these cases:
>
> * there is no existing master signing key uploaded to the homeserver, OR
> * there is an existing master signing key and it exactly matches the master
>   signing key provided in the request body [and other keys also match].

In practice, we have found this overly restrictive. This proposal suggests
relaxing the requirement, allowing server implementations to make their own
decision as to when to apply this additional check.

## Background

Matrix encryption expects each user to have a set of cross-signing keys, also
known (under [MSC4161]) as the user's "digital identity". Each of the user's
devices must then be signed by this identity.

[MSC4161]: https://github.com/matrix-org/matrix-spec-proposals/blob/andybalaam/crypto-terminology/proposals/4161-crypto-terminology.md#digital-identity

The cross-signing keys are asymmetric: they each have a public part, which the user
shares freely, and a secret part, which the user keeps to themselves.

The public parts are published by calling [`POST
/_matrix/client/v3/keys/device_signing/upload`]. Other users can then download
the public cross-signing keys for a particular user, and use them to validate
the signatures on each of that user's devices, to ensure they are genuine.

It is clear, then, that uploading a new set of public keys represents a
powerful attack vector for a would-be eavesdropper. Consider that Mallory has
gained access to an access token belonging to Alice: Mallory could then upload
a new set of cross-signing keys, which she then uses to sign a device under her
control, and is therefore able to intercept encrypted messages sent to Alice.

For this reason, the `/keys/device_signing/upload` endpoint is subject to
additional authentication requirements:

 * Initially the requirement (under
   [MSC1756](https://github.com/matrix-org/matrix-spec-proposals/pull/1756))
   was that all requests must pass through user-interactive authentication.

 * This was later relaxed in
   [MSC3967](https://github.com/matrix-org/matrix-spec-proposals/pull/3967) to
   allow the upload to take place without re-authentication if there was no
   existing published key.

 * A further change came in
   [MSC4312](https://github.com/matrix-org/matrix-spec-proposals/pull/4312),
   which specified how the re-authentication requirement should interact with
   OAuth 2.0 authentication (though note that no changes were made to when the
   reauthentication should take place).

In practice, the reauthentication requirements continue to be overly
zealous. For example, consider a user who has no active devices and has never
set up [server-side
secret storage](https://spec.matrix.org/v1.19/client-server-api/#storage) (aka
"Recovery"). Such a user has no alternative but to reset their cross-signing
keys; however under the terms of the current spec the server MUST require the
user to reauthenticate.

Rather than continue a series of MSCs making small changes to the
reauthentication requirements, we propose to make this
implementation-dependent, and instead provide recommendations to homeserver
implementers.

## Proposal

Replace the current UIAA requirement for [`POST
/_matrix/client/v3/keys/device_signing/upload`] with the following text:

> Servers MAY require that clients reauthenticate themselves via the
> User-Interactive Authentication API.

Also, provide an informational box with text similar to the following:

> Implementers should be mindful that replacing cross-signing keys is a
> powerful attack vector, and should default to requiring a client to
> re-authenticate rather than allowing a client with only an access token to
> replace the keys.
>
> It will normally be appropriate to skip reauthentication if the user has no
> existing master signing key. It may also be appropriate to relax the
> requirement if the user has no alternative: for example, if they have no
> other devices, and have not set up server-side secret storage.
>
> When deciding whether to skip reauthentication, implementers should take
> care that the conditions they check cannot be satisfied by an attacker who
> holds only an access token. For example, the account data describing
> server-side secret storage can be deleted without reauthentication, so a
> server might instead check whether secret storage has *ever* been
> configured.

## Potential issues

 * The main issue foreseen is that further relaxing the reauthentication
   requirements could lower the bar for an eavesdropper to access encrypted
   messages. See [Security considerations](#security-considerations) for
   further discussion.

 * Making the reauthentication requirement an implementation detail increases
   the risk of new server implementations providing inaccurate or inappropriate
   security.

 * It is likely that there will be inconsistencies between servers: some will
   reauthenticate more often than others. This could make it hard to implement
   a smooth user experience on the client side, since the client won't know in
   advance exactly what the server will choose to do.

   Indeed, client implementations may create a user experience that makes
   invalid assumptions about how the server will behave. In the worst case, a
   client implementer may not even realise that reauthentication can sometimes
   be required: there is therefore a risk of incompatibility between some
   client and server implementations.

## Alternatives

### Drop the reauthentication requirement altogether

One possibility is to drop the requirement for reauthentication on `POST
/_matrix/client/v3/keys/device_signing/upload` altogether -- particularly if
paired with a spec change that explicitly prohibits changing the device keys on
an existing device and server-side changes to enforce this.

The intended purpose of the check is to guard against an attacker who has stolen
an access token but does not know the account password (or, in a hardened
OAuth2 environment, lacks a 2FA token).

However, once an attacker successfully replaces the cross-signing keys for a
user, they must then upload signed device keys that they control. In practice,
it is not possible to replace the keys on an existing device
(see
[matrix-spec#2442](https://github.com/matrix-org/matrix-spec/issues/2442)), so
the only avenue available to the attacker is to create a *new* device -- which
itself will require authentication via the Authentication Server.

The wording proposed in this MSC would of course allow implementations to skip
reauthentication if they so chose.

### Do nothing

Doing nothing means that users have a suboptimal experience (see
https://github.com/element-hq/element-meta/issues/3372, for example).

### Make the changed reauthentication requirements explicit

Instead of leaving the reauthentication requirements as an implementation
decision, we could spell out a modified set of precise conditions under which a
server should perform a reauthentication.

Our experience shows that it is hard to come up with a one-size-fits-all
specification, and any such specification would likely be subject to even more
modifications in future.

## Security considerations

The reauthentication requirement on `POST
/_matrix/client/v3/keys/device_signing/upload` exists to defend against a
specific threat: an attacker who has obtained a user's access token, but who
does not have the user's password (or other credentials needed to complete
reauthentication). This proposal does not change that threat model, but it does
allow servers to skip that defence in more situations. The following points
are relevant.

### The reauthentication check is a server-side policy

Reauthentication is enforced by the homeserver, for the benefit of the user. It
provides no protection against a malicious or compromised homeserver, which can
already serve arbitrary cross-signing keys to other users. This proposal makes
no change to the power of a malicious server.

### Conditions for relaxation must not be attacker-controllable

Where a server chooses to skip reauthentication based on the state of the
user's account, it is important that the attacker under consideration (one
holding only an access token) cannot manipulate that state to satisfy the
conditions.

For example, the informational text above suggests that it may be appropriate
to skip reauthentication if the user has not set up server-side secret
storage. However, the account data which describes secret storage (such as
`m.secret_storage.default_key` and the `m.secret_storage.key.*` events) can be
modified or removed by any client holding an access token, without
reauthentication. A naive implementation which checks only for the presence of
this account data could therefore be trivially bypassed: the attacker deletes
the account data, then replaces the cross-signing keys.

Implementations should consider such risks when designing their heuristics:
for example, by tracking whether secret storage has *ever* been configured
rather than whether it is currently configured, or by requiring
reauthentication if the relevant state has changed recently.

### Replacing the cross-signing keys is not, on its own, sufficient for an attack

As discussed under [Drop the reauthentication requirement
altogether](#drop-the-reauthentication-requirement-altogether), an attacker who
replaces a user's cross-signing keys must still sign a device whose keys they
control in order to decrypt messages. This significantly limits the impact of
relaxing the reauthentication requirement.

### Changes in identity are visible

A change to a user's cross-signing keys is visible both to the user's own
existing devices and to other users who share encrypted rooms with them. Many
clients warn users when the identity of a contact that they have previously
seen changes, and clients which follow the recommendations of
[MSC4153](https://github.com/matrix-org/matrix-spec-proposals/pull/4153) will
refuse to send encrypted messages to devices which are not cross-signed by
the user's current identity. A successful attack therefore has a good chance of
being noticed, even if reauthentication is skipped.

### Default behaviour

Because the proposed spec text makes reauthentication optional, a naive new
server implementation might omit it entirely. The informational text
recommends that servers default to requiring reauthentication when an existing
master key is present, and only relax that requirement in specific,
carefully-considered circumstances. Server implementers should treat that
recommendation as the secure baseline.

## Unstable prefix

None required.

## Dependencies

None
