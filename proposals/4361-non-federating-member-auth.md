# MSC4361: Non-federating Membership Authorization Rules

Specification version 1.16. Room Version 12<sup>*</sup> § 2.2 (4)<sup>[1]</sup> is the sole clause within the Authorization Rules conditioned on the `m.federate` property. The `m.federate` property is an immutable declaration within the `m.room.create` event which isolates a room to a specific origin<sup>†</sup>. The sole condition to achieve a non-federating room is to deny events with a `sender` from a remote server.

This method has several leakages. The "target" of an `m.room.member` event declared by its `state_key` is allowed to be a remote user. Compliant servers will both create, transmit<sup>‡</sup> and accept such an event, only to find later it cannot be further acted upon. This specification change aims to correct this leakage and subsequent ⊥ by amending Rule `5. If type is m.room.member` prepending a new sub-rule `1. If the content of the m.room.create event in the room state has the property m.federate set to false, and the state_key domain of the event does not match the sender domain of the create event, reject.` shifting-up existing rules.

## Alternatives

Synapse has been observed in at least some cases to preclude the transmission and/or reception of events for non-federating rooms "manually." These restrictions are specified external to the authorization rules in some other places. This approach denudes the significance of authorization rules. One could ask: why specify _anything_ as authorization rules? This is the question a proponent of the status quo must bear.

## Security Considerations

While this proposal clearly increases security by reducing cross-origin leakage of events, the addition of any new restrictions is a theoretical Denial of Service vector which must be scrutinized during review. No such possibility is known to the author.

## Potential Issues

A new room version may be required. However, this author believes it is technically possible to backport this change to all prior room versions without any alteration to nominal correctness; leaked events would simply enter a failure state or remain ⊥.

---

[1]: https://spec.matrix.org/v1.16/rooms/v12/#authorization-rules

<sup><b>Special thanks to Dasha for assisting in the research for this proposal.</b></sup>

<sup>* In addition to all earlier stable room versions.</sup>

<sup>† Server or cluster sharing the same domain.</sup>

<sup>‡ Synapse has been observed to impose certain restrictions external to the auth-rules. See: Alternatives for discussion.</sup>
