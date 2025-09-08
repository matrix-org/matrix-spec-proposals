# MSC4225: Specification of an order in which one-time-keys should be issued

The specification for the
[`/keys/claim`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3keysclaim)
endpoint does not specify any particular order in which one-time keys (OTKs)
should be returned, leading to the possibility that old keys can remain on the
server a long time. Clients may discard the private parts of such old keys,
leading to [unable-to-decrypt
errors](https://github.com/element-hq/element-meta/issues/2356).

See the Appendix below for a more detailed discussion of the problem.

## Proposal

[`/_matrix/client/v3/keys/claim`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3keysclaim)
and [`/_matrix/federation/v1/user/keys/claim`](https://spec.matrix.org/v1.12/server-server-api/#post_matrixfederationv1userkeysclaim)
should return one-time keys in the order that they were uploaded via
[`/keys/upload`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3keysupload). All
keys uploaded in a given call to `/keys/upload` are considered equivalent in
this regard; no ordering is specified within them.

This means that the server will retain only the most recently-uploaded one-time
keys, therefore significantly reducing the chance that clients will discard
private one-time keys that are later used.

### Implementation note

When servers first implement this proposal, they may still have old one-time
keys in their datastore, and this may take many years to resolve.

It is suggested that one solution to this is, as a one-time job, to drop all
one-time keys older than, say, a week, from the database. Having done so,
clients will upload new one-time keys as soon as they come online; in the
meantime, fallback keys are available to allow conversation to continue.

Servers might consider applying further heuristics: for example, keys produced
by libolm are far more likely to have been dropped by the client than those
produced by Vodozemac, because libolm only retained 100 keys, whereas Vodozemac
retains 5000. The two can be identified by the different lengths of key ID they
produce (6 characters vs 11 characters).

## Potential issues

This proposal is not a complete solution to the problem of premature discarding
of one-time keys: even if the server issues a recent one-time key, it is still
possible for a to-device message to be delayed so long that the recipient has
discarded the private part of the one-time key. It is, however, a significant
improvement. A possible future solution is for clients that expect to be used
in conditions of poor connectivity to keep old OTKs for longer.

There are other ways in which the server and client can get out of sync with
respect to one-time keys, including by a [database
rollback](https://github.com/element-hq/element-meta/issues/2155), or
implementation defects. It is anticipated that other solutions will be found
for those situations.

## Alternatives

1. Mandate that clients keep the private parts of all uploaded but unused OTKs
   indefinitely.

   Given that each one-time key is only 32 bytes (plus the ID, say 8 bytes), it
   would certainly be possible for a client implementation to hold a very large
   number of private OTKs without significant concerns about resource usage. In
   particular, a OTK is much smaller than a Megolm key, and there is no limit
   to the number of Megolm keys that a client has to retain.

   In short though, this just seems inefficient, compared to specifying that
   OTKs should be issued in upload order.

2. [MSC4162](https://github.com/matrix-org/matrix-spec-proposals/pull/4162)
   proposes a mechanism by which a client can inform the server that it is
   discarding certain OTKs, so that the server can also remove the public
   keys. This seems a heavier-weight solution to the problem.

3. A more invasive alternative would be to design an encryption stack which
   does not rely on one-time keys. Setting aside whether the security
   properties of such a protocol would be sufficient, this is considered well
   out-of-scope for this proposal.

## Security considerations

Requiring keys to be allocated in upload order might leak information about the
user's traffic level, since key IDs are typically allocated sequentially: if I
issue two claims for Alice's OTKs a week apart, and I get sequential key IDs, I
know that nobody else has opened a conversation with her in that time.

To mitigate this, we might consider having clients create key IDs
non-sequentially (whilst remaining unique). This is considered out-of-scope for
this MSC.

## Unstable prefix

None required.

## Dependencies

None.

## Appendix: detailed explanation of the failure mode

### Background

End-to-end encryption in Matrix relies on individual devices sharing
[Megolm](https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md)
message keys via [to-device
messages](https://spec.matrix.org/v1.12/client-server-api/#send-to-device-messaging)
which are themselves encrypted using the
[Olm](https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/olm.md)
ratchet.

Suppose Alice wishes to send an Olm-encrypted message to Bob (with whom she
has not previously established an Olm session). When Bob logged in, his device
will have created a long-term identity key, as well as a number (typically 50)
of one-time keys. Each of these keys has a private part, which Bob's device
retains locally, and a public part, which Bob's device publishes to his
homeserver via the
[`/keys/upload`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3keysupload) endpoint.

Now, to establish an Olm session, Alice needs to claim one of Bob's one-time
keys. She does this by calling the
[`/keys/claim`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3keysclaim)
endpoint. Together with Bob's identity key, this allows Alice to encrypt a
message that only Bob will be able to decrypt.

Over time, Bob's supply of one-time keys will be depleted. The `/sync` endpoint
informs clients how many one-time keys remain unclaimed on the server, so that
it can generate new ones when required.

See [One-time and fallback
keys](https://spec.matrix.org/v1.12/client-server-api/#one-time-and-fallback-keys)
which specifies much of this behaviour.

### Problem

Clearly, a device must retain the private part of each one-time key until that
key is used to establish an Olm session. However, for a number of reasons,
ranging from network errors to malicious activity, it is possible for a claimed
one-time key never to be used to establish an Olm session.

This presents a problem: there is a limit to the number of private one-time
keys that a client can retain. Over time, as keys are repeatedly claimed,
replaced with newly-generated keys, but not actually used, the client must
start to discard older keys.

Unfortunately, the Matrix specification does not currently specify any order in
which keys should be returned by `/keys/claim`. This means that homeservers can
legitimately issue one-time keys effectively at random. Over time, then, it is
easy to get into a situation where the server still holds some very old
one-time keys, for which the client has discarded the private parts.

Suppose, when Alice claims one of Bob's one-time keys, she is issued one whose
private part Bob has discarded. Then, Bob will be unable to decrypt the Olm
message from Alice, and (assuming the Olm message contained Megolm keys), will
be unable to decrypt any room messages that Alice sends.
