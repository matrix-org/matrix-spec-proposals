# MSC2078 - Sending Password Reset Emails via the Homeserver

This MSC proposes removing the current requirement of the identity server to send password reset tokens, and allows homeservers to implement the functionality instead. The intention is to put less trust in the identity server which is currently one of the most centralised components of Matrix. As it stands, an attacker in control of a identity server can reset a user's password if that user has registered a third-party identifier (3PID) with that identity server, due to itself also handling the job of confirming the user's control of that identity.

The MSC aims to simply clarify that homeservers can take on the responisibility of sending password reset tokens themselves.

## Proposal

Currently when a client requests a password reset, they make a call to either [/_matrix/client/r0/account/password/email/requestToken](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-account-password-email-requesttoken) or [/_matrix/client/r0/account/password/msisdn/requestToken](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-account-password-msisdn-requesttoken). This request is supplied all the necessary details as well as a `id_server` field containing the address of a trusted identity server which the user has used in the past to bind their 3PID. Understand that it is recommended for the homeserver to only grant the request if the given identity server is in a trusted list.

The `id_server` field is currently required as the homeserver must know where to proxy the request to. This MSC proposes not to change the requirements of this field. Instead, it asks to clarify that the homeserver is allowed to not proxy the request, but carry it out itself. This would mean the homeserver can both send password reset tokens (via email or sms), as well as accept requests to [/_matrix/identity/api/v1/validate/email/submitToken](https://matrix.org/docs/spec/identity_service/r0.1.0.html#post-matrix-identity-api-v1-validate-email-submittoken) to verify that token.

Thus, this proposal really only requests that it be clear that a homeserver does not need to proxy requests to `/requestToken`, and instead can ignore the `id_server` field and perform emailing/sms message sending by itself.

## Tradeoffs

If homeservers choose to not proxy the request, they will need to implement the ability to send emails and/or sms messages. This is left as a detail for the homeserver implementation.

## Future Considerations

At some point we should look into removing the `id_server` field altogether and removing any email/sms message sending from the identity server. This would drastically reduce the amount of trust needed in the identity server and its required ability. This is, however, a good first step.
