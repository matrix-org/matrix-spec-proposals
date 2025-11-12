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
     |                           | bytes                   |                |
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
Origin->Remote: bytes
Remote->ClientB: bytes
-->

For encrypted rooms, the media is encrypted before being uploaded, and the decryption key material is
further encrypted before `/send`ing an event to the origin server. The (encrypted) `file` information
includes a sha256 hash of the *encrypted* blob that was uploaded to the server, described by
[`EncryptedFile`](https://spec.matrix.org/v1.9/client-server-api/#sending-encrypted-attachments).

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

Similar to the `EncryptedFile` schema, a new `hashes` field is introduced to `m.room.message` events
containing file/media references, including the thumbnail if present. An example image message would
be:

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

Similar to encrypted files, the sha256 hash is encoded using [Unpadded Base64](https://spec.matrix.org/v1.9/appendices/#unpadded-base64)
and covers the blob uploaded to the homeserver. Unlike `EncryptedFile` though, we place the hashes
inside the `[thumbnail_]info` object rather than the non-existent `file` object. This existing
inconsistency is expected to be resolved by future MSCs, such as [MSC3551](https://github.com/matrix-org/matrix-spec-proposals/pull/3551)
for Extensible Events.

`hashes` is optional, but when supplied *must* contain `sha256` at a minimum. When using `EncryptedFile`,
the `hashes` object described by this MSC serves no purpose and *must* be ignored by clients (if present).

Clients *should* verify the hash when downloading the media, and refuse to render/offer to save the
media when the hash is mismatched, or when `hashes` is malformed. In future, [`GET /download`](https://spec.matrix.org/v1.9/client-server-api/#get_matrixmediav3downloadservernamemediaid)
could be expanded to take a sha256 parameter to avoid "wasting" the client's bandwidth, however many
implementations already stream the media from origin to local clients while concurrently caching for
future requests.

## Potential issues

Several issues with this proposal are discussed in the security considerations section.

## Alternatives

No alternatives identified.

## Security considerations

This proposal increases security when an entity is attempting to tie a media blob to the DAG, but is
still vulnerable to a replacement attack during the original upload and sending process. Because the
hashes and media itself are not protected by a meaningful form of encryption, the origin server is
still capable of replacing the media blob and intercepting the client's event send request to change
the hash to match the malicious blob. Some clients will detect that their event changed when submitted
to the homeserver, though most will not.

Similarly, a local (remote) server could change the presented hash in an event before sending it down
to clients. Clients will believe these changes in most cases because they do not have the capability
to validate the DAG itself.

This proposal does *not* attempt to fix either tampering issue for unencrypted media. Encrypting events
(and thus media) already solves these issues. Instead, this proposal ties a blob to the DAG itself,
allowing entities processing that DAG to authenticate the media accordingly. This may be useful in
cases where a well-behaved remote server is attempting to prove that a user did in fact receive a
corrupt or maliciously modified file, or when a server is counting references to media before purging
it from a local cache.

(Servers which use reference counters should note that encrypted events can reference *unencrypted*
media as well, so should take care to not delete media they may not be able to re-request when a
client requests it.)

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4101.hashes`
in place of `hashes` in events.

## Dependencies

This MSC has no dependencies, but does interact with MSCs which link events to media. For example,
[MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911) may have increased security
if intermediate servers can verify not only that a user has access to the specific blob URI, but also
that the blob tied to that event is exactly what was sent. Further iteration may be required to support
encrypted media meaningfully in this scenario.
