# MSC4178: Error codes for requestToken

There are a number of ways that sending a token to validate a third party identifier can go wrong.
The requestToken API, however, has a very limited number of error codes that it can return.

Firstly, homeservers may not always support adding email addresses or phone numbers to a user's account,
however, there is no error code to signal this situation. Synapse currently returns `M_UNKNOWN`
which leads to bad, untranslatable error messages.

Secondly, the supplied third party identifier may be invalid.

## Proposal

Firstly, Add the `M_THREEPID_MEDIUM_NOT_SUPPORTED` code to be returned by both
[`POST /account/3pid/email/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3account3pidemailrequesttoken)
and
[`POST /account/3pid/msisdn/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3account3pidmsisdnrequesttoken),
defined to mean that the homeserver does not support adding a third party identifier of that medium.

Secondly, allow these endpoints to also return `M_INVALID_PARAM`, to indicate that the third party address
was not valid for that medium (eg. not a valid phone number).

For both of these codes, HTTP status code 400 should be used.

## Potential issues

None foreseen.

## Alternatives

A better UX would be for servers to advertise what third party identifiers they support adding so that clients can
inform users before they try to do so. This should be in addition rather than as alternative though: the clearest
possible API will come from having both.

## Security considerations

None foreseen.

## Unstable prefix

This is sufficiently simple that proving it on a large scale is unnecessary. The code should not be used in the open
before the MSC has been accepted.

## Dependencies

None
