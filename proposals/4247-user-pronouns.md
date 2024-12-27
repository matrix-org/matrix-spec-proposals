# MSC4247: User Pronouns

Many users of Matrix put pronouns in display names. However, that causes screen
clutter. This proposal defines a standardized pronouns field on top of
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

## Proposal

Profiles may have optional `m.pronouns` and `m.pronouns.secondary` fields as a
dictionary. These fields can be fetched through the
[profile API endpoints](https://spec.matrix.org/unstable/client-server-api/#profiles).
Clients should parse this and use these instead of they/them where possible.

### Example

```json
{ 
    "avatar_url": "…", "displayname": "…",
    "m.pronouns": {
        "subject": "it",
        "object": "it", 
        "possessive_determiner": "its", 
        "possessive_pronoun": "its", 
        "reflexive": "itself"
    }, 
    "m.pronouns.secondary": { 
        "subject": "she",
        "object": "her",
        "possessive_determiner": "her",
        "possessive_pronoun": "hers",
        "reflexive": "herself"
    }
}
```

## Potential issues

Some users may not want to publish pronouns to others, although that is out of
scope for this MSC. Some users may also complain about "woke", although
pronouns are a basic part of langauge.

## Security issues

None.

## Unstable prefix

Clients and servers wishing to implement this early may use
`io.fsky.nyx.pronouns` and `io.fsky.nyx.pronouns.secondary`.
