# MSC4485: Homeserver feature controls

Currently 'featured homeserver lists' are gaining more attention as community
members think about user onboarding. These would direct new users to homeservers
curated to provide a good experience. However, many homeservers don't have
the ability to accommodate any rate of growth, or a global audience. This
proposal provides a way to give server admins more responsive control over their
visibility on such lists.

## Proposal

This proposal adds a new well-known endpoint, `.well-known/matrix/featured`.
This endpoint responds with the following fields:

```jsonc
{
    "display": 0.5, // A number from 0 to 1 defining the probability that this homeserver should be shown in a list, with 0 being never and 1 being always.
    "languages": { // optional
        "allow": ["en", "en-US", "fr-FR"], // Optional. Language codes that the server should be featured in. If present, should not be shown for other languages.
        "deny": ["es"], // Optional. Language codes that the server should *not* be featured in.
    },
    "geos": { // optional
        "allow": ["GB"], // Optional. Country codes that the server should be featured in. If present, should not be shown for other countries.
        "deny": ["CN"], // Optional. Country codes that the server should *not* be featured in.
    },
}
```

Where language codes are specified, BCP 47 tags MUST be used. Where country
codes are specified, ISO 3166-1 alpha-2 codes MUST be used.

Implementations featuring this server in a list SHOULD fetch this endpoint, and
follow the rules to decide whether the server should be shown to users.

Implementations SHOULD follow the cache control headers specified in the
response, or otherwise MUST NOT cache the response for longer than an hour.
This is because servers MAY dynamically generate the response in reaction to the
amount of registrations they are getting.

To decide whether to show the server, featured homeserver lists should follow
the below algorithm. This MUST be evaluated for each unique user that views
the list:

- If the implementation encounters an error fetching this endpoint, for example
  it is missing, it SHOULD NOT display the server. Old lists MAY ignore this if
  they have many servers that do not have this endpoint, but should move towards
  following this rule over time.
- The implementation MUST generate a number in the range `( 0, 1 ]` with an
  approximately uniform distribution - that is from 0, exclusive, to 1,
  inclusive. If the result is greater than the value of the `display` property,
  it MUST NOT display the server.
- If the `languages` property is present:
    - The implementation should fetch the user's configured / spoken languages. If
      this is not possible, skip this section
    - If the user's primary language is present in the `deny` property, it SHOULD NOT
      display the server.
    - If the `allow` property is present, and none of the user's spoken languages are
      present, it SHOULD NOT display the server.
- If the `geos` property is present:
    - The implementation should fetch the user's geolocation, or otherwise their
      geographic jurisdiction. If this is not possible, skip this section.
    - If the user's geolocation is present in the `deny` property, it MUST NOT display
      the server.
    - If the `allow` property is present, and the user's geolocation is not present,
      it SHOULD NOT display the server.
- Otherwise, it SHOULD display the server.


## Potential issues

Because the algorithm includes randomness, reevaluating the algorithm on
each page load may result in a poor user experience as servers disappear
and reappear. Implementations should seed their random number generation
appropriately to ensure the list remains reasonably stable.

Methods for determining a user's geographic region and language often run into
cases where they do not get an accurate or useful result. Because of this,
clients may want to allow manual selection of these values.

Creating a new `.well-known` endpoint adds another HTTP round-trip for
clients or aggregators who are already fetching other .well-known endpoints
for discovery. This is considered an acceptable tradeoff here, because this
endpoint may want different caching and server-side treatment compared to other
`.well-known` endpoints.

## Alternatives

Homeservers could simply disable registrations, use registration tokens, or
block IPs from certain regions at the reverse-proxy level. However, this creates
a frustrating user experience: the user selects a server from a featured list,
attempts to register, and is met with an error. This proposal is preferable
because it filters the servers before the user attempts to sign up, and avoids
blocking users who already know which server they want to register at.

The `display` property could be a boolean. However, that reduces the ability of
servers to throttle registrations, rather than abruptly cutting them off. That
would make the proposal less useful for servers that want to maintain a specific
rate of growth.

## Security considerations

If a client fetches the rules by itself for evaluation, it leaks technical data
like the IP address to (a potentially large number of) third party servers.
For this reason, and to reduce load on servers, it is heavily recommended that
implementations proxy these rules, potentially bundling them with the server
list itself.

## Unstable prefix

While this endpoint is unstable, it should be served from
`.well-known/continuwuity/featured`

## Dependencies

None
