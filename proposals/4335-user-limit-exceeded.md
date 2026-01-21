# MSC4335: M_USER_LIMIT_EXCEEDED error code

Currently, Matrix homeservers lack a standardized error code to indicate when user-related limits
have been exceeded. This creates inconsistent client experiences when homeservers need to reject
operations due to per-user quotas, rate limits, or resource constraints.

Different implementations may return generic error codes like `M_FORBIDDEN` or `M_TOO_LARGE`, making
it difficult for clients to provide appropriate user feedback or implement proper retry logic.

A concrete use case for this is the
[fair usage limits introduced on the matrix.org homeserver](https://matrix.org/homeserver/pricing/#usage-limits).

This proposal introduces a new error code `M_USER_LIMIT_EXCEEDED` that homeservers can use to
signal when a user has exceeded their allocated limits, distinct from general rate limiting or
server-wide constraints. This improves the user experience by allowing clients to provide more
specific error messages and handle user-specific limitations appropriately.

## Proposal

This proposal adds a new [common error code]
`M_USER_LIMIT_EXCEEDED` to the Matrix specification. This error code should be returned when a user has exceeded
limits that are specifically associated with their account, such as:

* **Storage quotas**: When a user has exceeded their allocated storage space for smedia uploads,
  message history, or other persistent data.
* **Resource limits**: When a user has reached their maximum number of allowed rooms, devices,
  or other account-scoped resources.
* **Feature limits**: When a user has exceeded usage limits for specific features (e.g., number
  of public rooms they can create, number of invites they can send).
* **Account tier restrictions**: When a user's account type (free, premium, etc.) prevents them
  from performing certain operations.

The error response must also contain additional fields:

* `info_uri` string (required) - an opaque URI that the client can link the user to in order to get more context on the
  encountered limit and, if applicable, guidance on upgrading their account to increase the limit.
* `can_upgrade` boolean (optional, default `false`) - `true` means that the specific limit encountered can be increased.
  Otherwise it is a hard limit that cannot be increased.

The `info_uri` is "opaque" in the sense that the homeserver implementation may choose to encode
information, such as the type of limit encountered, within the URI but it may do so using an encoding of its choosing.

The homeserver may return *different* values for `info_uri` depending on what type of limit was
reached.

The HTTP response code should be chosen based on the specification for the individual endpoint. For
example, the most appropriate code for [`POST /_matrix/media/v3/upload`] would be `403 Forbidden`.

An example response body for the error might look as follows:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "You have exceeded your storage quota of 10GB",
  "info_uri": "https://example.com/homeserver/about?limit_type=quota",
  "can_upgrade": true
}
```

For a hard limit:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded their storage quota of 10GB",
  "info_uri": "https://example.com/homeserver/about?limit_type=quota"
}
```

### Applicable Endpoints

As it is a [common error code], `M_USER_LIMIT_EXCEEDED` may be returned by any Matrix Client-Server API endpoint.

For the purpose of illustration, practical examples could include:

* [`POST /_matrix/media/v3/upload`] - When the server is enforcing a storage quota.
* [`POST /_matrix/client/v3/rooms/{roomId}/invite`] - When invite limits (like maximum participant count) are exceeded.
* [`POST /_matrix/client/v3/createRoom`] - When the number or type of rooms is constrained.

### Distinction from Other Error Codes

This error code is distinct from:

* `M_LIMIT_EXCEEDED`: Used for general rate limiting that applies to all users or based on IP/client
* `M_FORBIDDEN`: Used for authorization failures or policy violations not related to usage limits
* `M_RESOURCE_LIMIT_EXCEEDED`: Used for server-wide resource constraints affecting all users
* `M_TOO_LARGE`: Used when a request is too large (file size, message length, etc.) regardless of user limits

## Potential issues

This error code does not specify the exact nature of the limit that was exceeded, which could
potentially lead to ambiguity. However, this is consistent with other Matrix error codes that
rely on the human-readable `error` field to provide specific details. Instead the `info_uri`
provides a way for the homeserver to apply arbitrary limits without the client having to understand
every type in advance.

The homeserver can choose to provide localised and personalised content on the `info_uri` if it
wishes.

