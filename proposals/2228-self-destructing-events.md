# Proposal for self-destructing messages

It's useful for users to be able to send sensitive messages within a
conversation which should be removed after the target user(s) has read them.
This can be achieved today by the sender redacting the message after the
receipient(s) have read them, but this is a tedious manual process. This
proposal provides a way of automating this process.

Originally [MSC1763](https://github.com/matrix-org/matrix-doc/pull/1763)
attempted to solve this by applying retention limits on a per-message basis
and purging expired messages from the server; in practice this approach is
flawed because purging messages fragments the DAG, breaking back-pagination
and potentially causing performance problems.  Also, the ability to set an
expiration timestamp relative to the send (rather than read) time is not of
obvious value.  Therefore the concept of self-destructing messsages was 
split out into this independent proposal.

## Proposal

Users can specify that a message should self-destruct by adding the following
field to any event's content:

`m.self_destruct`:
  the duration in milliseconds after which the participating servers should
  redact this event on behalf of the sender, after seeing an explicit read
  receipt delivered for the message from all users in the room. Must be null
  or an integer in range [0, 2<sup>31</sup>-1]. If absent, or null, this
  behaviour does not take effect.

Clients and servers MUST send explicit read receipts per-message for
self-destructing messages (rather than for the most recently read message,
as is the normal operation), so that messages can be destructed as requested.

The `m.self_destruct` field is not preserved over redaction (and
self-destructing messages may be redacted to speed up the self-destruct
process if desired).

E2E encrypted messages must store the `m.self_destruct` field outside of the
encrypted contents of the message, given the server needs to be able to act on
it.

## Server-side behaviour

When a client sends a message with `m.self_destruct` true, the servers
participating in a room should start monitoring the room for read receipts for
the event in question. Once a given server has received read receipts for this
message from all members in the room (other than the sender), then the server
should redact the event, and send a synthetic `m.redaction` event to the
clients in the room on behalf of the sender.

## Client-side behaviour

Clients should display self-destructing events in a clearly distinguished
manner in the timeline.  Details of the lifespan can be shown on demand
however, although a visible countdown is recommended.

Clients should locally remove self-destructing events as if they have been
redacted N milliseconds after first attempting to send the read receipt for the
message in question.  The synthetic redaction event sent by the local server
then acts as a fallback for clients which fail to implement special UI for
self-destructing messages.

## Tradeoffs

We could purge rather than redact destructed messages from the DB, but that
would fragment the DAG so we don't do that.

We could have the sending server send an explicit redaction event on behalf of
the sender rather than synthesise a redaction on the various participating
servers.  However, this would clog up the DAG with a redundant event, and also
introduce unreliability if the sending server is unavailable or delayed. 
Therefore synthetic redaction events (which are only for backwards compatibility
anyway) feel like the lesser evil.

## Issues

We should probably ignore missing read receipts from bots when deciding
whether to self_destruct.  This is blocked on having a good way to identify
bots.

Should we even bother sending a redaction, versus just having all the servers
behave as if a redaction has been received?

## Security considerations

There's scope for abuse where users can send obnoxious self-destructing messages
into a room.

One solution for this could be for server implementations to implement a
quarantine mode which initially marks redacted events as quarantined for N days
before deleting them entirely, allowing server admins to address abuse concerns.
This is of course true for redactions in general.

## Conclusion

This provides a simple and pragmatic way of automating the process of manually
redacting sensitive messages once the recipients have read them.