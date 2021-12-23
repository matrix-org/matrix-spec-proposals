# MSC2230: Store Identity Server in Account Data

The URL of the Identity Server to use is currently specified at registration and
login time and then used for the lifetime of a login session. If users wish to
specify a custom one, they must do so each time they log in on every client.
Once they have chosen an Identity Server to advertise their 3PIDs on, it would
be normal that they would wish to continue using this Identity Server for all
Identity requests in their account across all clients. This proposal aims to
make this easier.

## Proposal

The base URL of the Identity Server is to be stored in user account data. It
shall be stored in the same format as in a .well-known file under the event type
`m.identity_server` and shall comprise a single key, `base_url` which is the
base URL of the ID Server to use (that is, the part before `/_matrix`, including
`https://`).

Upon registration or login, a client SHOULD refrain from performing any requests
to the Identity Server until the account data has been fetched from the server.
Once it has the account data, it SHOULD check for the presence of the
`m.identity_server` key. If present, the `base_url` in this key SHOULD be used
as the Identity Server base URL for the duration of the login session. If this
key is not present, the client SHOULD use whatever value it would have used prior
to this MSC. It should not update the account data in this situation.

Client SHOULD listen for changes in the `m.identity_server` account data value
and update the URL that they use for ID Server requests accordingly.

Clients can offer a way for users to change the ID server being used. If they
do, the client MUST update the value of `m.identity_server` accordingly.

The `m.identity_server` may be present with a `base_url` of `null`. In this case,
clients MUST treat this as no ID Server URL being set and not perform ID
Server requests, disabling any functionality that requires such requests.

Conversely, if a user wishes to disable ID Server functionality, the client
shall action this by setting the `base_url` of the `m.identity_server`
account data entry to `null`.

### Transition Period

Clients will continue to use whatever IS URLs they currently use until the
user sets one explicitly, at which point it will be written to account data
and all clients will start using this value.

## Tradeoffs

There are a number of ways to transition to this new scheme. Clients could
populate the account data with their current ID Server URL as soon as
possible, and immediately use any new value seen on account data. This
would a much faster migration but any users with clients using different
ID Servers would suddenly find all their clients using the ID Server of
whichever client they updated first.

## Potential issues

Users will no longer be able to have different clients configured with
different ID Servers.

## Security considerations

An attacker would be able to force all a user clients to use a given ID Server
if they gained control of any of a user's logins.

## Conclusion

This makes the ID server an account setting which means it persists between
logins. The intention would be to phase out clients ever asking for an ID
Server URL at registration or login: this will be much easier for users to
understand whilst still retaining the flexibility for those who want it.
