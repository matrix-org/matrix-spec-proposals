# MSC3755: Pronouns

There are no pronoun labels in Matrix.
We often look to
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)
as the solution to this problem, but little progress has been made
and even with 1769, there would still need to be a representation of
pronouns.

## Proposal

Rather than creating new precedents like [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)
and waiting indefintley for them, this solution relies
on extending the m.room.member state event with a new optional field:
`m.pronouns.en`.
The name of this field uses a [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
code to classify a set of pronouns for the english language.

`m.pronouns.en` is a list of pronouns in order of user preference.

The pronouns each have the required fields `subject`
& `object`
as well as the optional fields `possessive`,
`possessive-determiner`,
`reflexive` and `singular`.
These are directly inspired from the site https://pronoun.is,
which gives examples for how to use a set of pronouns.
This set of pronouns only works with the english language
and cannot be used to specify pronouns for other languages
or blindly copied to do so.
A single text field can be considered problematic,
especially with neopronouns, as it can be hard for someone
who is new to a set of neopronouns to derive the others from just the
subject & object pronouns. We believe that specifying only
the subject and object pronouns can unfortunately lead to neopronouns
being ignored when referring to someone who has them.
Specifying each pronoun means that clients and bots can also use
the pronouns when referring to other users.


The following gives an example for the pronouns `They/Them`:

```
{
  "m.pronouns.en":[
    {
      "subject":"they",
      "object":"them",
      "possessive":"theirs",
      "possessive-determiner":"their",
      "reflexive":"themselves",
      "singular":"themself"
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
the `m.pronouns.en` field would instead be `ge.applied-langua.msc3755.pronouns.en` instead.

## Dependencies

None known.
