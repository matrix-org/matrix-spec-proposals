# MSC4312: Resetting cross-signing keys in the OAuth world

Matrix v1.15 added new [OAuth APIs] for authentication. As of writing, these APIs are not compatible
with the existing [User-Interactive Authentication (UIA)] mechanism that is used on a number of
endpoints. This is not problematic in most cases because these endpoints cover actions that can now
be preformed in the authorization server's web UI. One notable exception, however, is
[`/_matrix/client/v3/keys/device_signing/upload`] which clients use to publish their cross-signing
keys. This endpoint requires UIA when previously uploaded keys are being replaced, for instance
because the user lost their recovery key. OAuth knows nothing about cross-signing keys and,
consequently, the spec labels this endpoint as unusable:

> **WARNING:** When this endpoint requires User-Interactive Authentication, it cannot be used when
> the access token was obtained via the OAuth 2.0 API.

This is obviously not practical and unofficial workarounds have been invented to enable resetting
one's cross-signing keys in the client / homeserver / authorization server triangle. This proposal
documents these workarounds.

## Proposal

Clients that have authenticated via the new [OAuth APIs] continue to use
[`/_matrix/client/v3/keys/device_signing/upload`] to replace cross-signing keys. Homeservers
continue to enforce UIA on the endpoint but MUST only use a single stage `m.oauth`
together with a URL that points to the authorization server's account management UI.

``` json5
{
  "session": "$ARBITRARY",
  "flows": [{
    "stages": ["m.oauth"]
  }],
  "params": {
    "m.oauth": {
      "url": "$AUTHORIZATION_SERVER_ACCOUNT_MANAGEMENT_URL"
    }
  }
}
```

The client then instructs the user to approve the reset of their cross-signing keys using the
provided URL. How exactly that approval is achieved is an implementation detail between the
authorization server and the homeserver[^1]. The required end result is that after approving, the
client can complete the stage without further parameters.

``` json5
{
  "auth": {
    "session": "$FROM_ABOVE"
  },
  "master_key": ...
  ...
}
```

To facilitate the navigation, a new action `org.matrix.cross_signing_reset` is introduced and MAY be
used in the `account_management_actions_supported` authorization server metadata field from
[MSC4191]. Servers SHOULD use this action to deep link the user if the authorization server supports
it.

## Potential issues

Semantically, resetting cross-signing keys doesn't fall into the authorization server's domain. The
scheme outlined above increases coupling between the authorization server and the homeserver and
makes it more difficult to use off-the-shelve OAuth authorization servers.

## Alternatives

Rather than approving cross-signing reset specifically, the authorization server could provide
mechanisms for temporary scope elevation. An example of a potential mechanism that could help
achieve this is the [RFC 9470 OAuth 2.0 Step Up Authentication Challenge Protocol]. Theoretically
such a mechanism could act as full replacement for UIA in the CS API where protection is needed for
sensitive actions. However, there is no proposal on how this would be applied to the CS API and
therefore it is proposed to codify this present mechanism that does allow for the specific
cross-signing reset action.

## Security considerations

Since the details of how approval is communicated between the authorization server and the
homeserver are left unspecified, implementations could introduce security risks through their
concrete choice of protocol. The temporary lifting of UIA that happens between
[matrix-authentication-service] and Synapse, for instance, creates a time window in which an
attacker with an access token could take over the account.

## Unstable prefix

While this MSC is not considered stable, `m.oauth` should be referred to as
`org.matrix.cross_signing_reset`.

## Dependencies

This proposal doesn't strictly depend on but works better with [MSC4191].

[^1]: [matrix-authentication-service], for instance, uses a [Synapse admin API] to temporarily lift
    UIA on the endpoint.

  [OAuth APIs]: https://spec.matrix.org/v1.15/client-server-api/#oauth-20-api
  [User-Interactive Authentication (UIA)]: https://spec.matrix.org/v1.15/client-server-api/#user-interactive-authentication-api
  [`/_matrix/client/v3/keys/device_signing/upload`]: https://spec.matrix.org/v1.15/client-server-api/#post_matrixclientv3keysdevice_signingupload
  [MSC4191]: https://github.com/matrix-org/matrix-spec-proposals/pull/4191
  [RFC 9470 OAuth 2.0 Step Up Authentication Challenge Protocol]: https://datatracker.ietf.org/doc/rfc9470/
  [matrix-authentication-service]: https://github.com/element-hq/matrix-authentication-service
  [Synapse admin API]: https://element-hq.github.io/synapse/latest/admin_api/user_admin_api.html#allow-replacing-master-cross-signing-key-without-user-interactive-auth
