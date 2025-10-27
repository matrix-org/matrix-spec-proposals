# MSC4373: Server opt-out of specific EDU types

Some servers may wish to not receive specific types of EDUs, such as presence, to
cut down on the amount of bandwidth used (as an example).

## Proposal

### `GET /_matrix/federation/v1/edutypes`

This endpoint dictates what types of EDUs the server wishes to receive.

The response for this endpoint is shaped like the following:

```json
{
    "m.presence": false,
    "m.receipt": true,
    "m.typing": true
}
```

The allowed types are:
* `m.presence`
* `m.receipt`
* `m.typing`

Other types of EDUs (signing key updates, device lists, to-device messaging, etc)
are likely unsafe to opt-out of.

This endpoint SHOULD NOT require authentication, but if provided, follow the normal
verification process.

If the EDU type is listed, and is set to `false`, any EDUs of that type
SHOULD NOT be sent to the target homeserver. The target server MUST ignore
EDUs of these types.

If the EDU type is set to `true` or absent, the EDU MAY be sent to the target 
homeserver, unless other factors disallow it (such as room ACLs, where that is
relevant).

The endpoint response SHOULD be cached. Servers SHOULD read the `Cache-Control`
HTTP header, and max it out at a week, using a week if the header is absent
or malformed.

## Potential issues

Older homeservers (or simply non-compliant ones) will still send unwanted EDUs,
although these can just be ignored.

## Alternatives

An explicit allowlist is recommended over allowing everything with a list of keys
that SHOULD NOT be put in the list, to ensure important information in new EDU types
is not ignored or not sent to homeservers.

While the alternative design is more flexible, it introduces unnecessary risk by
defaulting to allowing filtering of all EDU types, which is bad for the reasons
described above.

## Security considerations

None.

## Unstable prefix

`/_matrix/federation/unstable/io.fsky.vel/edutypes`

## Dependencies

None.
