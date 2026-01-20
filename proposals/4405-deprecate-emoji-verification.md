# MSC4405: Deprecate the emoji method for SAS verification

Emojis are cute and fun.  They can be used to make things seem more friendly,
and to make a very technical process feel more approachable.  That was the hope
when the emoji method was introduced for [Short Authentication String (SAS)
verification](https://spec.matrix.org/v1.17/client-server-api/#short-authentication-string-sas-verification).

In practice, emojis present some usability problems.

## Background

When SAS authentication was first introduced, two methods were defined: emoji
and decimal.  The intention was that emoji would be the primary method, but for
clients who were unable to present emojis, the decimal method was added.  In
order to ensure that any pair of clients could verify, the decimal method was
made mandatory since it is the lowest common denominator.

### Problems with emojis

#### Communicating the emojis

When two people verify each other in person, they can look at each others'
devices and check that the emojis match directly.  However, if the verification
is not done in person, the two people need to communicate the emojis with each
other.  In most cases, the people would need to look at the emoji, and try to
determine how to describe the emoji to the other person.

To help with this, the spec defines standardised English names for the emojis,
and encourages client authors to collaborate on
[translations](https://github.com/matrix-org/matrix-doc/blob/master/data-definitions/).
However, this is not always sufficient.

Suppose that Alice's first language is German, and Bob's first language is
French.  They both speak English, but neither is fluent in it.  So Alice's
client shows Alice the German names for the emojis, and Bob's client shows Bob
the French names for the emojis.  Thus Alice and Bob need to translate the
German or French words into English.  While the emojis were chosen to be easily
describable, they are not all common words that would be known by non-native
speakers of a language, for example, 🌵 or ⌛.

A client could offer to show the names in multiple languages, but that would
complicate the user interface.

In addition, we made at least one error in choosing emojis: 🔧 is "spanner" in
en_GB, but "wrench" in en_US, so there may even be confusion between users
speaking the same language.  The spec picks "spanner" as the name, and if a
British and American user are verifying each other, the British user can explain
it to the American user.  But if two American users verifying each other may
need to figure out on their own what a "spanner" is.  (✈️ suffers a similar
problem, but less severely, since it is likely that users can figure out that
"aeroplane" is the same as "airplane".)

#### Differences in emoji representations

Clients may use different fonts for displaying emojis.  Some clients (such as
terminal-based clients) may not have a choice in which font is used.  Thus users
may not see the exact same images on the clients, causing them to wonder if the
difference is significant.  The standardised names were intended to help with
this, but in practice, it turns out that people still get confused.

### Decimal numbers do not have the same issues

Decimal numbers, the other method defined for SAS verification, do not have the
issues mentioned above.  Decimal numbers are widely understood (even in
languages that do not natively use Arabic numerals), so people will not struggle
to describe them to each other.  People who know enough of a language to have a
conversation in that language are likely to know enough about numbers in that
language be able to compare them.  And since the set of numbers is commonly
known, people do not need to worry about what differences in rendering are
significant.

## Proposal

The emoji method of SAS verification is deprecated.  Clients SHOULD only offer
to use the decimal method.

## Potential issues

### Decimal strings are longer

The decimal method specifies that three sets of 4 digits are presented to the
user, which means that users need to compare 12 items, compared with 7 emoji.
However, since clients also display the names along with the emojis, users are
presented with 14 items of information, so the difference in cognitive load may
not be that great.

In addition, in English, decimal digits are usually one syllable long, with 0
and 7 being two syllables long, whereas the English names of the emojis range
from one to three syllables long with the average length being closer to 2
syllables.  Therefore it should take similar effort to speak the strings out
loud.

Finally, emojis often need to be displayed at a larger size to be recognisable.
Along with the fact that the name is displayed with the emojis means that
decimals should not take any more visual space than emojis.

### Decimals look less friendly

Emojis make verification look more friendly, while decimals make verification
look more "techy".  And it is true that if something looks more friendly, then
people are more likely to find it easier to use.  However, I believe that the
actual usability benefits from deprecating the emoji method outweighs the
perceived usability of using emojis.

## Alternatives

[MSC4347](https://github.com/matrix-org/matrix-spec-proposals/issues/4347)
proposes to standardize the visual representation of the emojis.

[MSC4404](https://github.com/matrix-org/matrix-spec-proposals/pull/4404)
proposes to specify that the emoji names should be used rather than the visual
representations.  As a historical note, this would in some sense, make emoji
verification more similar to the original ZRTP, which SAS verification was based
on, and which uses a sequence of words as the Short Authentication String.

These two MSCs try to fix the issue of differences in emoji representation, but
do not fix the translation issue.

## Security considerations

None

## Unstable prefix

No new names are added, so no unstable prefix is needed.

## Dependencies

None
