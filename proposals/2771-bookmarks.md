# MSC2771: Message Bookmarks

Matrix is currently lacking a feature to bookmark events as a user to provide a way of easy finding
important messages without needing to know a search term.

Note: This is not the same as Element's message pinning feature.

## Proposal

Bookmarks are selected by a User on a Event. This means a user can select a event and add it to the bookmarks.
The bookmark event inside of the account data is used for clients to keep track of bookmarked events.

The bookmarks are saved with the type `m.bookmarks`.

It is being saved inside of the rooms account data

```json
{
  "events": [
    "$12345:example.com",
    "$67890:example.com"
  ]
}
```

## Alternatives

Instead of using the room account data it would be possible to save this in the global account data.
This would be similiar to `m.direct`.

```json
{
  "!12345:example.com": [
    "$67890:example.com"
  ],
  "!67890:example.com": [
    "$12345:example.com"
  ]
}
```

## Potential issues

None