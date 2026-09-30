# MSC4021: Archive client controls

The creation of archive.matrix.org indicates that search engine indexing of public Matrix rooms is a goal, but more
granular control over how rooms should be indexed and displayed in search engine results should be granted to room
admins.

The current solution determines indexing eligibility based on `world_readable` `public` history visibility, but this is
not an ideal solution because these settings only imply world readability within regular Matrix clients to most users,
as opposed to the wider internet. Most alternative social media platforms provide separate settings for profile
visibility and search engine indexing, for example.


## Proposal

Add an `m.room.archive_controls` state event where you can specify information about if and how you would like your
room to be crawled. The [/publicRooms API](https://spec.matrix.org/v1.7/client-server-api/#get_matrixclientv3publicrooms)
must relay this information to clients.

| key | type | value | description | required
|--|--|--|--|--
| `archive` | boolean | | Whether the room should be included in room directory listings which are indended to be viewed by the public |
| `robots` | [string] | Valid [robots meta rules](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag#directives) | A list of rules which should be included in a `robots` meta tag and/or [HTTP header](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag#xrobotstag-implementation) by public-facing clients. e.g. `["noarchive"]` or `["noindex", "nofollow"]`.
| `via` | string | Hostname | A hostname which should be set as the canonical archive URL. e.g. `"archive.matrix.org"`.

Public-facing clients like [matrix-public-archive](https://github.com/matrix-org/matrix-public-archive) should validate
these rules before returning them in a response.

When `archive` is `false`, clients which display a room directory intended for public internet consumption (e.g.
matrix-public-archive or matrix-static) should exclude that room from being displayed. Clients which provide access
to native Matrix users (e.g. Element) should ignore this setting.

When `via` is specified, the client should return a [rel=canonical link element](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls#rel-canonical-link-method)
and/or a [rel=canonical HTTP header](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls#rel-canonical-header-method)
with the response pointing to the archive URL on the specified hostname. This prevents the Matrix.org public archive
from returning duplicate content or taking precedence in search results over an organization's self-hosted archive.

For example, if `via` is set to `"archive.example.net"` in `#main:example.net`, the page at
https://archive.matrix.org/r/main:example.net/date/2023/05/28 should return this HTTP header:

```
Link: <https://archive.example.net/r/main:example.net/date/2023/05/28>; rel="canonical"
```


## Alternatives

- [MSC2219](https://github.com/matrix-org/matrix-spec-proposals/pull/2291) could provide an alternative method of
  specifying this information. However, this proposal includes the web archive metadata in the room directory API,
  in order to access this information efficiently (this is a [requirement](https://github.com/matrix-org/matrix-public-archive/issues/47#issuecomment-1536938601)
  for the matrix-public-archive project, for example). This proposal also allows rooms to opt-out of publicly accessible
  room directories without clients like matrix-public-archive needing to join the room to read the state, and should
  be interpreted by any client built for public web crawler access rather than [specific bots/clients](https://github.com/matrix-org/matrix-spec-proposals/pull/2291/files#diff-2b62d9e1c5ef21f7e10959da64da4000a69069b4dfb5d436db30d12c6bd23cb7R21-R23)
