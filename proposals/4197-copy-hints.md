# MSC4197: Copy-Paste Hints

In Matrix today, it can be used for communication. One thing that is communicated is two-factor auth codes. In other platforms, one convenience is being able to quickly copy-paste two factor auth codes. This is not possible in Matrix today.

When sending a message, my message could contain a hint to the user's client that they should copy some particular part of the message. I propose to add a new field to `m.room.message` events that will hint to clients what text they could facilitating the user to copy.

### Proposal

* technical details
* describe the solution (This is the solution. Be assertive.)

`m.room.message` contains a new field, `copy_hint`, under the existing `content` dictionary. This new field will contain a string representing text that the client could present to the user to copy.

An example is below:


```json5
{
  "content": {
    "body": "DO NOT SHARE THIS WITH ANYONE!!! Your 2FA code is: 100000",
    "m.mentions": {},
    "msgtype": "m.text",
    "copy_hint": "100000"
  },
  "origin_server_ts": 1726936182830,
  "sender": "@andrewm:element.io",
  "type": "m.room.message",
  "unsigned": {
    "membership": "join",
    "age": 54359693,
    "transaction_id": "m1726936182657.27"
  },
  "event_id": "$4WvO6_skvEIibdffnDKdTkFHtOKUZaPFLm8HJuXcz7E",
  "room_id": "!jWkHTegEyVsdPJkjHA:element.io"
}
```

Clients MAY automatically copy the contents of `copy_hint` to the clipboard without asking the user. This is an implementation detail.

### Potential Issues

None considered!

### Alternatives

1. `hints` dictionary.
2. Leave things as is (please don't!)
3. boolean `copy_hint` field (hint to client to copy the whole message)
4. give up (similar to 2.)
5. Use indexes in the message
    * Harder to implement
    * Use bandwidth
6. If the event is encrypted, leave the 2FA code out of the encryption

### Security Considerations

TODO.

### Unstable prefix

While this MSC is unstable, all instances of the field name `copy_hint` must be replaced with `org.matrix.msc4197.copy_hint`.

### Dependencies

I do not build on any giant's shoulders.
