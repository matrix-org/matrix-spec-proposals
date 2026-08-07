# MSC4117: Reinstating Events (Reversible Redactions)

Under the UK's Online Safety Bill and similar upcoming legislation in the EU, US, and Canada, users
who have action taken against their accounts *must* be provided an option to appeal that action and
undo consequences if successful. In the context of Matrix, this means when a room moderator or server
admin redacts a user's messages, the affected user must be able to "unredact" those messages with
successful appeal.

When a redaction is applied in Matrix, servers and clients both remove [protocol-insignificant](https://spec.matrix.org/v1.9/rooms/v11/#redactions)
information from the target event forever. Some server implementations retain the redacted fields for
a short time within their database, but flag that the event should be redacted when served to clients
or other servers. This is primarily for safety and platform security reasons, where server admins may
need to review content after a room moderator has cleaned it up already, for example.

Redactions are a permanent and unrecoverable alteration to the room history under this design, which
is clearly incompatible with above-mentioned (upcoming) legal requirements of server operators. This
proposal allows servers to "reinstate" events after they've been redacted to cover the technical
limitation, though does not create Client-Server API endpoints to invoke this behaviour or manage
appeals. Such functionality is better scoped to another MSC.

## Background

Redactions from room version 3 onwards are not tied to the authorization rules within a room. Instead,
as described [in the spec](https://spec.matrix.org/v1.9/rooms/v3/#handling-redactions), redaction
events are withheld from local clients until both the redaction and target event are received, and
sender of the redaction has permission to affect the target event. Once those conditions are met, the
redaction is applied to remove non-critical data from the event (typically the message content itself).

A related feature in Matrix is the integrity of `content` when sending events over federation. To ensure
that events are not modified, a content hash is calculated, recorded by the origin server, and signed
before the event is accepted by any other server. On the receiving side, the server validates the
content hash and *redacts* the event upon failure before processing it further, as described
[here](https://spec.matrix.org/v1.9/server-server-api/#checks-performed-on-receipt-of-a-pdu) and
[here](https://spec.matrix.org/v1.9/server-server-api/#validating-hashes-and-signatures-on-received-events).

The content hash is protected by the redaction algorithm because it is critical to the protocol's
operation. If the field were to be removed from the event upon redaction, servers would be unable to
validate the signature on the event which could potentially lead to the event being *rejected* when
it was previously accepted. In a worst case scenario, this could cause the majority of the room's
events to also be rejected because events are rejected if they reference rejected events themselves.
Instead, the content hash is protected by redaction to allow `content` itself to lose most/all of its
fields.

## Proposal

We can use the presence of the content hash to reinstate an event's content post-redaction. A new
message event type, `m.room.reinstate`, is introduced with the following shape:


```jsonc
{
  "type": "m.room.reinstate",
  "sender": "@bob:example.org",
  "content": {
    "$event_id_to_be_reinstated": {
      // original event content
    }
  },
  // other fields excluded for brevity
}
```

*Note*: Design considerations for [MSC2244](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2244-mass-redactions.md)
and [MSC4084](https://github.com/matrix-org/matrix-spec-proposals/pull/4084) are implied.

Similar to redactions, the reinstate event is withheld from local clients until the server has all
the information required to validate the event. Those conditions are:

1. The server has received *all* of the target events.
2. For each of the target events, *one* of the following conditions is met (these are the same as
   [redactions](https://spec.matrix.org/v1.9/rooms/v11/#handling-redactions)):
   1. The power level of the *reinstate* event's `sender` is greater than or equal to the *redact level*.
   2. The domain of the *reinstate* event's `sender` matches that of the target event's `sender`.
3. For each of the target event contents, the calculated content hash *must* equal the target event's
   content hash.

If any of the conditions cannot be met, the reinstate event is withheld. Servers *may* wish to
[soft-fail](https://spec.matrix.org/v1.9/server-server-api/#soft-failure) the event if it can never
be satisfied, such as in the case of condition 2 or 3.

Once the conditions are met, the reinstate event is applied to the target events as a virtual layer
similar to [message edits](https://spec.matrix.org/v1.9/client-server-api/#event-replacements). This
is done to allow the reinstate event itself to be redacted, which undoes the reinstation to return
the event back to the previous state.

> **TODO**: Or do we just apply the content directly, making redacting the reinstate event useless?

Note that the reinstate event does not have any fields protected from redaction. Such empty events
affect nothing and so pass the above conditions.

Reinstate and redaction events affect the target event in topological DAG order. That's to say that
if a redaction happens first, reinstate second, and another redaction third, the event will be redacted
in the end. There may be an information leak due to the reinstate event *not* being redacted in that
simplistic scenario, however.

> **TODO**: Do we need to address the leak? Is it sufficient to have clients highlight the redacted
> event to say it's only partially redacted and offer a button to finish the job (redact the reinstate
> event)?

### Client-side application of reinstate events

This proposal has a unique opportunity to avoid needing a net-new room version in order to be released
to the world because it does not modify the operation or behaviour of the room model. This means the
reinstate behaviour described above can be applied in *all* existing room versions, including v1 and
v2 where redactions are special-cased.

However, it can take a while for servers to update to support new mechanics and behaviours. This can
mean that a server which is unaware of `m.room.reinstate`'s special meaning will forward the event
down to clients as though it was any other event -- a desirable feature for most proposals. For this
proposal, such behaviour would be non-ideal as clients would assume the event has been validated and
can therefore apply the new content to their local cached copy. If the reinstate event was maliciously
sent, the room history could be illegally mutated for users on old homeservers.

A new room version could potentially solve the issue, though with the `m.room.reinstate` event holding
no authorization or security purpose within the room model, a room version is hardly justified. Further,
clients may trivially fail to perform a room version check when receiving the event and apply the
changes anyways (though this may be helped by servers soft-failing `m.room.reinstate` events in
unsupported room versions).

Some options to continue avoiding a new room version and not cause undesirable client behaviour are
explored in the following sections.

#### Option 1: Server-resent events

When `/sync`ing, the client *does not* receive the `m.room.reinstate` event. Instead, the clients
receive the reinstated events again with the `content` unredacted.

For example:

1. Client `/sync`s, receives two events:
   * `{"event_id": "$a", "type": "m.room.message", "content": {"body": "hi"}}`
   * `{"event_id": "$b", "type": "m.room.redaction", "content": {"redacts": "$a"}}`
2. The client locally redacts `$a` to have `content: {}`.
3. The server receives event `$c` which reinstates `$a`'s original `content`:
   `{"event_id": "$c", "type": "m.room.reinstate", "content": {"$a": {"body": "hi"}}}`
4. Because we're on a happy path, the event is valid and passes all conditions.
5. Client `/sync`s, receives `$a` with metadata to indicate it has been reinstated. The client does
   not receive the reinstate event, `$c`, directly.
   * `{"event_id": "$a", "type": "m.room.message", "content": {"body": "hi"}, "unsigned": {"reinstated_by": "$c"}}`
6. Client unredacts its local copy of `$a` using the duplicate event.

The client would still receive `$c` during `/messages`, `GET /event`, etc, but does not attach behaviour
to receipt of the event.

Likely, a sync filter flag similar to lazy loading would also be required to opt-in to this duplicate
event behaviour, otherwise the client may get confused about seeing events twice. Clients which fail
to opt-in would either simply not receive the reinstate event (forming a "gap" in the timeline), or
would receive the reinstate event as-is and not be permitted to attach behaviour to the event's receipt.

#### Option 2: Client verifies server support

Assuming `/sync` is unmodified and serves `m.room.reinstate` directly, the client would verify the
server supports this proposal's requirements before reinstating the target events locally. This would
likely be done with a call to `/versions` to check for an unstable/stable feature flag or released
specification version to indicate the server is processing the reinstate event correctly.

If the server does not outwardly show support for reinstate events, the client would not apply the event
and simply ignore it.

It's unclear how a client should handle a server advertising support for reinstantiation after already
receiving a reinstate event, or how the client would verify the reinstate event is valid.

This particular approach has a risk similar to the room version check described earlier in this proposal,
where clients may fail to detect feature support on the server (or in the room) and apply the reinstate
event regardless, leading to a visual security issue for the user.

## Worked examples

### Verbose basic example & test vectors

1. A message is sent in a room:

   `$bjW27hy4RlE6vhfboLMvUr_vxY8Dd7nYKof44nAhEkQ`
   ```json
   {
     "auth_events": [
       "$VPKbOoGaxXQaEsN_IiNvedVvWEXfN8u3uLn0LPMr8Ig",
       "$pN5FOV6ATa3PKgJ9xCNeSBgXaDjxy7plUzM2DHSKLgY",
       "$R6VJDJTanX4fJTmYYL0DPkseZjXeQI2qQpAp9K766xk"
     ],
     "content": {
       "body": "Hello world!",
       "m.mentions": {},
       "msgtype": "m.text"
     },
     "depth": 8,
     "hashes": {
       "sha256": "i3A/7ePt5si1fh+PuAi0oFPEQyOipoOhsGppLvvXDik"
     },
     "origin": "t2l.io",
     "origin_server_ts": 1709587032028,
     "prev_events": [
       "$9S3H3_jwtX7z0tEcvIqEh9VlAdgrIBVAIaT-Cpg0Uok"
     ],
     "room_id": "!bbPGWpTyDYppmybMgi:t2l.io",
     "sender": "@travis:t2l.io",
     "type": "m.room.message",
     "signatures": {
       "t2l.io": {
         "ed25519:a_iRjt": "l0NtAKOjjpjqgI4wy1K/gUSxSZednzw7/7sLalZNdEZ7z/X7jBHXP5I2RZYup1Mkkld27b61Y8RWV7y/Ox30Aw"
       }
     },
     "unsigned": {
       "age_ts": 1709587032028
     }
   }
   ```

2. It is redacted:

   `$1qjgT7LCSjGS3Dfs7VnitlPmpjI175rDfr_nhopLCP8`
   ```json
   {
     "auth_events": [
       "$VPKbOoGaxXQaEsN_IiNvedVvWEXfN8u3uLn0LPMr8Ig",
       "$pN5FOV6ATa3PKgJ9xCNeSBgXaDjxy7plUzM2DHSKLgY",
       "$R6VJDJTanX4fJTmYYL0DPkseZjXeQI2qQpAp9K766xk"
     ],
     "content": {},
     "depth": 9,
     "hashes": {
       "sha256": "WAFAW8aAAHIX5P3zAfQDaBgf1YJKouXKtdErRWuEq6Y"
     },
     "origin": "t2l.io",
     "origin_server_ts": 1709587154240,
     "prev_events": [
       "$bjW27hy4RlE6vhfboLMvUr_vxY8Dd7nYKof44nAhEkQ"
     ],
     "redacts": "$bjW27hy4RlE6vhfboLMvUr_vxY8Dd7nYKof44nAhEkQ",
     "room_id": "!bbPGWpTyDYppmybMgi:t2l.io",
     "sender": "@travis:t2l.io",
     "type": "m.room.redaction",
     "signatures": {
       "t2l.io": {
         "ed25519:a_iRjt": "7ukdLahzeIcWztPR0Ohylbu1cKWa163FfqECupjo9wA+Wtt/cv+vRV8S4juct6KaJ3CCP5kNdxya7IpG/zZjCA"
       }
     },
     "unsigned": {
       "age_ts": 1709587154240
     }
   }
   ```

3. It is reinstated:

   `$5jUO9TBHJ5j1NmrDKHlF3sTjHydYFEICwB3s8Vu3stk`
   ```json
   {
     "auth_events": [
       "$VPKbOoGaxXQaEsN_IiNvedVvWEXfN8u3uLn0LPMr8Ig",
       "$pN5FOV6ATa3PKgJ9xCNeSBgXaDjxy7plUzM2DHSKLgY",
       "$R6VJDJTanX4fJTmYYL0DPkseZjXeQI2qQpAp9K766xk"
     ],
     "content": {
       "$bjW27hy4RlE6vhfboLMvUr_vxY8Dd7nYKof44nAhEkQ": {
         "body": "Hello world!",
         "m.mentions": {},
         "msgtype": "m.text"
       }
     },
     "depth": 10,
     "hashes": {
       "sha256": "KEc6kmVY6mMLEzXHtJztXCxVwTirU3XHKngLuD9AdyE"
     },
     "origin": "t2l.io",
     "origin_server_ts": 1709587447747,
     "prev_events": [
       "$1qjgT7LCSjGS3Dfs7VnitlPmpjI175rDfr_nhopLCP8"
     ],
     "room_id": "!bbPGWpTyDYppmybMgi:t2l.io",
     "sender": "@travis:t2l.io",
     "type": "m.room.reinstate",
     "signatures": {
       "t2l.io": {
         "ed25519:a_iRjt": "aNzbc8auJNTQ9TjyEn/2ztnansDI7O3lmlhSC4SZyXEt36liJ+x+/q50AydbBTvbxu1uGFrzdQvWR6zulbBuDQ"
       }
     },
     "unsigned": {
       "age_ts": 1709587447747
     }
   }
   ```

4. Combining the original (now-redacted) event with the reinstate event's content reveals the same
   content hash, therefore allowing the server and client to use the reinstate event's content.

   > **NOTE**: Except it doesn't match because of `depth` - see Potential Issues section.

### Edge case: Reinstating unredacted events

1. An event is sent.
2. A reinstate event is sent for that event.

There's technically nothing illegal about this, it's just weird. Redacting the reinstate event would
have no effect, though redacting the original event would hide the event contents.

### Edge case: Redaction after reinstating

1. An event is sent.
2. It is redacted.
3. It is reinstated.
4. It is redacted, again.

The target event is redacted at the end of this chain, though the reinstate event is not which may
reveal event contents to the room still. See potential issues for more information.

### Edge case: Redacting the reinstate event

1. An event is sent.
2. It is redacted.
3. It is reinstated.
4. The reinstate event is redacted.

Both the target event and reinstate event are redacted, hiding the message contents.

## Potential issues

This proposal only supports reinstating events based on `content`, though the content hash covers
top-level fields on an event as well. If an event had a custom top-level field, it is not possible
to reinstate it under this proposal. This is done intentionally to avoid specifying a merge strategy
for JSON objects or having total duplication of events inside `m.room.reinstate` events.

> **TODO**: This^ is a massive problem because Synapse populates `depth` on events still, which serves
> no purpose and is an unprotected field. To make this proposal work in all existing room versions,
> and ideally with older events too, this proposal needs to handle top-level fields too.

Large events may not be possible to reinstate due to the overhead of the event ID in the `m.room.reinstate`
`content`, as after signatures and hashes the reinstate event could be over the
[size limits](https://spec.matrix.org/v1.9/client-server-api/#size-limits). This is only expected to
impact an extraordinarily small, but non-zero, number of events.

Discussed earlier in this proposal, if a target event is redacted after being reinstated but the
reinstate event is left unredacted (either because the client doesn't know about it or a race
condition), the contents of the target event are left exposed to the room. See the earlier *TODO* for
solution context.

## Alternatives

[MSC3531](https://github.com/matrix-org/matrix-spec-proposals/pull/3531) approaches the problem space
in a different way, building a holding system before committing to a redaction.

[MSC2815](https://github.com/matrix-org/matrix-spec-proposals/pull/2815) additionally handles concepts
related to this MSC's scope.

## Security considerations

Implied throughout.

> **TODO**: Reiterate here.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4117.room.reinstate`
in place of `m.room.reinstate` throughout.

## Dependencies

This proposal has no direct dependencies.
