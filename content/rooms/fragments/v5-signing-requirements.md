When validating event signatures, servers MUST enforce the
`valid_until_ts` property from a key request is at least as large as the
`origin_server_ts` for the event being validated. Servers missing a copy
of the signing key MUST try to obtain one via the [GET
/\_matrix/key/v2/server](/server-server-api#get_matrixkeyv2serverkeyid)
or [POST
/\_matrix/key/v2/query](/server-server-api#post_matrixkeyv2query)
APIs. When using the `/query` endpoint, servers MUST set the
`minimum_valid_until_ts` property to prompt the notary server to attempt
to refresh the key if appropriate.

Servers MUST use the lesser of `valid_until_ts` and 7 days into the
future when determining if a key is valid. This is to avoid a situation
where an attacker publishes a key which is valid for a significant
amount of time without a way for the homeserver owner to revoke it.
