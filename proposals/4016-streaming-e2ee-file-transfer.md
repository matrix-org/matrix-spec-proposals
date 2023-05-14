# WIP: MSC4016: Streaming E2EE file transfer with random access

## Problem

* File transfers currently take twice as long as they could, as they must first be uploaded in their entirety to the sender’s server before being downloaded via the receiver’s server.
* As a result, relative to a dedicated file-copying system (e.g. scp) they feel sluggish. For instance, you can’t incrementally view a progressive JPEG or voice or video file as it’s being uploaded for “zero latency” file transfers.
* You can’t skip within them without downloading the whole thing (if they’re streamable content, such as an .opus file)
* For instance, you can’t do realtime broadcast of voice messages via Matrix, or skip within them (other than splitting them into a series of separate file transfers).
* Another example is sharing document snapshots for real-time collaboration. If a user uploads 100MB of glTF in Third Room to edit a scene, you want all participants to be able to receive the data and stream-decode it with minimal latency.

Closes [https://github.com/matrix-org/matrix-spec/issues/432](https://github.com/matrix-org/matrix-spec/issues/432) 

## Solution overview

* Upload content in a single file made up of contiguous blocks of AES-GCM content.
    * Typically constant block size (e.g. 32KB)
    * Or variable block size (to allow time-based blocksize for low-latency seeking in streamable content) - e.g. one block per opus frame.  Otherwise a 32KB block ends up being 8s of typical opus latency.
        * This would then require a registration sequence to identify the starts of blocks boundaries when seeking randomly (potentially escaping the bitstream to avoid registration code collisions).
* Unlike today’s AES-CTR attachments, AES-GCM makes the content self-authenticating, in that it includes an authentication tag (AEAD) to hash the contents and protect against substitution attacks (i.e. where an attacker flips some bits in the encrypted payload to strategically corrupt the plaintext, and nobody notices as the content isn’t hashed).
    * (The only reason Matrix currently uses AES-CTR is that native AES-GCM primitives weren’t widespread enough on Android back in 2016)
* To prevent against reordering attacks, each AES-GCM block has to include an encrypted block header which includes a sequence number, so we can be sure that when we request block N, we’re actually getting block N back.
    * XXX: is there still a vulnerability here? Other approaches use Merkle trees to hash the AEADs rather than simple sequence numbers, but why?
* We then use normal [HTTP Range](https://datatracker.ietf.org/doc/html/rfc2616#section-14.35.1) headers to seek while downloading
* We could also use [Youtube-style](https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol) off-standard Content-Range headers on POST when uploading for resumable/incremental uploads.

## Advantages

* Backwards compatible with current implementations at the HTTP layer
* Fully backwards compatible for unencrypted transfers
* Relatively minor changes needed from AES-CTR to sequence-of-AES-GCM-blocks for implementations like [https://github.com/matrix-org/matrix-encrypt-attachment](https://github.com/matrix-org/matrix-encrypt-attachment)  
* We automatically maintain a serverside E2EE store of the file as normal, while also getting 1:many streaming semantics
* Provides streaming transfer for any file type - not just media formats
* Minimises memory usage in Matrix clients for large file transfers. Currently all(?) client implementations store the whole file in RAM in order to check hashes and then decrypt, whereas this would naturally lend itself to processing files incrementally in blocks.
* Leverages AES-GCM’s existing primitives and hashing rather than inventing our own hashing strategy
* We already had Range/Content-Range resumable/seekable zero-latency HTTP transfer implemented and working excellently pre-E2EE and pre-Matrix in our ‘glow’ codebase.

## Limitations

* Enterprisey features like content scanning and CDGs require visibility on the whole file, so would eliminate the advantages of streaming by having to buffering it up in order to scan it.
* When applied to unencrypted files, server-side content scanning (for trust & safety etc) would be unable to scan until it’s too late.
* Cancelled file uploads will still leak a partial file transfer to receivers who start to stream, which could be awkward if the sender sent something sensitive, and then can’t tell who downloaded what before they hit the cancel button
* Small bandwidth overhead for the additional AEADs and block headers - probably ~16 bytes per block.
* Out of the box it wouldn't be able to adapt streaming to network conditions (no HLS or DASH style support for multiple bitstreams)
* Might not play nice with CDNs? (I haven't checked if they pass through Range headers properly)

## Detailed proposal

TODO, if folks think it's worth it

## Alternatives

* Split files into a series of separate m.file uploads which the client then has to glue back together (as the [voice broadcast feature](https://github.com/vector-im/element-meta/discussions/632) does in Element today).
    * Pros:
        * Works automatically with antivirus & CDGs
        * Could be made to map onto HLS or DASH? (by generating an .m3u8 which contains a bunch of MXC urls? This could also potentially solve the glitching problems we’ve had, by reusing existing HLS players augmented with our E2EE support)
    * Cons:
        * Is always going to be high latency (e.g. Element currently splits into ~30s chunks) given rate limits on sending file events
        * Can be a pain to glue media uploads back together without glitching
* Transfer files via streaming P2P file transfer via WebRTC data channels (https://github.com/matrix-org/matrix-spec/issues/189)
    * Pros:
        * Easy to implement with Matrix’s existing WebRTC signalling
        * Could use MSC3898-inspired media control to seek in the stream
    * Cons:
        * You don’t get a serverside copy of the data
        * You expose client IPs to each other if going P2P rather than via TURN
* Do streaming voice/video messages/broadcast via WebRTC media channels instead (as hinted in [MSC3888](https://github.com/matrix-org/matrix-spec-proposals/pull/3888))
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

## Security considerations

* Variable size blocks could leak metadata for VBR audio.  Mitigation is to use CBR if you care about leaking voice traffic patterns (constant size blocks isn’t necessarily enough, as you’d still leak the traffic patterns)
* Is encrypting a sequence number in block header (with authenticated encryption) sufficient to mitigate reordering attacks?
* Do the repeated and predictable encrypted block headers facilitate attacks?
* The resulting lack of atomicity on file transfer means that accidentally uploaded files may leak partial contents to other users, even if they're cancelled.

## Conclusion

It’s a bit unclear whether this is actually an improvement over formalising chunk-based file transfer as voice broadcast does today.  The fact that it’s incompatible with content scanners and CDGs is a bit of a turn off.  It’s also a bit unclear whether voice/video broadcast would be better served via MSC3888 style behaviour.

Therefore, I’ve written this as a high-level MSC to gather feedback, and to get the design down on paper before I forget it (I originally sketched this out a month or so ago).

## Dependencies

This MSC depends on [MSC2246](https://github.com/matrix-org/matrix-spec-proposals/pull/2246), which is landing currently in the spec.
Extends [MSC3469](https://github.com/matrix-org/matrix-spec-proposals/pull/3469).