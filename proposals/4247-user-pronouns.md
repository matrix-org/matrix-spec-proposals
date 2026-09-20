# MSC4247: User Pronouns

Many users of Matrix put pronouns in display names. However, that causes screen
clutter. This proposal defines a standardized pronouns field on top of
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

## Proposal

Profiles MAY have an optional `m.pronouns` field as an
array. These fields can be fetched through the
[profile API endpoints](https://spec.matrix.org/unstable/client-server-api/#profiles).

### Example

```json
{ 
    "avatar_url": "…", "displayname": "…",
    "m.pronouns": [
        {
            "language": "en",
            "summary": "it/its"
        },
        {
            "language": "en",
            "summary": "she/her"
        }
    ]
}
```
The example uses it/its pronouns followed by she/her pronouns, both in English.
The array is ordered by preference, `language` SHOULD be a
[BCP-47](https://www.rfc-editor.org/rfc/bcp/bcp47.txt) language code, and
clients MUST render the `summary` for the pronouns, and clients SHOULD only show
pronouns in the user's language.

## Potential issues

Some users may not want to publish pronouns to others, although that is out of
scope for this MSC.

## Security issues

Potential for abusive content in the `summary` of pronouns.

## Unstable prefix

Clients and servers wishing to implement this early may use
`io.fsky.nyx.pronouns`.
