# MSC4183: Additional Error Codes for submitToken endpoints

The [`POST
/_matrix/identity/v2/validate/email/submitToken`](https://spec.matrix.org/v1.11/identity-service-api/#post_matrixidentityv2validateemailsubmittoken)
and [`POST
/_matrix/identity/v2/validate/msisdn/submitToken`](https://spec.matrix.org/v1.11/identity-service-api/#post_matrixidentityv2validatemsisdnsubmittoken)
endpoints do not specify any specific error codes, instead relying on the common error codes defined in the identity
service API.

However, these common error codes don't have any codes to signal many errors that can occur in these APIs: most
obviously, that the token the user entered was incorrect.

This MSC can be considered similar to [MSC4178](https://github.com/matrix-org/matrix-spec-proposals/pull/4178) although
that MSC is for `requestToken` on the C/S API only.

The numerous `requestToken` endpoints (enumerated in the proposal section) in the C/S API also specify a `submit_url`
response parameter, defining their parameters to be the same as the Identity API's `submitToken` endpoints. Everything
this MSC specifies applies to these endpoint in the same way.

Note that the `POST` version of the email `submitToken` endpoint ([`POST
/_matrix/identity/v2/validate/email/submitToken`](https://spec.matrix.org/v1.11/identity-service-api/#post_matrixidentityv2validateemailsubmittoken))
is not generally used in practice: Sydent's emails include a link to click instead of the `submit_url` response field and
therefore use the `GET` version. Synapse does not implement the `POST` API for email validation for this reason. This
proposal updates both `POST` and `GET` versions for consistency.

## Proposal

Add the following specific error code as a code that can be returned by both
[`POST
/_matrix/identity/v2/validate/email/submitToken`](https://spec.matrix.org/v1.11/identity-service-api/#post_matrixidentityv2validateemailsubmittoken)
and [`POST
/_matrix/identity/v2/validate/msisdn/submitToken`](https://spec.matrix.org/v1.11/identity-service-api/#post_matrixidentityv2validatemsisdnsubmittoken):
 * `M_TOKEN_INCORRECT`: Indicates that the token that the user entered to validate the session is incorrect.

Note that we deliberately chose not to re-use `M_UNKNOWN_TOKEN` since that refers to an access token, whereas this
refers to a token that the user enters.

HTTP status code 400 should be used for this error.

Additionally specify that the following common error codes can be returned:
 * `M_INVALID_PARAM`: One of the supplied parameters in not valid.
 * `M_SESSION_EXPIRED`: The validation session is question has expired.

HTTP status code 400 should also be used for both of these errors.

Also apply the same change to the endpoints returned in the `submit_url` fields in the response to the various `POST requestToken` endpoints in the client-server API, i.e.:

 * [`POST /_matrix/client/v3/register/email/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3registeremailrequesttoken)
 * [`POST /_matrix/client/v3/register/msisdn/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3registerrequesttoken)
 * [`POST /_matrix/client/v3/account/3pid/email/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3account3pidemailrequesttoken)
 * [`POST /_matrix/client/v3/account/3pid/msisdn/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3account3pidmsisdnrequesttoken)
 * [`POST /_matrix/client/v3/account/password/email/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3accountpasswordemailrequesttoken)
 * [`POST /_matrix/client/v3/account/password/msisdn/requestToken`](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3accountpasswordmsisdnrequesttoken)

...to specify that response parameters and error codes are the same as the I/S API version, as well as request parameters.

## Potential issues

None foreseen.

## Alternatives

None considered.

## Security considerations

None foreseen.

## Unstable prefix

No unstable prefix is deemed necessary. Sydent already sends the common error codes and also sends
`M_NO_VALID_SESSION` if the code is incorrect. Once an identity server (or homeserver) switches to
use the new error code, clients (including homeservers proxying the IS API) may not recognise the
error condition correctly until updated to support the new code. We say that this is acceptable in
favour of avoiding the complexity of negotiating error codes with API versions. Since the identity
server is generally used via the homeserver now, most users of this API will not currently receive
a sensible error code in this situation anyway.

## Dependencies

None
