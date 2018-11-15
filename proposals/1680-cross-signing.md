Cross-signing devices
=====================

Problem/Background
------------------
A user with multiple devices will have a different key for end-to-end
encryption for each device.  Other users who want to communicate securely with
this user must then verify each key on each of their devices.  If Alice has *n*
devices, and Bob has *m* devices, then for Alice to be able to communicate with
Bob on any of their devices, this involves *n×m* key verifications.

One way in which key verification has historically been addressed is through a
web-of-trust system: if Alice trusts Bob, and Bob trusts Carol, then Alice may
trust Carol even though Alice is unable to verify Carol's key directly.
Cross-signing can be seen as a limited web-of-trust, in which one device can
vouch for another device that belongs to the same user.  For example if Alice
has an Osborne 2 and a PDP-11, and Bob has a Dynabook and a VAX, then Alice can
verify her Osborne 2 with her PDP-11 (and vice versa), and Bob can verify his
Dynabook with his VAX (and vice versa).  When Alice and Bob meet in person,
Alice's Osborne 2 can verify Bob's Dynabook (and vice versa).  These
verifications can be published, which will allow Alice's PDP-11 to trust Bob's
VAX (and vice versa) without having them directly verify each other, or even
without the PDP-11 having to directly verify any of Bob's devices, or any of
Alice's devices having to directly verify Bob's VAX.

See also:

- https://github.com/vector-im/riot-web/issues/2714

Proposal
--------

When one device verifies another device, it will publish an attestation (in the
form of a [signed JSON
object](https://matrix.org/docs/spec/appendices.html#signing-json)) indicating
this. Attestations can also be revoked by publishing another signed JSON
object. Other devices can use these attestations to trust other devices that
have not been directly verified.  Users will only be able to see attestations
and revocations made by their own devices, or attestations and revocations made
between devices belonging to the same user.  That is, Alice can see
attestations made by her own devices, or attestations made by Bob's devices
about Bob's devices, but she cannot see attestations made by Carol's devices
about Bob's devices, attestations made by Bob's devices about Carol's devices,
nor attestations made by Bob nor Carol about Alice's devices.

Attestations and revocations are published by using the `POST
/_matrix/client/r0/keys/upload` endpoint and are retrieved by using the `POST
/_matrix/client/r0/keys/query` endpoint.  When new attestations or revocations
are published, then the user who owns the device that the attestation is about
will be included in the `changed` array in the `device_lists` property of the
`/sync` response for all users that share a room with that user.

Attestations form a directed graph (not necessarily acyclic) in which edges go
from the device making the attestation to the device that the attestation is
about, as long as the signature is valid, the data in the data in the
attestation matches the device key, and there is no corresponding
revocation. If Device A can construct a directed path in this graph starting
from a device it has verified and ending at Device B, consisting only of
devices owned by either Device A's owner or Device B's owner, then it may treat
Device B as trusted. Device A may do so automatically, or after prompting the
user, or may allow the user to disable this functionality completely.

TODO: should Device A then publish an attestation for Device B?

### API

#### Additions to `POST /_matrix/client/r0/keys/upload`

This proposal will add an additional property to the request body of the [`POST
/_matrix/client/r0/keys/upload`](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-keys-upload)
endpoint:

- `attestations` (`[Attestation]` (see below)): The attestations or revocations
  to be published.  Attestations that do not come from the user calling the
  endpoint MUST be discarded.

#### Additions to `POST /_matrix/client/r0/keys/query`

This proposal will add an additional property to the `DeviceKeys` type, for the `device_keys` return
parameter in the [`POST
/_matrix/client/r0/keys/query`](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-keys-query)
endpoint:

- `attestations` (`[Attestation]` (see below)): The published attestations or
  revocations for the device.  This array MUST only include the attestations or
  revocations made by devices belonging to the user calling the endpoint, or
  made by devices belonging to the owner of the device being queried.  For
  example, when Alice calls this endpoint to fetch information about Bob's
  devices, this array will only include attestations or revocations made by
  Alice's devices or by Bob's other devices.

TODO: `keys/query` may need to include devices that have been logged out, in
order to avoid unexpectedly breaking trust chains, so we may want to recommend
that devices remain in the result for *n* days after they log out?  However, we
don't want to other devices to continue to encrypt for that device, so maybe
add a flag saying that it's stale, or put stale devices in a separate parameter
(`stale_device_keys` instead of `device_keys`)?

#### `Attestation` type

Properties:

- `user_id` (string): Required. The ID of the user whose device has been verified
- `device_id` (string): Required. The ID of the device that has been verified.
- `keys` ({string: string}): Required. The public identity keys that have been
  verified. This will normally just be the signing key (e.g. the ed25519 key).
- `state` (string): Required. The verification state. One of "verified" or
  "revoked".
- `signatures` (object): signatures of the above properties.

#### Additions to extensions to /sync

The End-to-End encryption module defines [extensions to
`/sync`](https://matrix.org/docs/spec/client_server/r0.4.0.html#device-lists-sync).
This proposal will change the description of the `changed` parameter in the
`DeviceLists` type defined in those extensions to read:

> List of users who have updated their device identity keys, or who now share
> an encrypted room with the client, or who have received additional
> attestations or revocations since the previous sync response.

TODO: S2S stuff

Tradeoffs
---------

Security Considerations
-----------------------

If an attacker gains access to a device, then they can send revocations for all
of the user's other devices, causing it to seem like the device controlled by
the attacker is the only valid device.  For this reason, revocations should be
treated with caution, and may require manual intervention to sort out.

TODO: we probably need to spell out in more detail how revocations should be
handled.

Other Issues
------------

Conclusion
----------
