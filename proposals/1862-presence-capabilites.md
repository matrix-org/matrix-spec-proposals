# Presence flag for capabilities API

## Proposal

Some homeservers choose to disable the presence feature, so that users cannot send or receive presence.
This should be specificed in the new capabilities API. Servers can also choose to restrict some users
while allowing others, and the capabilities response should reflect this (since the endpoint is authed).

It should be noted that homeservers such as matrix.org already disable presence, and this MSC is an attempt
to make the behaviour specced so that clients may avoid sending it presence information.

`GET /_matrix/client/r0/capabilities`

```json
{
  "capabilities": {
    "m.presence": {
      "send_enabled": false,
      "receive_enabled": false,
    },
    ...
}
```

An omission of `m.presence` would default both sending and receiving to true. An omission of either child flag
would also default that flag to true.

The /sync format does not change based on whether this is enabled. `presence.events` SHOULD be empty when `receive_enalbed` is `false`.

## Tradeoffs

This proposal makes no attempt to address disabled presence over S2S (so remote homeservers are still
clueless). 

None that I can think of.

## Potential issues

None that I can think of.

## Security considerations

None that I can think of.
