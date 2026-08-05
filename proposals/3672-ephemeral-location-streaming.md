# MSC3672 - Sharing ephemeral streams of location data

## Problem

[MSC3489](https://github.com/matrix-org/matrix-doc/pull/3489)
focuses on streaming persistent location data for applications that require
historical knowledge.

While that's perfect for situations in which long term storage of the data is a
non-issue and implied (e.g. flight paths, strava style exercises, fleet
tracking), there are also cases in doing so is undesirable for either privacy
or performance reasons.

Sharing user live location updates is one of the cases in which privacy is
paramount and where we need the ability to share data in a safe and
non-persistent fashion.

## Proposal

This MSC adds the ability to publish short-lived location beacons through
the use of Ephemeral Data Units (EDUs). It is almost identical to MSC3489,
apart from this change.

Ephemeral data units (EDUs) are Matrix's default mechanism for broadcasting
short-lived data to a group of users. They are intended to be
non-persistent, not take part in a room's history and are currently used
for typing notifications, event receipts, and presence updates.

To allow the use of EDUs for live location sharing, this MSC depends on
[MSC2477](https://github.com/matrix-org/matrix-spec-proposals/pull/2477/)
for user-defined EDUs, and
[MSC3673](https://github.com/matrix-org/matrix-spec-proposals/pull/3673)
for encrypted EDUs.

Clients announce a share, and stop a share exactly as in MSC3489, by
emitting an `m.beacon_info` state event.

Clients share locations by emitting an `m.beacon` event which is identical
to those described in MSC3489, except that it is an EDU (whereas in MSC3489
the events are PDUs).

All other behaviour is the same as in MSC3489. The only difference is that
`m.beacon` events are EDUs.

### Delivery guarantees

MSC2477 specifically avoids defining delivery guarantees for user-defined EDUs,
so we avoid making hard recommendations here. We expect that future MSCs will
clarify the available options. When that happens, clients should choose the
available option that suits their use case, which we expect will be broadly in
line with the following paragraph.

Servers should attempt to deliver `m.beacon` EDUs to all clients, and delete
them as soon as possible. Servers should implement a timeout mechanism to ensure
they are always deleted, even if undelivered. For the expected use cases, we
suggest 30 minutes would be a suitable timeout.

## Security considerations

The security considerations are identical to MSC3489, except that EDUs
provide a better privacy situation because they are not persisted long-term.

## Alternatives

Alternatively, we could negotiate a WebRTC data channel using
[MSC3401](https://github.com/matrix-org/matrix-doc/pull/3401)
and stream low-latency geospatial data over the participating devices in the
room. However it would be useful to support plain HTTP like the rest of Matrix
and requiring a WebRTC stack is prohibitively complicated for simple clients
(e.g. basic IOT devices reporting spatial telemetry).

Another alternative is to use to-device events but that comes with disadvantages
of its own as they're 1:1, single message per transaction and not intended for
conversational data.

## Dependencies

This proposal relies on the following MSCs:

* [MSC2477: User-defined ephemeral events in rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/2477)
* [MSC3673: Encrypted ephemeral data units](https://github.com/matrix-org/matrix-spec-proposals/pull/3673)
* [MSC3489: Sharing streams of location data with history](https://github.com/matrix-org/matrix-spec-proposals/pull/3489)

For live location shares to work in appservices, these MSCs will also be
required:

* [MSC2409: Proposal to send EDUs to appservices](https://github.com/matrix-org/matrix-spec-proposals/pull/2409)
* [MSC3202: Encrypted appservices](https://github.com/matrix-org/matrix-spec-proposals/pull/3202)

## Unstable prefix

This MSC uses the same unstable prefixes as
[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489).

Note that MSC3489 actually uses prefixes that match this MSC's numbering.
This is an historical artifact of the various revision histories of these
proposals.
