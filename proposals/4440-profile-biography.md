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
    "body": "hello world!\n\ninterests:\n-  programming\n-  matrix\n-  sleeping\n-  petting cats"
  }
}
```

with HTML formatting:
```json
{
  "m.biography": {
    "body": "hello world!\n\ninterests:\n-  programming\n-  matrix\n-  sleeping\n-  petting cats",
    "format": "org.matrix.custom.html",
    "formatted_body": "hello world!<br/><br/>interests:<br/><ul data-md=\"-\"><li><p>programming</p></li><li><p>matrix</p></li><li><p>sleeping</p></li><li><p>petting cats</p></li></ul><br/><img data-mx-emoticon src=\"mxc://fomx.gay/ICgRWFY6HWvMVVrHRqr7MYMLiTCgWxpl\" alt=\"bwaa\" title=\"bwaa\" height=\"32\" />"
  }
}
```

The `body` field should hold a plaintext representation of the users' biography, similar to room messages.
Clients can optionally set the `formatted_body` field to an HTML-formatted representation of the body in the
same format as [formatted messages](https://spec.matrix.org/v1.17/client-server-api/#mroommessage-msgtypes),
in which case the format field has to be set to `org.matrix.custom.html`.
When rendering a user's biography, the `formatted_body` should be preferred if set, but clients are free to
render the plaintext representation in `body` instead.

## Potential issues

Unsure?

## Alternatives

None, really. Maybe linking a pastebin URL in your username?

## Security considerations

Malicious actors could set an unreasonably long bio, potentially lagging or even crashing clients, if length
stays unlimited.

## Unstable prefix

Clients implementing this MSC early may use the profile key `gay.fomx.biography`.

## Dependencies

This MSC builds on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).
