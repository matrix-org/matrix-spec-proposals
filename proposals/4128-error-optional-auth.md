# MSC4128: Error on invalid optional authentication

## Introduction

[MSC4026](https://github.com/matrix-org/matrix-spec-proposals/pull/4026) added optional authentication
to the `/versions` endpoint, the first of the spec to do so. However, this MSC did not specify the behaviour
of servers in cases where the authentication or identity assertion failed .

This has lead to some implementations of the spec expecting the request to go through even when the auth is
invalid, while some servers respond with an error in the above cases, damaging interoperability.

## Proposal

In cases where authentication is optional and provided, servers should respond with an error when the authentication
token is invalid. Appservice identity assertion should also not happen on endpoints with optional authentication, as
homeserver administrators are not likely to treat some appservice users differently to others for endpoints where
authentication is not required in the first place.

## Potential issues

Once merged, implementations unaware of this change may error unexpectedly, as they previously depended on such
endpoints not returning an error. However, since this has already occurred with some servers already doing this,
it is best to specify this so that implementers know to account for this.

## Alternatives

Specifying that servers must **not** error in these cases is a possible alternative, but it is undesirable since
if the implementation is doing something wrong, they should be made aware of it as soon as possible.

## Security considerations

None considered.

## Unstable prefix

Due to this MSC simply enforcing that servers should error in specific conditions, no unstable prefix is applicable.

## Dependencies

None.
