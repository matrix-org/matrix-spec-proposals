# MSC4440: Profile Biography via Global Profiles

A lot of users, especially those switching to Matrix from other platform (e.g. Discord) are finding Matrix
lacking for not providing a way to write information about themselves, e.g. their interests, and having
others be able to view that. Several clients already have their own, client-specific implementations of a
biography field via extended global profiles, creating a split in the ecosystem.
To bring back standardization, this proposal defines a standardized biography field on top of [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

## Proposal

Profiles may have an optional `m.biography` field as object. These fields can be fetched through the [profile API endpoints](https://spec.matrix.org/unstable/client-server-api/#profiles).
Clients should display the biography of a user in their respective user popup/profile view UI.

### Examples

Plaintext only:
```json
{
  "m.biography": {
    "m.text": [
      { "body": "hello world!\n\ninterests:\n-  programming\n-  matrix\n-  sleeping\n-  petting cats" }
    ]
  }
}
```

with HTML formatting:
```json
{
  "m.biography": {
    "m.text": [
      { "body": "hello world!<br/><br/>interests:<br/><ul data-md=\"-\"><li><p>programming</p></li><li><p>matrix</p></li><li><p>sleeping</p></li><li><p>petting cats</p></li></ul><br/><img data-mx-emoticon src=\"mxc://fomx.gay/ICgRWFY6HWvMVVrHRqr7MYMLiTCgWxpl\" alt=\"bwaa\" title=\"bwaa\" height=\"32\" />", "mimetype": "text/html" },
      { "body": "hello world!\n\ninterests:\n-  programming\n-  matrix\n-  sleeping\n-  petting cats" }
    ]
  }
}
```

The `m.biography` object should hold an ordered `m.text` array as defined by [MSC1767](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/msc1767/proposals/1767-extensible-events.md)
/ extensible events.
Clients may wish to add formatting to their biography in forms of an HTML-formatted representation of the
body in the same format as [formatted messages](https://spec.matrix.org/v1.18/client-server-api/#mroommessage-msgtypes),
in which case clients should prefer rendering that one instead.

## Potential issues

Unsure?

## Alternatives

Maybe linking a pastebin URL in your username?
Potentially setting an m.presence status_msg could work too, though that is much more limited.

## Security considerations

- Malicious actors could set an unreasonably long bio, potentially lagging or even crashing clients, if length
stays unlimited.
- Additional T&S concerns, e.g. moderation and when clients should (not) render a users biography.
One possible consideration could be disallowing clients from rendering a biography once a users' membership
event has been redacted or they've been banned from the current room, while not sharing further rooms with
the viewer. This approach would be similar to Discord in terms of UX.

## Unstable prefix

Clients implementing this MSC early may use the profile key `gay.fomx.biography`.

## Dependencies

None.
