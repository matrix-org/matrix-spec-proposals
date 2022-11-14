# MSC2713: Remove deprecated Identity Service endpoints

Implementations will have had plenty of time to adopt the new v2 API for Identity Servers, so
we should clean out the old endpoints.

All deprecated endpoints in the r0.3.0 Identity Service API specification are to be removed.

For completeness, this includes:

* `GET /_matrix/identity/api/v1`
* `GET /_matrix/identity/api/v1/pubkey/{keyId}`
* `GET /_matrix/identity/api/v1/pubkey/isvalid`
* `GET /_matrix/identity/api/v1/pubkey/ephemeral/isvalid`
* `GET /_matrix/identity/api/v1/lookup`
* `POST /_matrix/identity/api/v1/bulk_lookup`
* `POST /_matrix/identity/api/v1/validate/email/requestToken`
* `POST /_matrix/identity/api/v1/validate/email/submitToken`
* `GET /_matrix/identity/api/v1/validate/email/submitToken`
* `POST /_matrix/identity/api/v1/validate/msisdn/requestToken`
* `POST /_matrix/identity/api/v1/validate/msisdn/submitToken`
* `GET /_matrix/identity/api/v1/validate/msisdn/submitToken`
* `GET /_matrix/identity/api/v1/3pid/getValidated3pid`
* `POST /_matrix/identity/api/v1/3pid/bind`
* `POST /_matrix/identity/api/v1/3pid/unbind`
* `POST /_matrix/identity/api/v1/store-invite`
* `POST /_matrix/identity/api/v1/sign-ed25519`
