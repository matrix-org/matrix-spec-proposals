# MSC4016: Streaming and resumable E2EE file transfer with random access

## Problem

* File transfers currently take twice as long as they could, as they must first be uploaded in their entirety to the
  sender’s server before being downloaded via the receiver’s server.
* As a result, relative to a dedicated file-copying system (e.g. scp) they feel sluggish. For instance, you can’t
  incrementally view a progressive JPEG or voice or video file as it’s being uploaded for “zero latency” file
  transfers.
* You can’t skip within them without downloading the whole thing (if they’re streamable content, such as an .opus file)
* For instance, you can’t do realtime broadcast of voice messages via Matrix, or skip within them (other than splitting
  them into a series of separate file transfers).
* You also can't resume uploads if they're interrupted.
* Another example is sharing document snapshots for real-time collaboration. If a user uploads 100MB of glTF in Third
  Room to edit a scene, you want all participants to be able to receive the data and stream-decode it with minimal
  latency.

Closes [https://github.com/matrix-org/matrix-spec/issues/432](https://github.com/matrix-org/matrix-spec/issues/432) 

N.B. this MSC is *not* needed to do a streaming decryption or encryption of E2EE files (as opposed to streaming
transfer).  The current APIs let you stream a download of AES-CTR data and incrementally decrypt it without loading the
whole thing into RAM, calculating the hash as you go, and then either surfacing or deleting the decrypted result at the
end if the hash matches.

Relatedly, v2 MXC attachments can't be stream-transferred, even if combined with [MSC2246]
(https://github.com/matrix-org/matrix-spec-proposals/pull/2246), given you won't be able to send the hash in the event
contents until you've uploaded the media.

## Solution sketch

* Upload content in a single file made up of contiguous blocks of AES-GCM content.
    * Typically constant block size (e.g. 32KB)
    * Or variable block size (to allow time-based blocksize for low-latency seeking in streamable content) - e.g. one
      block per opus frame.  Otherwise a 32KB block ends up being 8s of typical opus latency.
        * This would then require a registration sequence to identify the starts of blocks boundaries when seeking
          randomly (potentially escaping the bitstream to avoid registration code collisions).
* Unlike today’s AES-CTR attachments, AES-GCM makes the content self-authenticating, in that it includes an
  authentication tag (AEAD) to hash the contents and protect against substitution attacks (i.e. where an attacker flips
  some bits in the encrypted payload to strategically corrupt the plaintext, and nobody notices as the content isn’t
  hashed).
    * (The only reason Matrix currently uses AES-CTR is that native AES-GCM primitives weren’t widespread enough on
      Android back in 2016)
* To prevent against reordering attacks, each AES-GCM block has to include an encrypted block header which includes a
  sequence number, so we can be sure that when we request block N, we’re actually getting block N back - or
  equivalent.
    * XXX: is there still a vulnerability here? Other approaches use Merkle trees to hash the AEADs rather than simple
      sequence numbers, but why?
* We use streaming HTTP upload (https://developer.chrome.com/articles/fetch-streaming-requests/) and/or
  [tus](https://tus.io/protocols/resumable-upload) resumable upload headers to incrementally send the file. This also
  gives us resumable uploads.
* We then use normal [HTTP Range](https://datatracker.ietf.org/doc/html/rfc2616#section-14.35.1) headers to seek while
  downloading.

## Advantages

* Backwards compatible with current implementations at the HTTP layer
* Fully backwards compatible for unencrypted transfers
* Relatively minor changes needed from AES-CTR to sequence-of-AES-GCM-blocks for implementations like
  [https://github.com/matrix-org/matrix-encrypt-attachment](https://github.com/matrix-org/matrix-encrypt-attachment)  
* We automatically maintain a serverside E2EE store of the file as normal, while also getting 1:many streaming
  semantics
* Provides streaming transfer for any file type - not just media formats
* Minimises memory usage in Matrix clients for large file transfers. Currently all(?) client implementations store the
  whole file in RAM in order to check hashes and then decrypt, whereas this would naturally lend itself to processing
  files incrementally in blocks.
* Leverages AES-GCM’s existing primitives and hashing rather than inventing our own hashing strategy
* We've already implemented this once before (pre-Matrix) in our 'glow' codebase, and it worked excellently.
  pre-E2EE and pre-Matrix in our ‘glow’ codebase.
* Random access could enable torrent-like semantics in future (i.e. servers doing parallel downloads of different chunks
  from different servers, with appropriate coordination)
* tus looks to be under consideration by the IETF HTTP working group, so we're hopefully picking the right protocol for
  resumable uploads.

## Limitations

* Enterprisey features like content scanning and CDGs require visibility on the whole file, so would eliminate the
  advantages of streaming by having to buffering it up in order to scan it.  (Clientside scanners would benefit from
  file transfer latency halving but wouldn't be able to show mid-transfer files)
* When applied to unencrypted files, server-side content scanning (for trust & safety etc) would be unable to scan until
  it’s too late.
* For images & video, senders will still have to read (and decompress) enough of the file into RAM in order to thumbnail
  it or calculate a blurhash, so the benefits of streaming in terms of RAM use on the sender are reduced.  One could
  restrict thumbnailing to the first 500MB of the transfer (or however much available RAM the client has) though, and
  still stream the file itself, which would be hopefully be enough to thumbnail the first frame of a video, or most
  images, while still being able to transfer arbitrary length files.
* Cancelled file uploads will still leak a partial file transfer to receivers who start to stream, which could be
  awkward if the sender sent something sensitive, and then can’t tell who downloaded what before they hit the cancel
  button
* Small bandwidth overhead for the additional AEADs and block headers - ~32 bytes per block.
* Out of the box it wouldn't be able to adapt streaming to network conditions (no HLS or DASH style support for multiple
  bitstreams)
* Might not play nice with CDNs? (I haven't checked if they pass through Range headers properly)
* Recorded E2EE SFU streams (from a [MSC3898](https://github.com/matrix-org/matrix-spec-proposals/pull/3898) SFU or
  LiveKit SFU) could be made available as live-streamed file transfers through this MSC. However, these streams would
  also have their own S-Frame headers, whose keys would need to be added to the `EncryptedFile` block in addition to
  the AES-GCM layer.

## Detailed proposal

The file is uploaded asynchronously using [MSC2246](https://github.com/matrix-org/matrix-spec-proposals/pull/2246).

The proposed v3 `EncryptedFile` block looks like:

```json5
"file": {
    "v": "org.matrix.msc4016.v3",
    "key": {
        "alg": "A256GCM",
        "ext": true,
        "k": "cngOuL8OH0W7lxseExjxUyBOavJlomA7N0n1a3RxSUA",
        "key_ops": [
            "encrypt",
            "decrypt"
        ],
        "kty": "oct"
    },
    "iv": "HVTXIOuVEax4E+TB", // 96-bit base-64 encoded initialisation vector
    "url": "mxc://example.com/raAZzpGSeMjpAYfVdTrQILBI",
},
```

N.B. there is no longer a `hashes` key, as AES-GCM includes its own hashing to enforce the integrity of the file
transfer. Therefore we can authenticate the transfer by the fact we can decrypt it using its key & IV (unless an
attacker who controls the same key & IV has substituted it for another file - see Security Considerations below)

We split the file stream into blocks of AES-256-GCM, with the following simple framing:

 * File header with a magic number of: 0x4D, 0x58, 0x43, 0x03 ("MXC" 0x03) - just so `file` can recognise it.
 * 1..N blocks, each with a header of:
    * a 32-bit field: 0xFFFFFFFF (a registration code to let a parser handle random access within the file
    * a 32-bit field: block sequence number (starting at zero, used to calculate the IV of the block, and to aid random
      access)
    * a 32-bit field: the length in bytes of the encrypted data in this block.
    * a 32-bit field: a CRC32 checksum of the block, including headers. This is used when randomly seeking as a
      consistency check to confirm that the registration code really did indicate the beginning of a valid frame of
      data.  It is not used for cryptographic integrity.
    * the actual AES-GCM bitstream for that block.
        * the plaintext block size can be variable; 32KB is a good default for most purposes.
        * Audio streams may want to use a smaller block size (e.g. 1KB blocks for a CBR 32kbps Opus stream will give
          250ms of streaming latency).  Audio streams should be CBR to avoid leaking audio waveform metadata via block
          size.
        * The block is encrypted using an IV formed by concatenating the block sequence number of the `file` block with
          the IV from the `file` block (forming a 128-bit IV, which will be hashed down to 96-bit again within
          AES-GCM).  This avoids IV reuse (at least until it wraps after 2^32-1 blocks, which at 32KB per block is
          137TB (18 hours of 8k raw video), or at 1KB per block is 4TB (34 years of 32kbps audio)).
            * Implementations MUST terminate a stream if the seqnum is exhausted, to prevent IV reuse.
            * Receivers MUST terminate a stream if the seqnum does not sequentially increase (to prevent the server from
              shuffling the blocks)
            * XXX: Alternatively, we could use a 64-bit seqnum, spending 8 bytes of header on seqnums feels like a waste
              of bandwidth just to support massive transfers. And we'd have to manually hash it with the 96-bit IV
              rather than use the GCM implementation.
        * The block is encrypted including the 32-bit block sequence number as Additional Authenticated Data, thus
          stopping encrypted blocks from impersonating each other.

Or graphically, each frame is:

```
protocol "Registration Code (0xFFFFFFF):32,Block sequence number:32,Encrypted block length:32,CRC32:32,AES-GCM encrypted Data:64"

 0                   1                   2                   3  
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Registration Code (0xFFFFFFF)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Block sequence number                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Encrypted block length                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             CRC32                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                     AES-GCM encrypted Data                    +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

```

The actual file upload can then be streamed in the request body in the PUT (requires HTTP/2 in browsers). Similarly, the
download can be streamed in the response body.  The download should stream as rapidly as possible from the media
server, letting the receiver view it incrementally as the upload happens, providing "zero-latency" - while also storing
the stream to disk.

For resumable uploads (or to upload in blocks for HTTP clients which don't support streaming request bodies), we use
[tus](https://tus.io/protocols/resumable-upload) 1.0.0.

For resumable downloads, we then use normal 
[HTTP Range](https://datatracker.ietf.org/doc/html/rfc2616#section-14.35.1) headers to seek and resume while downloading.

TODO: We need a way to mark a transfer as complete or cancelled (via a relation?).  If cancelled, the sender should
delete the partial upload (but the partial contents will have already leaked to the other side, of course).

TODO: While we're at it, let's actually let users DELETE their file transfers, at last.

N.B. Clients which implement displaying blurhashes should progressively load the thumbnail over the top of the blurhash,
to make sure the detailed thumbnail streams in and is viewed as rapidly as possible.

## Alternatives

* We could use an existing streaming encrypted framing format of some kind rather (SRTP perhaps, which would give us
  timestamps for easier random access for audio/video streams) - but this feels a bit strange for plain old file
  streams.
* Alternatively, we could descope random access entirely, given it only makes sense for AV streams, and requires
  timestamps to work nicely - and simply being able to stream encryption/decryption is a win in its own right. For
  instance, glow doesn't let you seek randomly within files which are mid transfer; only tail.
* Split files into a series of separate m.file uploads which the client then has to glue back together (as the
  [voice broadcast feature](https://github.com/vector-im/element-meta/discussions/632) does in Element today).
    * Pros:
        * Works automatically with antivirus & CDGs
        * Could be made to map onto HLS or DASH? (by generating an .m3u8 which contains a bunch of MXC urls? This could
          also potentially solve the glitching problems we’ve had, by reusing existing HLS players augmented with our
          E2EE support)
    * Cons:
        * Is always going to be high latency (e.g. Element currently splits into ~30s chunks) given rate limits on
          sending file events
        * Can be a pain to glue media uploads back together without glitching
* Transfer files via streaming P2P file transfer via WebRTC data channels
  (https://github.com/matrix-org/matrix-spec/issues/189)
    * Pros:
        * Easy to implement with Matrix’s existing WebRTC signalling
        * Could use MSC3898-inspired media control to seek in the stream
    * Cons:
        * You don’t get a serverside copy of the data
        * Hard for clients to implement relative to a simple HTTP download
        * You expose client IPs to each other if going P2P rather than via TURN
* Do streaming voice/video messages/broadcast via WebRTC media channels instead
    * Pros:
        * Lowest latency
        * Could use media control to seek
        * Supports multiple senders
        * Works with CDGs and other enterprisey scanners which know how to scan VOIP payloads
        * Could automatically support variable streams via SFU to adapt to network conditions
        * If the SFU does E2EE and archiving, you get that for free.
    * Cons:
        * Complex; you can’t just download the file via HTTP
        * Requires client to have a WebRTC stack
        * A suitable SFU still doesn’t exist yet
* Transfer files out of band using a protocol which already provides streaming transfers (e.g. IPFS?)
* Could use ChaCha20-Poly1305 rather than AES-GCM, but no native webcrypto impl yet: https://github.com/w3c/webcrypto/issues/223
  * See also https://soatok.blog/2020/05/13/why-aes-gcm-sucks/ and https://andrea.corbellini.name/2023/03/09/authenticated-encryption/
* We could use YouTube's resumable upload API via `Content-Range` headers from
  https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol, but having implemented both it and
  tus, tus feels inordinately simpler and less fiddly.  YouTube is likely to be well supported by proxies etc, but if
  tus is ordained by the HTTP IETF WG, then it should be well supported too.

## Security considerations

* AES-GCM is not key-committing, so removing hashes on the event means:
  * the key committing attacks are all about an adversary which constructs a ciphertext C with multiple ((IV1, K1), (IV2, K2), ...) so that C decrypts to P1, P2, ... at the same time
  * given that AES GCM is specifically not key committing, we introduce this attack.
  * (thanks to @dkasak for pointing this out)
* Variable size blocks could leak metadata for VBR audio.  Mitigation is to use CBR if you care about leaking voice
  traffic patterns (constant size blocks isn’t necessarily enough, as you’d still leak the traffic patterns)
* Is encrypting a sequence number in block header (with authenticated encryption) sufficient to mitigate reordering
  attacks?
  * When doing random access, the reader has to trust the server to serve the right blocks after a discontinuity
* The resulting lack of atomicity on file transfer means that accidentally uploaded files may leak partial contents to
  other users, even if they're cancelled.
* Clients may well wish to scan untrusted inbound file transfers for malware etc, which means buffering the inbound
  transfer and scanning it before presenting it to the user.
* Removing the `hashes` entry on the EncryptedFile description means that an attacker who controls the key & IV of the
  original file transfer could strategically substitute the file contents.  This could be desirable for CDGs wishing to
  switch a file for a sanitised version without breaking the Matrix event hashes.  For other scenarios it could be
  undesirable - for instance, a malicious server could serve different file contents to other users or servers to evade
  moderation.  An alternative might be for the sender to keep sending new hashes in related matrix events as the
  stream uploads (but it's unclear if this is worth it, relative to MSC3888)

## Conclusion

For the voice broadcast use case, it's a bit unclear whether this is actually an improvement over splitting files into
multiple file uploads (or [MSC3888](https://github.com/matrix-org/matrix-spec-proposals/blob/weeman1337/voice-broadcast/proposals/3888-voice-broadcast.md)).
It's also unfortunate that the benefits of the MSC are reduced with content scanners and CDGs.  It’s also a bit unclear
whether voice/video broadcast would be better served via MSC3888 style behaviour.

However, for halving the transfer time for large videos and files (and the magic "zero latency" of being able to see
file transfers instantly start to download as they upload) it still feels like a worthwhile MSC.  Switching to GCM is
desirable too in terms of providing authenticated encryption and avoiding having to calculate out-of-band hashes for
file transfer.  Finally, implementing this MSC will force implementations to stream their file encryption/decryption
and avoid the temptation to load the whole file into RAM (which doesn't scale, especially in constrained environments
such as iOS Share Extensions).

## Dependencies

This MSC depends on [MSC2246](https://github.com/matrix-org/matrix-spec-proposals/pull/2246), which has now landed in
the spec. Extends [MSC3469](https://github.com/matrix-org/matrix-spec-proposals/pull/3469).

## Unstable prefixes

| Unstable prefix       | Stable prefix       |
| --------------------- | ------------------- |
| org.matrix.msc4016.v3 | v3                  |
