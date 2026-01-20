# MSC4404: Compare emoji by name rather than image

## Problem

SAS verification via emoji comparison is problematic because users treat the request to compare
emoji literally, and then trip over whether the images literally match, as well as whether
the label of the emoji is the same (causing problems with i18n).

One solution is to hardcode the emoji representation into the spec as per 
[MSC4347](https://github.com/matrix-org/matrix-spec-proposals/pull/4347).
However, this poses more problems: as a client implementor, i don't want *any* of the pixel layout
of my app dictated by a communication protocol - i want to pick the aesthetics, a11y,
branding, image licence, theming, UI idiom (TUI, XR, Braille reader, etc) that works for me.

## Proposal

 * Advise clients to ask users to compare SAS by name rather than image. "Do the words match?" rather
   than "Do the emoji match?".
 * Pass an optional `accept_languages` parameter in the `content` block of the m.key.verification.start` and
   `m.key.verification.accept` messages containing a list of accepted languages, so that the other party knows
   what languages to display the SAS words in for comparison purposes.
 * Recommend that clients should display the initiator's language first on both screens, followed by any other
   translations in brackets if the users don't share a common accepted languages.

Example:

```json5
{ // from Alice (UI in en_GB)
  "content": { 
    "from_device": "AliceDevice",
    "accept_languages": ["en_GB", "en", "fr_FR"],
    ...
  },
  "type": "m.key.verification.start"
}
```

```json5
{ // from Bob (UI in de_DE)
  "content": {
    "accept_languages": ["de_DE"],
    ...
  },
  "type": "m.key.verification.accept"
}
```

Would result in Alice and Bob both seeing something like this in the UI as the verification string:

```
   🍄       ⌛        🌽      🌏
Mushroom Hourglass  Corn   Globe  
 (Pilz)  (Sanduhr) (Mais) (Globus)

      🍎      ⌛       ⚓
    Apple  Hourglass Anchor
   (Apfel) (Sanduhr) (Anker)

```

We can also recommend that emoji are typically presented in a row of 4 and a row of 3 for
consistency and ease of comparison, but this would be a MAY rather than a MUST.

## Potential issues

 * The user could get confused by seeing the 'wrong' language turning up, especially if it's
   in a different alphabet, and get hung up trying to decrypt the CJK or Cyrillic or whatever
   to try to check whether they match or not.  This seems *very* unlikely if the correct words
   are shown parenthetically below in the right language.
 * Similarly, if there is zero shared language between the users, then they might not be able to
   read the other user's language in order to express the word in question.  This is going to
   be a problem for normal communication too; they should use machine translation or buy a
   dictionary for support.
 * This (optionally) leaks the language of the user to the peer being verified (and the servers
   in between), which could be quite sensitive in terms of outing people's nationalities and
   implied geolocale.

## Alternatives

 * Emoji comparison is basically flawed, and while fun and quirky, has awkward edge cases like this.
   We could/should deprecate it in favour of simple decimal SAS comparison, but we're stuck with
   emoji for compatibility, hence this incremental fix.
 * We could hardcode emoji visual representation into the spec, as per
   [MSC4347](https://github.com/matrix-org/matrix-spec-proposals/pull/4347). However:
    * this has the problems outlined in the Problem section above:
      * as an app developer, i want to pick the aesthetics, accessibility, branding, image licencing, theming,
        UI idiom (TUI, XR, Braille reader, etc) for my own app, and not have it dictated by a protocol.
    * and also makes the spec even more sprawling and bloated and is a much bigger change to land and maintain.
    * it also hardcodes any 'bugs' in the image representation into the spec without any possible migration mechanism -
      e.g. if one day we decide that a handgun emoji should be displayed as a waterpistol rather than a revolver, etc.

## Security considerations

 * Optionally leaking your language to the person you're verifying is metadata leakage which could
   be avoided if we used decimal (or QR) verif.
 * Getting this wrong discourages cross-user verification and harms E2E trust.

## Unstable prefix

None

## Dependencies

None