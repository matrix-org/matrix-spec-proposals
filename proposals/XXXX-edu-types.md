# MSCXXXX: Server opt-out of specific EDU types

Some servers may wish to not receive specific types of EDUs, such as presence, to
cut down on the amount of bandwidth used (as an example).

## Proposal

### `GET /_matrix/federation/v1/edutypes`

This endpoint dictates what types of EDUs the server wishes to receive.

The server should reply with a list of EDU types:

```json
{
    "read_receipts": true,
    "presence": true,
    "typing": true
}
```

Other types of EDUs (signing key updates, device lists, to-device messaging)
are likely unsafe to opt-out of and thus must not be included.

This endpoint should not require authentication as nothing too sensitive is
revealed by having it as such.

## Potential issues

Older homeservers (or simply non-compliant ones) will still send unwanted EDUs,
although these can just be discarded.

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

`/_matrix/federation/unstable/io.fsky.vel/edutypes`

## Dependencies

None.
