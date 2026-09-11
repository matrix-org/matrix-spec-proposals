# MSC4101: Hashes for unencrypted media

A typical flow for unencrypted media being sent in a room looks like this:

```
+---------+                 +---------+               +---------+      +---------+
| ClientA |                 | Origin  |               | Remote  |      | ClientB |
+---------+                 +---------+               +---------+      +---------+
     |                           |                         |                |
     | /upload                   |                         |                |
     |-------------------------->|                         |                |
     |                           |                         |                |
     |               content_uri |                         |                |
     |<--------------------------|                         |                |
     |                           |                         |                |
     | /send/m.room.message      |                         |                |
     |-------------------------->|                         |                |
     |                           |                         |                |
     |                           | Append PDU fields       |                |
     |                           |------------------       |                |
     |                           |                 |       |                |
     |                           |<-----------------       |                |
     |                           |                         |                |
     |                           | /send (federation)      |                |
     |                           |------------------------>|                |
     |                           |                         |                |
     |                           |                         | /sync          |
     |                           |                         |--------------->|
     |                           |                         |                |
     |                           |                         |      /download |
     |                           |                         |<---------------|
     |                           |                         |                |
     |                           |               /download |                |
     |                           |<------------------------|                |
     |                           |                         |                |
     |                           | info+bytes              |                |
     |                           |------------------------>|                |
     |                           |                         |                |
     |                           |                         | bytes          |
     |                           |                         |--------------->|
     |                           |                         |                |
```
<!--
object ClientA Origin Remote ClientB
ClientA->Origin: /upload
Origin->ClientA: content_uri
ClientA->Origin: /send/m.room.message
Origin->Origin: Append PDU fields
Origin->Remote: /send (federation)
Remote->ClientB: /sync
ClientB->Remote: /download
Remote->Origin: /download
Origin->Remote: info+bytes
Remote->ClientB: bytes
-->