The error code does not provide machine-readable information about current usage or limits,
which could be useful for clients to display progress bars or usage statistics. However, adding
such fields would require a more complex specification change and could be addressed in a future
MSC if deemed necessary.

### Backwards compatibility for existing clients

Existing clients which do not understand the new error code might have a degradation in UX as a
result of this new error code.

To understand the likelihood of this the common Web and iOS clients on the
[Matrix.org Ecosystem](https://matrix.org/ecosystem/clients/) web page were tested.

The results of this are attached as a
[comment](https://github.com/matrix-org/matrix-spec-proposals/pull/4335#issuecomment-3769636127)
on the proposal PR.

No significant degradation was identified for the clients tested.

## Alternatives

Several alternatives were considered for this proposal:

### Use M_RESOURCE_LIMIT_EXCEEDED

The existing [`M_RESOURCE_LIMIT_EXCEEDED`] looks very similar at first glance.

However, this code is explicitly referring to a limit being applied to the *server* and not to the *user* themselves:

> The request cannot be completed because the homeserver has reached a resource limit imposed on it.
> For example, a homeserver held in a shared hosting environment may reach a resource limit if it starts using too much
> memory or disk space.

As such this error code is currently rendered by
[existing](https://github.com/element-hq/element-web/blob/c96da5dbf8e20ced4a512a03a75c91f8680e8d40/src/i18n/strings/en_EN.json#L1112)
[clients](https://github.com/element-hq/element-ios/blob/2dc7b76c44545b3d027cdf0196c6af6eba8932f4/Riot/Assets/en.lproj/Vector.strings#L615)
as something similar to:

> This homeserver has exceeded one of its resource limits

As such, I think this message would be confusing to users  in the interim whilst clients updated their implementations and
that a new error code would be the best way forward.

### Add structured error information

Instead of a simple error code, a more complex error format
could include machine-readable fields for limit types, current usage, and maximum limits. While
this would provide more information, it would require a more significant change to the error
response format and could be added in a future MSC if needed.

### Multiple specific error codes

Separate error codes could be introduced for different types
of limits (e.g., `M_STORAGE_LIMIT_EXCEEDED`, `M_ROOM_LIMIT_EXCEEDED`). However, this approach
would require many new error codes and doesn't provide significant benefits over a single code
with descriptive error messages.

This would also prevent homeservers from implementing new limits without writing an MSC.

However, it would solve the translation problem without the homeserver needing to define every
translation.

### Define specific endpoints

Instead of making this a [common error code] instead it could be an
["other" error code](https://spec.matrix.org/v1.16/client-server-api/#other-error-codes) and have the specific endpoints
listed.

A downside of this is that if a homeserver wished to introduce a new type of limit or quota that was not foreseen, then
another MSC would be required to introduce it.

Instead, by making it a [common error code] the homeserver operator has flexibility over what types of limit they
choose without requiring further coordination with clients.

### Use server side translations

This could be similar to what is proposed generically by [MSC4176], but would need to support some form of markup rather
than just plain text in order to allow linking to external resources.

If the homeserver wanted to communicate a "soft" limit then it could return something like:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded a media upload limit",
  "messages": {
    "en": "You have reached your daily upload limit. More information on the usage limits that apply to your account is available <a href=\"https://matrix.org/homeserver/pricing/#usage-limits\">here</a>. You can upgrade to a Premium account to increase the limits <a href=\"https://account.matrix.org/account?action=org.matrix.plan_management\">here</a>.",
    "fr": "Vous avez atteint votre limite de téléchargement quotidienne. Pour plus d'informations sur les limites d'utilisation applicables à votre compte, cliquez <a href=\"https://matrix.org/homeserver/pricing/#usage-limits\">ici</a>. Vous pouvez passer à un compte Premium pour augmenter ces limites <a href=\"https://account.matrix.org/account?action=org.matrix.plan_management\">ici</a>.",
  }
}
```

Similarly for a "hard" limit:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded a media upload limit",
  "messages": {
    "en": "You have reached your daily upload limit. More information on the usage limits that apply to your account is available <a href=\"https://matrix.org/homeserver/pricing/#usage-limits\">here</a>.",
    "fr": "Vous avez atteint votre limite de téléchargement quotidienne. Pour plus d'informations sur les limites d'utilisation applicables à votre compte, cliquez <a href=\"https://matrix.org/homeserver/pricing/#usage-limits\">ici</a>.",
  }
}
```

Comparison:

* An advantage is that the homeserver can be as specific as it wishes with the messages. For example, the matrix.org
  homeserver can specifically refer to the usage plans that are available rather than having to be generic.
* The size of the error response payload increases significantly. [MSC4176] has some discussion around using a header
  such as `Accept-Language` or a query parameter to reduce the number of translations returned.
* A change in behaviour for clients: ordinarily the client picks the wording that is used to describe things in the
  client User Interface, this would move responsibility to the server. However, this is no different from how the
  [OAuth 2.0 API] makes the server responsible for translations relating to login and registration screens.

### Server side translation with client side translation fallback

This combines the benefits of above, with a client side fallback for servers that don't provide translations.

The client would use the value from `messages` if a matching language is found, otherwise it can fallback to use generic
strings like in the main proposal.

An example might be:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded a media upload limit",
  "info_uri": "https://example.com/homeserver/about?limit_type=quota",
  "can_upgrade": true,
  "messages": {
    "en": "You have reached your daily upload limit. More information on the usage limits that apply to your account is available <a href=\"https://matrix.org/homeserver/pricing/#usage-limits\">here</a>. You can upgrade to a Premium account to increase the limits <a href=\"https://account.matrix.org/account?action=org.matrix.plan_management\">here</a>.",
    "fr": "Vous avez atteint votre limite de téléchargement quotidienne. Pour plus d'informations sur les limites d'utilisation applicables à votre compte, cliquez <a href=\"https://matrix.org/homeserver/pricing/#usage-limits\">ici</a>. Vous pouvez passer à un compte Premium pour augmenter ces limites <a href=\"https://account.matrix.org/account?action=org.matrix.plan_management\">ici</a>.",
  }
}
```

So for English and French the client could show the specific messages provided by the homeserver, but for German the
client would pick the message with it's own translations.

A downside of this is inconsistency in wording across languages depending on what the server provided.

## Security considerations

None as only adding a new error code.

## Unstable prefix

While this proposal is being developed and refined, implementations should use the following:

* `ORG.MATRIX.MSC4335_USER_LIMIT_EXCEEDED` instead of `M_USER_LIMIT_EXCEEDED`
* `org.matrix.msc4335.info_uri` instead of `info_uri`
* `org.matrix.msc4335.can_upgrade` instead of `can_upgrade`

For example:

```json
{
  "errcode": "ORG.MATRIX.MSC4335_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded their fair usage limit of 2GB",
  "org.matrix.msc4335.info_uri": "https://example.com/homeserver/about?limit_type=quota",
  "org.matrix.msc4335.can_upgrade": true
}
```

### Include a URI to complete the upgrade action

An earlier version of the proposal included an `increase_uri` that could be attached as a UI button for the user to
take start the action of upgrading.

However, this led to [uncertainty](https://github.com/matrix-org/matrix-spec-proposals/pull/4335#discussion_r2582153412)
about what exactly would happen when the button is pressed.

To remove this uncertainty `increase_uri` was removed and the homserver gets to provide a single `info_uri` and it is
the responsibility of the homeserver to provide a UX that makes sense and is clear about what is happening.

## Dependencies

None.

[`POST /_matrix/media/v3/upload`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixmediav3upload
[`POST /_matrix/client/v3/rooms/{roomId}/invite`]: https://spec.matrix.org/v1.16/client-server-api/#thirdparty_post_matrixclientv3roomsroomidinvite
[`M_RESOURCE_LIMIT_EXCEEDED`]: https://spec.matrix.org/v1.16/client-server-api/#other-error-codes
[common error code]: https://spec.matrix.org/v1.16/client-server-api/#common-error-codes
[`POST /_matrix/client/v3/createRoom`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3createroom
[MSC4176]: https://github.com/matrix-org/matrix-spec-proposals/pull/4176
[OAuth 2.0 API]: https://spec.matrix.org/v1.16/client-server-api/#oauth-20-api
