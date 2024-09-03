# Remove prev_content from the essential keys list

Matrix supports the concept of event redaction. The ability to redact rather
than delete is necessary because some events e.g. membership events are
essential to the protocol and _cannot_ be deleted. Therefore we do not delete
events outright and instead redact them. This involves removing all keys from
an event that are not required by the protocol. The stripped down event is
thereafter returned anytime a client or remote server requests it.


## Proposal

[The redaction algorithm](https://matrix.org/docs/spec/client_server/r0.4.0.html#redactions)
defines which keys must be retained through a redaction. Currently it lists
```prev_content``` as a key to retain, though in practice there is no need to
do so at the protocol level.

The proposal is simply to remove ```prev_content``` from the essential keys
list.

Note: the inclusion of ```prev_content``` in the essential keys list was
unintentional and should be considered a spec bug. Synapse (and other server
implementations) have not implemented the bug and already omit
```prev_content``` from redacted events.


## Tradeoffs

When sending events over federation the events are [hashed and
signed](https://matrix.org/docs/spec/server_server/r0.1.0#adding-hashes-and-signatures-to-outgoing-events),
this involves operating not only on the original event but also the redacted
form of the event. The redacted hash and redacted signed event are necessary if
the event is ever redacted in future. As a result, any change of the essential
keys list must be managed carefully. If disparate servers implement different
versions of the redaction algorithm (for a given event) attempts to send the
event over federation will fail.

We _could_ manage this change via room versioning and create a new room
version that implements this MSC. However, because the federation already
omits the ```prev_content``` key by convention, implementing this MSC only in
the new room version would mean that the entire existing federation would not
be spec compliant.

As a result it seems pragmatic to have the spec reflect reality, acknowledge
that the spec and federation have deviated and instead update the spec
retrospectively to describe the de-facto redaction algorithm.

## Potential issues

It is theoretically possible that a closed federation could exist whose servers
do follow the spec as is. This MSC would render those servers non-compliant with
the spec. On balance this seems unlikely and in the worst case those
implementors could add the change to a subsequent room version, eventually
reaching spec consistency as older room versions are deprecated.

Another scenario is that a client may redact events according to the spec as is
and persist prev_content through the redaction, thereby diverting from that on
the server(s). Client authors will have to update their code to drop
```prev_content``` - however, given that prev_content should not be used in
important calculations and/or visualisations, this ought to be a relatively
non-invasive change.


## Security considerations

A further reason to support removal of ```prev_content``` is the case where a
malicious user adds illegal or abusive content into a state event and then
overwrites that state event. The content would then be preserved through the
redaction.

Additionally, there are plenty of reasons to have security concerns over a
precedent that the federation can deviate from the spec.

## Conclusions
Removing ```prev_content``` is pragmatic response to the current situation. It
aligns the federation and the spec, and does so in a way that removes
unnecessary overhead.