For encrypted rooms, the media is encrypted before being uploaded, and the decryption key material is
further encrypted before `/send`ing an event to the origin server. The (encrypted) `file` information
includes a sha256 hash of the *encrypted* blob that was uploaded to the server, described by
[`EncryptedFile`](https://spec.matrix.org/v1.16/client-server-api/#sending-encrypted-attachments).

Because the hash is encrypted by the sending client, the server is unable to meaningfully change the
content of that file. Any difference in the encrypted blob would result in a mismatched hash, which
the server cannot modify because it can't see the hash itself. This effectively authenticates the
media blob to the event (and thus the DAG) from the view of the client.

However, unencrypted media does not have similar authentication measures. When responding to the remote
server's `/download` request, the origin server could serve a completely different file without either
user being aware. Further, if a user does report that they are seeing something potentially unexpected,
the origin server has plausible deniability that the wrong file was served.

For maximum security against this problem, rooms should be encrypted. This proposal introduces an
optional sha256 hash on unencrypted media to remove *part* of the plausible deniability problem, but
does not solve it. An origin server can still modify both the upload *and* hashes in an event before
that event is converted to a PDU and sent to other servers. Once the PDU is sent though, the download
is authenticated by the hash present in the DAG.

## Proposal

Similar to `EncryptedFile`'s schema, a new `hashes` field is introduced under `(thumbnail_)info` in
`m.room.message` events containing files. Note that `EncryptedFile` places `hashes` under a `(thumbnail_)file`
field instead of `info` - this proposal intentionally avoids using `file` to avoid confusing clients
into thinking they're looking at encrypted media when it is in fact unencrypted. Future proposals,
like [MSC3551](https://github.com/matrix-org/matrix-spec-proposals/pull/3551) under Extensible Events,
may address this inconsistency.

An example would be:

```jsonc
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.image",
    "body": "image.png",
    "url": "mxc://example.org/abc123",
    "info": {
      "size": 33186,
      "mimetype": "image/png",
      "w": 500,
      "h": 500,
      "hashes": { // NEW!
        "sha256": "<unpadded base64 encoded hash>"
      },
      "thumbnail_url": "mxc://example.org/def456",
      "thumbnail_info": {
        "size": 3816,
        "mimetype": "image/png",
        "w": 128,
        "h": 128,
        "hashes": { // NEW!
          "sha256": "<unpadded base64 encoded hash>"
        }
      }
    }
  }
}
```

`hashes` is optional but *strongly recommended*. Exactly like encrypted files, it is an object of
algorithm(s) to hash value, where the value is encoded using [unpadded base64](https://spec.matrix.org/v1.16/appendices/#unpadded-base64).
At a minimum, clients SHOULD support the SHA-256 hash, which uses the key `sha256` (exactly like
encrypted files).

When `hashes` is present, clients SHOULD verify the hash when downloading the media. If the hash differs,
or the `hashes` object is malformed, the client SHOULD refuse to render the media to the user. A future
proposal may alter the [`GET /download`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv1mediadownloadservernamemediaid)
endpoint to include a hash value, allowing the server to take on the comparison. Though, this is not
done for encrypted media today, so may be a non-issue.

## Potential issues

There are drawbacks to this proposal which are discussed in the Security Considerations section. The
notes within the proposal text about lack of consistency with encrypted files are relevant, but not
duplicated here.

## Alternatives

* Making media IDs be hashes instead of randomly generated IDs. This has value in deduplicating media,
  but causes issues in a world with linked media or copyright concerns. The author of this proposal
  expands upon these concerns in commentary on [MSC3468](https://github.com/matrix-org/matrix-spec-proposals/pull/3468)
  (written by a different author).

## Security considerations

Prior to this proposal, the server receiving the event or the origin server could serve different
media to different users without the users knowing. This proposal fixes a trivial version of this
attack, but does not solve the situation where either of those servers go a step further to modify
or replace the hashes before serving the event to the clients. For example, a receiving server could
strip the hashes off the event to 'trick' the client into downloading unverifiable media because clients
do not typically receive or verify the full PDU format for events.

This proposal does not intend to resolve this concern. Instead, the following may be used to mitigate
the concerns:

1. [MSC2757](https://github.com/matrix-org/matrix-spec-proposals/pull/2757) may be used to have clients
   sign (unencrypted) events, preventing tampering with the contained hashes and other details. This
   would also fix other tampering concerns with events.

2. Some time after this proposal is merged to the specification, clients may *require* hashes be present
   otherwise they fail to download the media entirely. This is still subject to issues where the server
   modifies rather than strips the hashes, but at least increases attack complexity in the process.

   This choice may cause subpar user experience for users which regularly receive media from clients
   that do not support hashes. As such, it is left as a deliberate implementation detail for when/how
   to require hashes on received media. If a client chooses to require hashes, this proposal recommends
   doing so no sooner than 3 months after the spec release containing this proposal.

3. At a room level, communities may invoke the above option 2 through use of [MSC4284](https://github.com/matrix-org/matrix-spec-proposals/pull/4284)
   Policy Servers. By receiving the full PDU format, policy servers can ensure that at least the
   event which leaves the origin server contains unmodified media hashes, but cannot detect or prevent
   situations where the origin server has modified the event between the client sending it and the
   policy server validating it. Policy servers additionally cannot prevent or detect servers modifying
   events before they are sent to local users, as identified by [MSC2757](https://github.com/matrix-org/matrix-spec-proposals/pull/2757).

   Policy servers can similarly be used to enforce MSC2757 mechanics, if desired by the community.

A combination of the above options may also be deployed for higher coverage of the attack space.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4101.hashes`
in place of `hashes` in events.

## Dependencies

This MSC has no dependencies, but does interact with MSCs which link events to media. For example,
[MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911) may have increased security
if intermediate servers can verify not only that a user has access to the specific blob URI, but also
that the blob tied to that event is exactly what was sent. Further iteration may be required to support
encrypted media meaningfully in this scenario. Likewise, [MSC2757](https://github.com/matrix-org/matrix-spec-proposals/pull/2757)
will help this MSC become safer if it were to be merged, but is not a blocking dependency.
