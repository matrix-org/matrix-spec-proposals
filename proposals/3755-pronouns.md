# MSC3755: Pronouns

There are no pronoun labels in Matrix.
We are often look to
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)
as the solution to this problem, but little progress has been made
and even with 1769, there would still need to be a representation of
pronouns.

## Proposal

Rather than creating new precedents like [msc1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)
and waiting indefintley for them, this solution relies
on extending the m.room.member event with a new field: `m.pronouns.english`.

`m.pronouns.english` is a list of pronouns in order of user precedence.

The pronouns each have the required fields `m.pronouns.english.subject`
& `m.pronouns.english.object`
as well as the optional fields `m.pronouns.english.possessive`,
`m.pronouns.english.possessive-determiner`,
`m.pronouns.english.reflexive` and `m.pronouns.english.singular`

The following gives an exmample for the pronouns `They/Them`:

```
{
  "m.pronouns.english":[
    {
      "m.pronouns.english.subject":"they",
      "m.pronouns.english.object":"them",
      "m.pronouns.english.possessive":"theirs",
      "m.pronouns.english.possessive-determiner":"their",
      "m.pronouns.english.reflexive":"themselves",
      "m.pronouns.english.singular":"themself"
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

The profile directory may also [leak](https://github.com/matrix-org/synapse/issues/5677)
someone's pronouns that are used only in certain contexts and out them.

This is very english centric and only specifies pronouns for english.

Pronouns could be used maliciously by inserting abusive text in their place.

## Alternatives

* An [extensible](https://github.com/matrix-org/matrix-spec-proposals/pull/1767)
state event combined with [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769).

* An alternative involving per room profiles and spaces [MSC3189](https://github.com/matrix-org/matrix-spec-proposals/pull/3189).


## Security considerations

No considertion taken so far.

## Unstable prefix

While this MSC is not considered stable by the specification, implementations *must* use
`ge.applied-langua.msc3755` as a prefix to denote the unstable functionality. For example,
the `m.pronouns.english` field would instead be `ge.applied-langua.msc3755.pronouns.english` instead.

## Dependencies

None known.
