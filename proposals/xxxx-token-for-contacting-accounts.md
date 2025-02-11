# MSC0000: Tokens for Contacting Accounts

Federated networks eventually face the problem of spam. Without a central
instance to ensure some form of identification, a small number of people will
abuse the network for unwanted communication. Even a small number of abusers can
create a large number of unwanted contact requests. This annoys users and makes
the network unattractive compared with centralized networks.

A common approach to solve this problem is the implementation of a reporting
system, by which malicious users are reported and eventually blocked. However,
this requires the action of some users, thereby not ruling out the problem
entirely. Additionally, a reporting system requires some form of centralized
structure and/or causes a additional traffic and load on the server
infrastructure.


## Proposal

Baiscally, it's something like plus-addressing for e-mail, just with requiring
and managing a token.

The idea is to optionally require a token when first contacting another user.
For example: When starting a conversation with `@alice:matrix.org`, the user
`@bob:matrix.org` would have to either start the conversation with
`@alice::token1234:matrix.org` (syntax to be discussed) or enter the token
`token1234` in a subsequent prompt. Alice will be informed by only conversation
requests with a valid token.

The token `token1234` is one of several tokens Alice maintains within her Matrix
client. Tokens can be arbitrarily created and deleted. They can be easily
memorizable phrases like `connect`, or random ASCII stings.

Thus, for initiating a first contact, both persistent information of the account
(user `alice` and server `matrix.org`) and a flexible token is required. This
has several benefits:

* Users that only know `@alice:matrix.org` cannot contact Alice.
* When wanting to be contacted, Alice can give away her address+token (e.g.
  `@alice::token1234:matrix.org` or `@alice::connect:matrix.org`). If the token
  is spoiled because it is intentionally or unintentionally published,
  forwarded, or infringed, and unwanted contact requests appear on Alice's
  account, Alice can simply delete the token(s) `token1234` or `connect` from
  her list of valid tokens.
* If the token is displayed to Alice during the communication request, Alice can
  identify by which means Bob got this information (e.g. if Alice was contacted
  via `@alice::i_gave_this_token_to_peter:matrix.org`).


I have a few more ideas:

* Instead of blocking all contacting requests without a (valid) token, these
  requests could be marked as spam instead of being refused automatically. This
  may be configurable in the matrix client.
* There may be a token manager in the Matrix client that handles tasks like:
    * Show all valid tokens.
    * Create a new token from scratch or by a randomized string.
    * Make a token invalid.
    * Create a new token with a defined expiration date.
    * View previously valid tokens (including their period(s) of validity).
    * Organize tokens by folders and/or tags.
* The combination user+server+token can be displayed (and printed) as a QR code
  that can be read in by another Matrix client.
* When participating in (public) rooms and if wanted, a room-specific token can
  be automatically generated and published such that other members of the room
  can start a direct conversation.
* There should be no automatic feedback to the requester whether the token is
  valid or not, to avoid brute-force attacks.

## Potential issues

Of course, adding a third component next to username and server creates more
complexity, both to the system and to the user experience. Particularly
unexperienced users can be irritated. This problem can be encountered by making
the token method optional and disabled by default. Additionally, having the
option to merely mark contact requests without tokens as spam, might be a soft
landing.


## Alternatives

As mentioned above, a good reporting system of malicious users is an
alternative. However, at the cost of not blocking malicious users entirely by
design, additional load on the servers. A token system is not a full replacement
for a reporting system, though. Probably, it would be best to use both
alongside.

The token syntax introduced above is just an example. There are probably better
ways to implement it.


## Security considerations

* Users might be irritated by the token concept and enter a password instead.
* A wrong implementation can lead to people not being able to get reached.
* It must be ensured that both communication partners keep in contact, because
  otherwise Bob might not be able to reach Alice if Alice deleted the token.
* The token list must be stored encrypted in a safe location.


## Unstable prefix

not known.

## Dependencies

not known.
