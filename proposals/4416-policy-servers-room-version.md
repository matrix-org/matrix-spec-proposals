# MSC4416: Optionally requiring policy server signatures in a room

[MSC4284 (proposed-FCP)](https://github.com/matrix-org/matrix-spec-proposals/pull/4284) introduces a
concept of Policy Servers to Matrix. These servers produce recommendations on events attempting to be
sent to a room, and lead to events being [soft failed](https://spec.matrix.org/v1.17/server-server-api/#soft-failure)
if the policy server refuses to sign it.

Not all homeservers will be aware of policy servers though. Noted in MSC4284, this can lead to higher
traffic for the policy server to handle or accepting events that other homeservers have soft failed.

This proposal changes the [auth rules](https://spec.matrix.org/v1.17/rooms/v12/#authorization-rules),
[auth event selection algorithm](https://spec.matrix.org/v1.17/server-server-api/#auth-events-selection),
and [redaction algorithm](https://spec.matrix.org/v1.17/rooms/v12/#redactions) in a new room version.
These changes collectively ensure that the room's choice to use a policy server is reflected by all
homeservers in that room.

**Note**: Nothing in this proposal requires that a room use a policy server. If a room does decide
to use a policy server though, the room version changes in this proposal will reinforce that choice.
Rooms are still free to disable or never use a policy server whenever they want.

**Note**: At the time of writing [Room Version 12](https://spec.matrix.org/v1.17/rooms/v12) is the
latest room version available. This proposal uses v12 as a base room version for ease of reference,
but the concepts/changes can apply to future room versions as well.


## Proposal

This proposal makes breaking changes to how the auth rules and redaction algorithm work, and therefore
requires a new room version.

### Changes: Auth rules

Reference: [Current auth rules](https://spec.matrix.org/v1.17/rooms/v12/#authorization-rules)

Rule 3.2 (auth events selection) is clarified to make it clear that the `m.room.policy` state event
with empty state key *MUST* be selected in this room version, if present in the room.

A new rule is inserted between auth rule 4 (`m.federate` handling) and rule 5 (`m.room.member` tree)
which reads:

5. Considering the room's `m.room.policy` state event with empty state key (the "policy event"):

   1. If the event being authorized is an `m.room.policy` state event with empty state key, skip the
      remainder of rule 5. **Note**: non-empty state keys or non-state `m.room.policy` events are
      still checked by rule 5.
   2. If the room does not have a policy event set, skip the remainder of rule 5.
   3. If the room's policy event has a non-string or undefined `content.via` field, skip the remainder
      of rule 5.
   4. If the room's policy event does not list at least one [supported signing algorithm](https://spec.matrix.org/v1.17/appendices/#signing-details)
      under `content.public_keys`, skip the remainder of rule 5.
   5. If the room does not have a *joined* user belonging to the server denoted by the policy event's
      `content.via`, skip the remainder of rule 5.
   6. Using `policy_server` as the key version, if the event being authorized is not validly signed
      by at least one of the policy event's `content.public_keys` and `content.via` server name, reject.
      **Note**: for the ed25519 key algorithm, the key ID would be `ed25519:policy_server`.
      **Note**: rule 5.4 above effectively requires servers to support `ed25519`.

This new rule has the following desirable effects:

* Rooms without a policy server set up are not affected by the concept of a policy server. This extends
  to improperly-created events (non-string `via`), undefined fields (missing `public_keys`), and the
  policy server not having a local joined user. These are the same conditions as in MSC4284. This is
  largely achieved by "skipping" the new rule and allowing the other auth rules to execute normally.

* The policy server's signature is *required* on an event when the policy server is valid. This is
  unlike MSC4284, where lack of signature leads to soft failure instead.

* `m.room.member` events are checked by the policy server by inserting the new rule ahead of that rule.

* Instead of performing a bunch of signature/policy server checks only to find out the room is set to
  `m.federate: false`, the new rule is inserted immediately after that rule.

* Making policy server signatures *required* when a policy server is configured, homeservers *MUST*
  acquire that signature from the policy server. They were already supposed to under MSC4284, but now
  it's enforced under the auth rules too.

* Due to the [checks performed when receiving a PDU](https://spec.matrix.org/v1.17/server-server-api/#checks-performed-on-receipt-of-a-pdu),
  if the policy server's key(s) are rotated then an event might be valid at the time the event was
  sent but not valid under "current state", leading to the event being soft failed. This still prevents
  events from making it down to clients even if the key were to be compromised.

  This mechanism can also be used to ensure that old events conform to modern policy, which is also
  desirable. For example, when an old event sent at a time where a policy server wasn't in place is
  received when a policy server is now part of "current state" - the policy server's signature is
  checked and can lead to soft failure if not present.

**Note**: Policy servers might not be aware of the DAG and therefore sign events which are otherwise
invalid under the auth rules. For example, a policy server might add a signature to an event where
the sender isn't joined to the room, breaking what is currently rule 6. The presence of a signature
does *not* override the auth rules which follow the new rule - the new rule falls through to the
remaining rules.

### Changes: Auth events selection

Reference: [Current auth events selection algorithm](https://spec.matrix.org/v1.17/server-server-api/#auth-events-selection)

To support the auth rule changes above, the auth events selection algorithm appends the following:

* Depending on the room version, the `m.room.policy` state event, if any.

This MSC's new room version activates that clause by updating auth rule 3.2 above.

### Changes: Redaction algorithm

Reference: [Current redaction algorithm](https://spec.matrix.org/v1.17/rooms/v12/#redactions)

To ensure the auth rule changes above are stable through redaction, the `m.room.policy` event type
allows the `via` and `public_keys` (including all subkeys) keys in `content`.

### Changes: Homeserver behaviour

MSC4284 says "If the [policy server's] signature is plainly missing, the homeserver SHOULD call `/sign`
on the policy server and use that result to determine whether to pass the event through unimpeded or
soft fail it.". This recommendation is changed to be a SHOULD NOT in this proposal's new room version.
Removing the recommendation to acquire a signature when processing a received event which is missing
it encourages homeservers to get that signature themselves or face rejection under the new auth rules
above.


## Potential issues

This proposal inherits many of the potential issues of MSC4284. Issues relating to homeservers "not
knowing" about policy servers are resolved however due to those homeservers needing to be aware of
this proposal's new auth rules to participate in rooms which use them.

Issues relating to redaction of the `m.room.policy` state event are also resolved by this proposal
adjusting the redaction algorithm accordingly.


## Alternatives

This proposal also implicitly inherits alternatives from MSC4284. Specifically, it might be desirable
to support multiple policy servers in a room. This proposal defers figuring out how that would work
to a future MSC for the reasons outlined in MSC4284.


## Security considerations

Further, this proposal inherits security considerations from MSC4284. Policy servers are still natural
DoS targets, and homeservers could request signatures but wait to use them for a while. Some of the
risk in MSC4284's security considerations is mitigated by causing events to become rejected rather
than soft failed in some cases.


## Safety considerations

All safety considerations are inherited from MSC4284 verbatim.


## Unstable prefix

This proposal's functionality will exist in an unstable room version until another MSC can assign it
to a stable room version. This is normal process for the specification. See [MSC4304 (merged)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4304-room-version-12.md)
for an example of this process.

Implementations should use `org.matrix.msc4416.v1` as an unstable room version using v12 as a base
until this MSC can be adopted into a stable room version.


## Dependencies

This proposal depends on [MSC4284: Policy Servers](https://github.com/matrix-org/matrix-spec-proposals/pull/4284).

This proposal is targeting inclusion in room version 13, but can be deferred to a future room version
as required.
