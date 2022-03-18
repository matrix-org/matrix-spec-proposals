# MSC3755: Pronouns

There are no pronoun labels in Matrix.
We are often look to
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/msc1769/proposals/1769-extensible-profiles-as-rooms.md)
as the solution to this problem, but little progress has been made
and even with 1769, there would still need to be a representation of
pronouns.

## Proposal

Rather than creating new precedents like [msc1769](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/msc1769/proposals/1769-extensible-profiles-as-rooms.md)
and waiting indefintley for them, this solution relies
on extending the m.room.member event with a new field: `ge.applied-langua.ge.pronouns.english`.

`ge.applied-langua.ge.pronouns.english` is a list of pronouns in order of user precedence.

The pronouns each have the required fields `ge.applied-langua.ge.pronouns.english.subject`
& `ge.applied-langua.ge.pronouns.english.object`
as well as the optional fields `ge.applied-langua.ge.pronouns.english.possessive`,
`ge.applied-langua.ge.pronouns.english.possessive-determiner`,
`ge.applied-langua.ge.pronouns.english.reflexive` and `ge.applied-langua.ge.pronouns.english.singular`

The following gives an exmample for the pronouns `They/Them`:

```
{
  "ge.applied-langua.ge.pronouns.english":[
    {
      "ge.applied-langua.ge.pronouns.english.subject":"they",
      "ge.applied-langua.ge.pronouns.english.object":"them",
      "ge.applied-langua.ge.pronouns.english.possessive":"theirs",
      "ge.applied-langua.ge.pronouns.english.possessive-determiner":"their",
      "ge.applied-langua.ge.pronouns.english.reflexive":"themselves",
      "ge.applied-langua.ge.pronouns.english.singular":"themself"
    }
  ]
}
```

### Disclaimer

The author is not a linguist and knows nothing about natural language.

## Potential issues

Changing avatars and displayname is already a cause of concern for
users who are in lots of rooms as it takes a long time on Synapse to
update the member event for all the rooms.

The profile directory may also leak someone's pronouns that are used
only in certain contexts and out them. Unsure if this has been fixed yet.

This is very english centric and only specifies pronouns for english.

## Alternatives

* An extensible state event combined with [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/msc1769/proposals/1769-extensible-profiles-as-rooms.md).


## Security considerations

No considertion taken so far.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

None known.
