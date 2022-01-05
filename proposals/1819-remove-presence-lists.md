# Remove references to presence lists

[Presence](https://matrix.org/docs/spec/client_server/r0.4.0.html#id107) lists
allow a given user the ability to subscribe to other users and be alerted to
their current presence status.

While spec'd, no established client has implemented support and the only server
side implementation raises privacy concerns.

The proposal is to simply remove references to presence lists with a view to
revisiting the same ideas in the future.

This MSC addresses
[#1810](https://github.com/matrix-org/matrix-doc/issues/1810)

## Proposal

Presence lists seem like a good fit for ['MSC1769: Extensible profiles as
rooms'](https://github.com/matrix-org/matrix-doc/pull/1769) proposal, meaning
that the current design will most likely be superseded.

Additionally, no major client has implemented the behaviour to date and the
only server implementation of presence lists (Synapse) auto-accepts invites
leading to privacy concerns in the wild.

With this in mind the most pragmatic solution is to remove presence lists ahead
of the r0 release.

Specifically:-

CS API: Remove
* [POST
  /_matrix/client/r0/presence/list/{userId}](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-presence-list-userid)
* [GET
  /_matrix/client/r0/presence/list/{userId}](https://matrix.org/docs/spec/client_server/r0.4.0.html#get-matrix-client-r0-presence-list-userid)

SS API: Remove
 * [m.presence_invite](https://github.com/matrix-org/matrix-doc/blob/8b65da1cf6fce5f657a2a46b5c6c8bcc24d32ae3/api/server-server/definitions/event-schemas/m.presence_invite.yaml)
 * [m.presence_accept](https://github.com/matrix-org/matrix-doc/blob/8b65da1cf6fce5f657a2a46b5c6c8bcc24d32ae3/api/server-server/definitions/event-schemas/m.presence_accept.yaml)
 * [m.presence_deny](https://github.com/matrix-org/matrix-doc/blob/8b65da1cf6fce5f657a2a46b5c6c8bcc24d32ae3/api/server-server/definitions/event-schemas/m.presence_deny.yaml)


## Tradeoffs

Ideally this proposal would also come with an alternative design for this
functionality. Out of pragmatism the proposal only covers removal of what is
there today.


## Conclusions

This is a common sense attempt to remove unused portions of the spec ahead of
an r0 release. It does not suggest that the ability to subscribe to the
presence of others is undesirable and assumes that this behaviour will return
again in some form.
