# MSC4356: Recently used emoji

Like other chat platforms, Matrix supports emoji as a way to visually express ideas or emotions. In
practice, most people use a limited set of emoji only. Since emoji are commonly used as a quick way
to react to something, it is desirable for clients to offer users shortcuts to their favorite emoji.
Some emoji picker libraries support this feature by locally tracking emoji usage. This doesn't work
well in a multi-device environment, however, because such history cannot easily be shared between
clients.

This proposal introduces a way for clients to maintain a shared storage of recently used emoji to
enable emoji suggestions across clients.

## Proposal

A new global account data event `m.recent_emoji` is introduced. In `content`, it contains a single
property `recent_emoji` that is an array where each element is itself an array. The first element in
this nested array is the emoji, the second element is a counter (\<= 2^53-1) for how often it was
used. The outer `recent_emoji` array is ordered descendingly by last usage time.

``` json5
{
  "type": "m.recent_emoji",
  "content": {
    "recent_emoji": [
      [ "😅",  7 ], // Most recently used, 7 times overall
      [ "👍", 84 ], // Second most recently used, 84 times overall
      ...
  }
}
```

When an emoji is used in a message or an annotation, the sending client moves (or adds) it to the
beginning of the `recent_emoji` array and increments (or initializes) its counter.

When an image is sent as an inline image or in a reaction (using [MSC4027]), the `mxc://` URI of the
image MAY be used as the "emoji" in this event. Clients which do not support such use of images MUST
tolerate the existence of `mxc://` entries, e.g. by ignoring the entries when deciding what to
display to the user, while still preserving them when modifying the list.

As new emoji are being used, clients SHOULD limit the length of the `recent_emoji` array by dropping
elements from the end. A RECOMMENDED maximum length is 100 emoji. Apart from this, no other
mechanism for resetting counters is mandated as the upper boundary of 2^53-1 seems sufficiently
large for all practical purposes.

Clients MAY freely customise the logic for generating recommendations from the stored emoji. As an
example, they could select the 24 first (= most recently used) emoji and stably sort them by their
counters (so that more recently used emoji are ordered first on ties).

## Potential issues

Clients could choose wildly different ways to generate recommendations from the shared storage
leading to significantly different UX across clients.

## Alternatives

Further metadata such as the concrete access time or the room could be tracked together with emoji.
It is unclear, however, if this would lead to materially better suggestions. A last-used timestamp
could also be used to cull emoji that haven't been used in a very long time. Given that implementations
are already encouraged to limit the maximum number of tracked emoji, this doesn't appear necessary,
however.

## Security considerations

This proposal doesn't mandate encrypting the `m.recent_emoji` account data event. Since emoji are
most commonly used in annotations which are not encrypted, servers could already track and abuse
this information today, however.

Malicious or buggy clients could cause undefined behavior on other clients by setting emoji counters
to negative values or the maximum allowed value. To prevent this, clients SHOULD drop any emojis
with a count below 0 from the list. When observing a count of 2^53-1 for an emoji, clients SHOULD
normalise the entire set of emoji by dividing all counts by two and rounding up. To prevent race
conditions, both of these changes SHOULD only be applied when the client is updating the account
data event due to local emoji usage.

## Unstable prefix

While this MSC is not considered stable, `m.recent_emoji` should be referred to as
`io.element.recent_emoji`.

## Dependencies

None.

  [MSC4027]: https://github.com/matrix-org/matrix-spec-proposals/pull/4027
