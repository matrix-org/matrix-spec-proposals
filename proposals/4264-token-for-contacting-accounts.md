# MSC4264: Tokens for Contacting Accounts or Joining Semi-Public Rooms

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

This problem does not just apply to making a first contact with individuals, but
generally to requests joining semi-private rooms.

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
* When wanting to be contacted, Alice must state her address+token (e.g.
  `@alice::token1234:matrix.org` or `@alice::connect:matrix.org`). This could be
  done both outside and inside of Matrix, e.g. when giving her
  address+toke+server, showing/printing a QR code, showing a token in addition
  to the address in public rooms (if wanted), or else.
* If the token is spoiled because it is intentionally or unintentionally
  published, forwarded, or infringed, and unwanted contact requests appear on
  Alice's account, Alice can simply delete the token(s) `token1234` or `connect`
  from her list of valid tokens.
* If the token is displayed to Alice during the communication request, Alice can
  identify by which means Bob got this information (e.g. if Alice was contacted
  via `@alice::i_gave_this_token_to_peter:matrix.org`).


There are a few more ideas:

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
* This feature could be used not just for first communication attempts to
  individuals, but generally to requests joining semi-public rooms:
  * A semi-public room can be configured to be visible to the world, but only
    accept requests to join if users enter a valid token.
  * Instead of entering a valid token upon request, one could use the same
    syntax, like `#semi_public_room::token:matrix.org`.
  * Admins of the semi-public room can edit the token list.
  * Instead of requiring the token to entered when joining, a request could also
    be sent to group admins (configurable).
  * This could possibly further expanded to spaces as well.


An implementation would probably have to cover both the server and the client
side.
* Server side:
  * The communication within and between servers has to be enhanced to allow and
    deal with the token part in the address.
  * The list of valid tokens (and their validity dates) must be stored on the
    server side. This is because users using multiple clients would not want to
    maintain multiple token lists on each client, which also may interfere with
    each other.
      * For semi-public rooms, there must be a list of valid tokens for each
        each semi-public room.
  * A communication between server and client to sync the token list.
  * The decision whether a contact attempt is allowed or rejected should be made
    on the server side.
  * Depending on the configuration, there might be no need to inform the client
    of rejected communication attempts. Alternatively, the server may pass
    information about rejected communication attempts to the client, thereby
    allowing the client to merely flag it as spam.
* Client side:
  * A token manager with the requirements stated above.
  * A communication between server and client to sync the token list.
  * Showing the token to the user upon communication requests (and also in the
    chat history).
  * Semi-public rooms must be made identifiable as such.

An implementation could possibly rely upon [MSC4155]. It's
`m.invite_permission_config` might be amended to include the token list,
possibly including expiration dates as well. If implemented in this way, this
MSC might be seen as an extension to [MSC4155].


## Potential issues

Of course, adding a third component next to username and server creates more
complexity, both to the system and to the user experience. Particularly
unexperienced users can be irritated. This problem can be encountered by making
the token method optional and disabled by default. Additionally, having the
option to merely mark contact requests without tokens as spam, might be a soft
landing.

User IDs are limited to 255 bytes. So depending on the length of your ID, your
options for defining sub IDs could be limited. This issue might be solved by not
treating the token to be part of the user ID but rather a separate part (with
again e.g. 255 bytes).


## Alternatives

As mentioned above, a good reporting system of malicious users is an
alternative. However, at the cost of not blocking malicious users entirely by
design, additional load on the servers. A token system is not a full replacement
for a reporting system, though. Probably, it would be best to use both
alongside.

Some of the block- and allow-list filtering methods for invites in [4192] might
be further alternatives.

The token syntax introduced above is just an example. There are probably better
ways to implement it.

Instead of using the word 'token', a more precise word could be found.
[RFC5233](https://datatracker.ietf.org/doc/html/rfc5233) for a comparable
feature in e-mail describes it as 'detail'. All proposals are welcome. Some
ideas are: token, detail, secret, access_token, access_secret, voucher,
room_password, ...

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

[MSC4155]: https://github.com/matrix-org/matrix-spec-proposals/pull/4155
