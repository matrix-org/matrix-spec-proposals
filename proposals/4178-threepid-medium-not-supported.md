# MSC4178: Error code for Third Party Medium Not Supported

Homeservers may not always support adding email addresses or phone numbers to a user's account,
however, there is no error code to signal this situation. Synapse currently returns `M_UNKNOWN`
which leads to bad, untranslatable error messages.

## Proposal

Add the `M_THREEPID_MEDIUM_NOT_SUPPORTED` code to be returned by both
[`/account/3pid/email/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3account3pidemailrequesttoken)
and
[`/account/3pid/msisdn/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3account3pidmsisdnrequesttoken),
defined to mean that the homeserver does not support adding a third party identifier of that medium.

## Potential issues

None forseen

## Alternatives

A better UX would be for servers to advertise what third party identifiers that support adding so that clients can
inform users before they try to do so. This should be in addition rather than as alternative though: the clearest
possible API will come from having both.

## Security considerations

None forseen

## Unstable prefix

This is sufficiently simple that proving it on a large scale is unnecessary. The code should not be used in the open
before the MSC has been accepted.

## Dependencies

None
