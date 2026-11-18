# MSC4228: Search Redirection

**Content Warning**: This proposal discusses mechanisms to reduce searches for illegal or harmful
content on a homeserver. This proposal links to research which discusses the impact of Child Sexual
Abuse Material (CSAM).

Given the sensitive nature of the topic, comments, suggestions, and concerns may be sent directly to
the author. It is important that all members of our community contribute to a safe and positive review
atmosphere.

The author can be reached on Matrix at `@travis:t2l.io` or via email at `travisr@matrix.org`. If you
prefer to contact the Trust & Safety (T&S) team instead, please email `abuse@matrix.org`. The author
is a member of the T&S team, and will ensure a different member of the team reviews `abuse@matrix.org`
emails.

----

A common approach for tackling abuse is to prevent the content from being presented to users in any
way, disincentizing the use of the platform for sharing that particular type of content. The common
way users attempt to find content on Matrix is through the [room directory](https://spec.matrix.org/v1.12/client-server-api/#listing-rooms)
on their local server. With the current specification, there is no opportunity for a server to directly
say "you can't search for that here". There is additionally no way for the server to provide help and
support to the user when their search is denied.

This proposal adds an error code to the room directory search endpoints to "redirect" user searches
to help or supportive resources rather than serve rooms matching their query. This error code is
optional and intended to be used only when a user searches for illegal material. Users are expected
to be presented with resources which can help them stop, or not start, offences related to the content
instead of the content itself.

This proposal is heavily based upon the research of the Lucy Faithfull Foundation, where a
[chatbot was run on Pornhub UK](https://www.lucyfaithfull.org.uk/featured-news/stop-it-now-internet-watch-foundation-and-pornhub-launch-first-of-its-kind-chatbot-to-prevent-child-sexual-abuse.htm)
to intercept searches for explicit imagery of children and instead direct users to [Stop It Now](https://www.stopitnow.org.uk/).
More recently, the University of Tasmania published a [report](https://www.lucyfaithfull.org.uk/files/reThink_Chatbot_Evaluation_Report.pdf)
demonstrating that the 18-month approach works and led to a reduction in (potential) harm. An analysis
of the report can be found [on the Lucy Faithful Foundation's website](https://www.lucyfaithfull.org.uk/featured-news/pioneering-chatbot-reduces-searches-for-illegal-sexual-images-of-children.htm).

To assist in better user experience, servers using this MSC should consider using [MSC4176](https://github.com/matrix-org/matrix-spec-proposals/pull/4176)
as an optional dependency as well.

## Proposal

The room directory search endpoints (listed below) MAY return a `403 M_FORBIDDEN` error at the server's
discretion. The `error` message SHOULD be human readable and presented to the end user performing the
search. If [MSC4176](https://github.com/matrix-org/matrix-spec-proposals/pull/4176) or similar is
accepted, the translatable error is to be used as the human readable representation instead.

The endpoints affected are:
* [`POST /_matrix/client/v3/publicRooms`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3publicrooms)
* [`POST /_matrix/federation/v1/publicRooms`](https://spec.matrix.org/v1.12/server-server-api/#post_matrixfederationv1publicrooms)

For the federation endpoint specifically, the local user SHOULD have the remote server's error proxied
straight through to them, however some implementations may prefer to replace the error before serving
it to their users. This can help reduce the potential of remote Cross-Server Scripting (XSS) attacks.

When to return `403 M_FORBIDDEN` is left as an implementation detail.

### Example

A user makes a request to `/_matrix/client/v3/publicRooms` with a search term of `something illegal`.
The user's local server decides that it will not serve rooms matching that search term, and instead
responds with the following 403 error:

```json5
{
  "errcode": "M_FORBIDDEN",

  // Servers are encouraged to research phrasing which achieves their intended result. The example here
  // is based on zero research.
  "error": "No results are available for potentially illegal material. https://www.stopitnow.org.uk/helpline/ may be able to help you if you're searching for illegal content.",

  // Optional component from MSC4176
  "messages": {
    "en-US": "No results are available for potentially illegal material. https://www.stopitnow.org.uk/helpline/ may be able to help you if you're searching for illegal content.",
    "fr": "Aucun résultat n'est disponible pour le contenu potentiellement illégal. https://www.stopitnow.org.uk/helpline/ peut peut-être vous aider si vous recherchez du contenu illégal."
  }
}
```

The user sees a dialog containing the error message and link they can visit.

In another case, a user searches `remote.example.org` through their local server with a search term
of `something illegal`. Their server doesn't perform any filtering on the request, and passes it along
to `remote.example.org` over federation. `remote.example.org` intercepts the search and returns an
error similar to the one used in the prior example. The user's local server sees the error and decides
to proxy it to the user as-is. The user sees a dialog containing the error message and link they can
visit.

## Potential issues

Servers, particularly over federation, can use this to restrict or filter content beyond illegal
material. This is already possible by returning reduced result sets, or by returning errors in a
non-compliant manner.

## Alternatives

Specific error codes are a potential alternative, however due to the wide variety of illegal material
and jurisdictions, this proposal has determined that a single, generic, error code with specific message
more easily covers the use cases.

## Security considerations

Mentioned in the proposal text, it is possible for a remote server (or local server for that matter)
to return a malicious error message which the client may ultimately parse. Clients should avoid XSS
concerns by not parsing error messages, or by applying appropriate sandboxes and measures to contain
the scope of a potential breach. Similarly, servers should consider whether they proxy errors unmodified
from remote servers, or if they replace those errors. Some servers may establish "trusted remotes"
where they are okay to proxy errors and replace errors from all other servers.

## Safety considerations

This proposal is specifically intended to increase the relative safety of Matrix by reducing access
to content which is generally accepted to be illegal. Specifically, the matrix.org homeserver plans
to utilize this MSC (or similar) to disable access to CSAM, thus discouraging the content from being
created in the first place.

Additionally, as noted in the University of Tasmania's [report](https://www.lucyfaithfull.org.uk/files/reThink_Chatbot_Evaluation_Report.pdf),
this feature provides an opportunity to help individuals who may not know how to ask for help related
to their searches, and prevent offences from occurring.

## Unstable prefix

While this proposal is not considered stable, implementations should refrain from responding with 403
errors on the endpoints. This may mean an implementation is required to stay as an open Pull Request
until this MSC can become stable.

## Dependencies

This proposal supports [MSC4176](https://github.com/matrix-org/matrix-spec-proposals/pull/4176) as an
optional, value-add, dependency rather than blocker.
