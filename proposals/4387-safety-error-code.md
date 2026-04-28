# MSC4387: `M_SAFETY` error code

Homeservers and communities on Matrix establish rules and guidelines for what is acceptable. They use
safety tooling, such as moderation bots or [Policy Servers](https://spec.matrix.org/v1.18/client-server-api/#policy-servers),
to enforce those rules. Currently, the method for communicating to a user that something they did
broke those rules is lacking. It isn't clear to a user what they did, which rule they broke, or the
impact of any action taken against their account.

This MSC introduces a new error code to explain to users that safety tools acted on a request they
made. Rather than a generic `M_FORBIDDEN`, tools can use `M_SAFETY` to explain the reasons for the
action, and if the impact is permanent.

## Proposal

A new error code, `M_SAFETY` with HTTP 400 status code, is introduced on the following endpoints:

* [`POST /_matrix/client/v3/publicRooms`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3publicrooms)
  (room directory searching)
* [`POST /_matrix/federationv1/publicRooms`](https://spec.matrix.org/v1.16/server-server-api/#post_matrixfederationv1publicrooms)
  (room directory searching over federation)
* [`PUT /_matrix/client/v3/rooms/:roomId/send/:eventType/:txnId`](https://spec.matrix.org/v1.16/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
  (send message event)
* [`PUT /_matrix/client/v3/rooms/:roomId/state/:eventType/:stateKey`](https://spec.matrix.org/v1.16/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
  (send state event)
* [`PUT /_matrix/media/v3/upload/:serverName/:mediaId`](https://spec.matrix.org/v1.16/client-server-api/#put_matrixmediav3uploadservernamemediaid)
  (async media upload)
* [`POST /_matrix/media/v3/upload`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixmediav3upload)
  (regular media upload)
* [`GET /_matrix/client/v1/media/download/:serverName/:mediaId`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv1mediadownloadservernamemediaid)
* [`GET /_matrix/client/v1/media/download/:serverName/:mediaId/:fileName`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv1mediadownloadservernamemediaidfilename)
* [`GET /_matrix/client/v1/media/thumbnail/:serverName/:mediaId`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv1mediathumbnailservernamemediaid)
* [Deprecated `GET /_matrix/media/v3/download/:serverName/:mediaId`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixmediav3downloadservernamemediaid)
* [Deprecated `GET /_matrix/media/v3/download/:serverName/:mediaId/:fileName`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixmediav3downloadservernamemediaidfilename)
* [Deprecated `GET /_matrix/media/v3/thumbnail/:serverName/:mediaId`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)

Other endpoints, if not most of the Client-Server API, are likely good places to also receive this
new error code capability. Future MSCs are expected to add support as-needed to these other endpoints.
Some examples include message search, URL previews, invites, alias creation, etc.

The `M_SAFETY` error should be proxied from federation requests to the associated Client-Server API
request(s), if that federation request is linked to a client request. Servers SHOULD trim the error
to the schema described by this MSC before sending it to clients.

`M_SAFETY` is used when the server is refusing to serve results or content because the server has
determined that harm will be or is being caused. An example may be the server refusing to give results
for a room directory search because the keywords used are typically associated with searches for
illegal material.

When the server responds with `400 M_SAFETY`, the `error` message MUST be present. `harms` (described
below) SHOULD also be present alongside `expiry` if applicable. `expiry` is the approximate unix
timestamp in milliseconds for when the user can retry the request and probably get a different
response. Clients SHOULD NOT assume that the timestamp is precise. If the same input is unlikely to
succeed in a reasonable timeframe upon retry, the server should elide `expiry` or set it to `null`
to indicate it's an effectively permanent response. This makes `expiry` optional.

The allowable values for `harms` are defined by [MSC4456](https://github.com/matrix-org/matrix-spec-proposals/pull/4456).

An example of a permanent failure might be searching for illegal material in the room directory:

```jsonc
{
  "errcode": "M_SAFETY",
  "error": "No results are available for illegal materials", // required for M_SAFETY errors
  "harms": [
    "m.child_safety.csam"
  ],
  "expiry": null // or just don't have it here at all
}
```

A user might typically encounter temporary failures after first encountering a permanent failure. For
example, trying to mention too many users then sending a benign message:

```jsonc
{
  "errcode": "M_SAFETY",
  "error": "That message appears to be trying to mention 3000 people, which is too many.",
  "harms": [
    "m.spam",
  ]
  // permanent because `expiry` is missing: resending the message with its 3000 mentions won't work
}
```

*this is where the user says "fine then" after deleting their spammy message*

```jsonc
{
  "errcode": "M_SAFETY",
  "error": "You can't send messages right now because of an anti-spam measure. Try again in 5 minutes.",
  "harms": [
    // there might not be any articulable harm, so leave the array empty or elide `harms` entirely.
  ],
  "expiry": 1765312137979 // "5ish minutes from now"
}
```

Note that clients can (and SHOULD, where possible) render more detailed error messages than whatever
is provided in the `error` field. For example, if `harms` contains `m.child_safety.csam`, then the
client might opt to include links to Lucy Faithfull Foundation's [Stop It Now](https://www.stopitnow.org.uk/)
support website. The `error` field would be ignored in this situation, but remains human readable for
clients which don't override the rendering.

Multiple harms can be specified in the `harms` array to help indicate to the client that multiple
detailed messages might need appending together. For example, a client might implement something
like the following:

```js
let errorText = "Your message can't be sent for safety reasons:\n";

for (const harm in err.harms) {
  if (harm == "m.spam.fraud") {
    errorText += "* Contains fraudulent information, a scam, or phishing attempt.\n";
  } else if (harm == "m.violence.threats") {
    errorText += "* Appears threatening.\n"
  } // etc
}

showError(errorText);
```

## Potential issues

* As mentioned in the proposal, not all of the harms may be applicable to a server, or may be infeasible
  to scan/detect in the first place. There is no expectation that a server gains support for any of
  the harms. A server could always respond with an empty `harms` array, for example, or may not even
  implement `M_SAFETY` at all (this is not recommended).

* The server may choose to return a harm based on a different interpretation from the client, leading
  to some confusion by the user. This is not quite considered a bug or feature: the server perceived
  harm and prevented it, even if the messaging to the user is bit awkward. For example, the server
  returns `m.spam.flooding` for a message containing lots of messages but the client says that the
  "message has been repeated too many times" - this isn't entirely accurate, but still does tell the
  user that *something* is wrong about their message. Clients can reduce the impact of this situation
  by using general language like "Your message *may* have been repeated too many times or causes
  disruption to the room".

## Alternatives

The major alternative to this proposal is [MSC4228: Search Redirection](https://github.com/matrix-org/matrix-spec-proposals/pull/4228).
That MSC narrowly focuses on the room directory, whereas this proposal aims to address search
redirection *and* the communication issues encountered when safety tooling (like policy servers)
prevent an action.

Other alternatives include:

* Using `M_FORBIDDEN` as an error code instead. `M_FORBIDDEN` is used to describe a permissions or
  capability issue whereas `M_SAFETY` is intended to be more dynamic and less deterministic.

* Some variation of sub-errors, where there's a top level `errcode` with one or more "sub error codes".
  This could theoretically replace the `harms` array and be more generic outside of safety use cases,
  though practical examples aren't as easily found.

* Instead of pushing the rendering to the client, the server could provide pre-translated errors with
  [MSC4176](https://github.com/matrix-org/matrix-spec-proposals/pull/4176). `M_SAFETY` is compatible
  with MSC4176, but decided against using it directly due to concerns about server projects needing
  to sprout a translations layer and the complexities involved in doing that.

  Note that the `error` message returned alongside `M_SAFETY` is likely to be English, but like other
  errors in Matrix, is not required to be English.

## Security considerations

This MSC should *not* be used as a replacement for [`M_LIMIT_EXCEEDED`](https://spec.matrix.org/v1.16/client-server-api/#rate-limiting),
which is an error code specifically for performing actions too quickly. The "timeout" function of
`M_SAFETY` is meant as a discouraging factor rather than a mechanical limit - the timeout may not
be related to frequency of an action.

## Unstable prefix

While this proposal is not considered stable, implementations should use `ORG.MATRIX.MSC4387_SAFETY`
instead of `M_SAFETY`.

When transitioning from unstable to stable, implementations should:

* Populate `harms` with both the unstable and stable variants of relevant harms.
* Consider returning the unstable `ORG.MATRIX.MSC4387_SAFETY` error code for a short while after the
  error code becomes stable, but still combining stable & unstable `harms`, for maximum client support.

Implementations should not spend longer than 3 months after the relevant spec release returning unstable
prefixes alongside stable ones. Completing the transition sooner than 3 months after spec release is highly
encouraged.

## Dependencies

* [MSC4456: Harms taxonomy](https://github.com/matrix-org/matrix-spec-proposals/pull/4456) - Used to
  populate the `harms` array returned alongside the error code.
