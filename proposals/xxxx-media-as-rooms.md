# MSCXXXX: Media as Rooms

Matrix currently has the concept of Media Repositories, which act as dumb
file stores tied to a specific homeserver. While this works rather well at
the moment, it comes with two major drawbacks:

* When a homeserver goes offline, any media posted by that server is unretrievable
* Very popular media can put strain on the single homeserver hosting it

This proposal aims to solve both of these by representing media files as
events in a room.

## Proposal

### Uploading media

When a user uploads a piece of media, their server will instead create a new
room, where the room ID is `!<hash-alg>.<file-hash>`. We include the hash
algorithm here in case it ever needs to be changed. The only supported
hashing algorithm at the moment that this proposal introduces in `sha256`, as
this algorithm is used in other places of the Matrix specification. This will
not conflict with existing room IDs as they are currently defined as
`!opaque_id:domain`.

As an example, when a user uploads a PDF with a `sha256` hash of `abc...123`,
a new room will be created on the server with room ID `!sha256.abc...123`.

The server will then begin sending a number of events with
the new event type `m.room.media_chunk`. The content of this event type is as
follows:

```
{
  "data": "dGhpcyBpcyBzb21lIGdyZWF0IHN0dWZmIHlv...",
  "index": 0
}
```

* `data` contains an unpadded-base64 representation of a chunk of the file.
* `index` marks this chunk's index within the array of chunks

Both of these fields are required.

The `data` field should be filled with as many bytes as possible without
the event crossing the maximum size Matrix event size.

The server MUST send these into the room in reverse order of the actual file.
This is to allow someone reading the room from the latest point and
back-paginating to stream the file.

Once the room is created and filled with media data, the room ID will be
returned to the user, using the existing semantics of the
[`/_matrix/media/r0/upload`](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-media-r0-upload)
endpoint.

Example:

**Request**

```
POST /_matrix/media/r0/upload?filename=War+and+Peace.pdf HTTP/1.1
Content-Type: Content-Type: application/pdf

<bytes>
```

**Response**

HTTP 200
```
{
  "content_uri": "mxc://!sha256.abc...123"
}
```

The client will then include this in the body of a `m.room.message` that
references the file, as they do now.

No fields changes need to be made to these events.

### Retrieving media

* The client requests to download some media. It hands the server the room ID and a server to join it with.
  This needs a new/updated endpoint that takes domain names.
* A homeserver chooses to either seed or leech a media room.

Leeching the file:

* Server A asks Server B /media_info -> chunks: 50, size: 9999 bytes, servers: [B,C,D]
* Server A asks Server B /media/chunk with ID !123, chunk [0-4]
  Server A asks Server C /media/chunk with ID !123, chunk [5-9]
  Server A asks Server D /media/chunk with ID !123, chunk [10-14]
  ...
  Chunks are sent as binary.
* Server A can stream the file to the user as it gets it (but not securely)
  Or, Server A has received the whole file, has verified it with its hash,
  and can send it to the client

For notes on how to stream files securely, see [Alternative solutions](#alternative-solutions).

Seeding the file:

* Server A joins the room via Server B
* Server A reconstructs the file from events in the room.
* Server A sends the reconstructed file down to the client.
* Server A continues to let other servers join from it.

Deciding no longer to seed the file:

* Server A leaves the room.

## Potential issues

The size of a piece of media on disk would be greater, as we're storing it in
base64 with metadata of the room and chunk events added on top. However, this
solution not only requires deduplication of media on the local homeserver,
but also across the federation. This should average out less storage space
used across the federation.

Hmm, here's a hard one. Servers will create rooms on their lonesome and not
be able to find other rooms that have been created with the same hash,
causing collisions.

When a server creates a media room, they need a way to know whether one
already exists. How? DHT I guess.

## Alternative solutions

Instead of representing files as a simple list of chunks with a hash on top,
it would be nice to shove a merkle tree into the room instead, with the room
ID then being the merkle root.. You could then stream the media file from
multiple servers at once while verifying each piece on-the-fly. This would
allow for streaming of media without worrying about a malicious server
modifying particular chunks. With the proposal currently as it stands, you
can only verify the integrity of a media file once you've completely
downloaded it.

This would be nice, but would increase the complexity of this proposal quite
a bit. We can always have a new room version in the future which implements
this.

## Security considerations

With media being represented as rooms, it's possible to use the existing
permissions system to allow access to only an approved set of users.

## Privacy considerations

* Don't let other people see that you're viewing a file

If you're just peeking into a room, then only the server you peek through
will know that you've seen it.

If you've joined a room, you join with the server user. You can also be
somewhat anonymised if your homeserver has many different users on it.

* Have to let other people see that you're seeding a file, but you can choose
  to/not choose to (user chooses during /download, server can override
  perhaps?)

## Future Work

There's a known problem in Matrix, which is that to join a room via room ID,
you'll need to know beforehand which servers are in the room. We've patched
this by putting a list of known servers in `matrix.to` links and by scraping
the domain name out of `m.room.tombstone` sender fields, but it'd be nice to
have a more robust solution. This would allow the server who posted the media
to not have to be online for others to gain access to the room.

## Other benefits

This would allow us to use aliases to address files, which could be
potentially useful.

Communities can act as folders, especially once Communities v2 lands and we
can nest them.
