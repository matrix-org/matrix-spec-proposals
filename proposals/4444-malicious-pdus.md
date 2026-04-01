# MSC4444: Malicious PDUs

XMPP and IPv4 both have their systems for marking data as evil/malicious:
- [XEP-0076](https://xmpp.org/extensions/xep-0076.html)
- [RFC 3514](https://www.ietf.org/rfc/rfc3514)

However, Matrix lacks such a mechanism, and as such clients and servers
cannot easily discern between a normal PDU and one with malicious intent.

## Proposal

We add an `evil` boolean to the top-level of all PDUs, and protect it from
redaction. 

If `evil` is `true` or is not present, then the PDU is malicious.
Secure clients and servers SHOULD reject these PDUs. Insecure
clients and servers MAY crash, use the wrong stateres algorithm,
ignore auth rules, or permit IP literals in all rooms.
<!-- DOWN WITH MSC4045 -->

If `evil` is `false`, the PDU is not malicious. Clients and servers
MAY allow these PDUs, assuming they pass other auth rules.

If `evil` is a non-boolean value, then it is assumed the PDU is
malicious and should be handled as stated above.

`/_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}` has a new query
parameter to assist clients in sending malicious PDUs: `evil`. When set to
`true`, the PDU has the `evil` key set to `true`, otherwise it is `false`.

A new error code is added if the server refuses to send malicious PDUs:
`M_SPEAK_NO_EVIL`. Clients SHOULD NOT attempt to send malicious PDUs anymore
after receiving this error.

This will require a new room version.

## Potential issues

None.

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

| Stable               | Unstable                                      |
|---------------------:|:----------------------------------------------|
|    `M_SPEAK_NO_EVIL` | `COM.NHJKL.MSC4444.SPEAK_NO_EVIL`             |
|   `evil` query param | `com.nhjkl.msc4444.evil`                      |
|        Room version: | `com.nhjkl.msc4444.opt2`, based on v3.        |

## Dependencies

None.
