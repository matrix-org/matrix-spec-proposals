# MSC4450: Identity Provider selection for User-Interactive Authentication with Legacy Single Sign-On

When a client presents a user with a User-Interactive Authentication flow using the Single Sign-On
authentication type (`m.login.sso`), the client must direct the user to complete the flow in the
browser, using the fallback URL at `/_matrix/client/v3/auth/m.login.sso/fallback/web?session=<session ID>`.

(Note that despite being called 'fallback', there is no other method for completing `m.login.sso`.)

It is possible for a homeserver to have multiple Single Sign-On providers (also known as 'Identity Providers').

There is currently no mechanism for the client to indicate a preference/selection of identity provider
to be used for the User-Interactive Authentication flow.

This proposal adds such a mechanism.


## Proposal

An `idp_id` query parameter is introduced to the `m.login.sso` fallback endpoint:

```
/_matrix/client/v3/auth/m.login.sso/fallback/web?session=<session ID>&idp_id=<IDP ID>
```

The IDP IDs (Identity Provider identifiers) are the same as used in the [`GET /_matrix/client/v3/login/sso/redirect/{idpId}`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3loginssoredirectidpid) endpoint.

If the Identity Provider identifier is not set, the homeserver MUST act the same as before this MSC
was introduced, for example automatically selecting an Identity Provider or offering a web user interface
for the user to do so manually.

If the Identity Provider identifier refers to an Identity Provider that is non-existent,
not associated to the user or otherwise invalid,
the homeserver MAY either treat the parameter as not having been set, or display an error to the user,
depending on which is more appropriate for the homeserver's circumstances.


## Potential issues

- Legacy authentication is already somewhat in the process of being replaced by OAuth 2.0 authentication,
  so perhaps it's not worth proceeding with changes to legacy authentication.


## Alternatives

- We could instead make it possible for the homeserver to offer multiple `m.login.sso` authentication options
  and have a generic authentication 'subtype' system for selecting one of multiple independent `m.login.sso`
  authentication options.
  
  This 'subtype' approach could generalise beyond `m.login.sso`.
  
  The fallback for authentication subtypes could then be exposed at e.g. `/_matrix/client/v4/auth/<auth type>/<auth subtype>/fallback/web?session=<session ID>`


## Security considerations

None anticipated.


## Unstable prefix

Whilst this MSC is unstable, the unstable-prefixed query parameter `io.element.idp_id` should be used in place of `idp_id`.


No unstable feature advertisement in `/versions` is necessary, as homeservers ignore extraneous query parameters and so
homeservers which do not support this feature will ignore the added query parameter.


## Dependencies

None.
