# Add a seperate message type for voice messages

In the matrix spec right now, there is a message type `m.audio` for audio files.
In other messaging apps, there is also a special type for voice memos, since they carry a different meaning and inflict different behaviour.
This MSC calls for the introduction of an `m.voice` message type.


## Proposal

Even if it's not the primary mode of communication for nerds,
voice memos are very important to a lot of users of modern instant messaging services.
In order to provide awesome voice messages, they need to be treated differently from generic audio files.

For example, WhatsApp renders them differenty, to hihglight that they are a way of communication.
WhatsApp also always force-downloads them, because like a text message, they should be available to consume as early as possible.
This lets the recipient know at a glance that they are being expected to listen to the voice messages now,
instead of later.

So, I propose to introduce a new message type `m.voice` with the same contents as `m.audio`, but to be handled slightly differently.

## Potential issues

Introducing a new message type means that client developers will have to do work to implement it,
or many people won't be able to use the feature.

## Alternatives

Alternatively, a flag `voice = true` or `type = "voice"` could be created inside of the `m.audio` event.
I'm not sure what the more canonical way of doing things would be here.

## Security considerations

none
