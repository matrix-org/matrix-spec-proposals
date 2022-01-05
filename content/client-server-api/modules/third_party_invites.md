---
type: module
---

### Third party invites

This module adds in support for inviting new members to a room where
their Matrix user ID is not known, instead addressing them by a third
party identifier such as an email address. There are two flows here; one
if a Matrix user ID is known for the third party identifier, and one if
not. Either way, the client calls `/invite` with the details of the
third party identifier.

The homeserver asks the identity server whether a Matrix user ID is
known for that identifier:

-   If it is, an invite is simply issued for that user.
-   If it is not, the homeserver asks the identity server to record the
    details of the invitation, and to notify the invitee's homeserver of
    this pending invitation if it gets a binding for this identifier in
    the future. The identity server returns a token and public key to
    the inviting homeserver.

When the invitee's homeserver receives the notification of the binding,
it should insert an `m.room.member` event into the room's graph for that
user, with `content.membership` = `invite`, as well as a
`content.third_party_invite` property which contains proof that the
invitee does indeed own that third party identifier. See the
[m.room.member](#mroommember) schema for more information.

#### Events

{{% event event="m.room.third_party_invite" %}}

#### Client behaviour

A client asks a server to invite a user by their third party identifier.

{{% http-api spec="client-server" api="third_party_membership" %}}

#### Server behaviour

Upon receipt of an `/invite`, the server is expected to look up the
third party identifier with the provided identity server. If the lookup
yields a result for a Matrix User ID then the normal invite process can
be initiated. This process ends up looking like this:

```
    +---------+                         +-------------+                                    +-----------------+
    | Client  |                         | Homeserver  |                                    | IdentityServer  |
    +---------+                         +-------------+                                    +-----------------+
        |                                     |                                                    |
        | POST /invite                        |                                                    |
        |------------------------------------>|                                                    |
        |                                     |                                                    |
        |                                     | GET /lookup                                        |
        |                                     |--------------------------------------------------->|
        |                                     |                                                    |
        |                                     |                                     User ID result |
        |                                     |<---------------------------------------------------|
        |                                     |                                                    |
        |                                     | Invite process for the discovered User ID          |
        |                                     |------------------------------------------          |
        |                                     |                                         |          |
        |                                     |<-----------------------------------------          |
        |                                     |                                                    |
        |        Complete the /invite request |                                                    |
        |<------------------------------------|                                                    |
        |                                     |                                                    |
```

However, if the lookup does not yield a bound User ID, the homeserver
must store the invite on the identity server and emit a valid
`m.room.third_party_invite` event to the room. This process ends up
looking like this:

```
    +---------+                         +-------------+                                               +-----------------+
    | Client  |                         | Homeserver  |                                               | IdentityServer  |
    +---------+                         +-------------+                                               +-----------------+
        |                                     |                                                               |
        | POST /invite                        |                                                               |
        |------------------------------------>|                                                               |
        |                                     |                                                               |
        |                                     | GET /lookup                                                   |
        |                                     |-------------------------------------------------------------->|
        |                                     |                                                               |
        |                                     |                                             "no users" result |
        |                                     |<--------------------------------------------------------------|
        |                                     |                                                               |
        |                                     | POST /store-invite                                            |
        |                                     |-------------------------------------------------------------->|
        |                                     |                                                               |
        |                                     |          Information needed for the m.room.third_party_invite |
        |                                     |<--------------------------------------------------------------|
        |                                     |                                                               |
        |                                     | Emit m.room.third_party_invite to the room                    |
        |                                     |-------------------------------------------                    |
        |                                     |                                          |                    |
        |                                     |<------------------------------------------                    |
        |                                     |                                                               |
        |        Complete the /invite request |                                                               |
        |<------------------------------------|                                                               |
        |                                     |                                                               |
```

All homeservers MUST verify the signature in the event's
`content.third_party_invite.signed` object.

The third party user will then need to verify their identity, which
results in a call from the identity server to the homeserver that bound
the third party identifier to a user. The homeserver then exchanges the
`m.room.third_party_invite` event in the room for a complete
`m.room.member` event for `membership: invite` for the user that has
bound the third party identifier.

If a homeserver is joining a room for the first time because of an
`m.room.third_party_invite`, the server which is already participating
in the room (which is chosen as per the standard server-server
specification) MUST validate that the public key used for signing is
still valid, by checking `key_validity_url` in the above described way.

No other homeservers may reject the joining of the room on the basis of
`key_validity_url`, this is so that all homeservers have a consistent
view of the room. They may, however, indicate to their clients that a
member's membership is questionable.

For example, given H1, H2, and H3 as homeservers, UserA as a user of H1,
and an identity server IS, the full sequence for a third party invite
would look like the following. This diagram assumes H1 and H2 are
residents of the room while H3 is attempting to join.

```
    +-------+ +-----------------+         +-----+                                          +-----+           +-----+                      +-----+
    | UserA | | ThirdPartyUser  |         | H1  |                                          | H2  |           | H3  |                      | IS  |
    +-------+ +-----------------+         +-----+                                          +-----+           +-----+                      +-----+
        |              |                     |                                                |                 |                            |
        | POST /invite for ThirdPartyUser    |                                                |                 |                            |
        |----------------------------------->|                                                |                 |                            |
        |              |                     |                                                |                 |                            |
        |              |                     | GET /lookup                                    |                 |                            |
        |              |                     |---------------------------------------------------------------------------------------------->|
        |              |                     |                                                |                 |                            |
        |              |                     |                                                |                Lookup results (empty object) |
        |              |                     |<----------------------------------------------------------------------------------------------|
        |              |                     |                                                |                 |                            |
        |              |                     | POST /store-invite                             |                 |                            |
        |              |                     |---------------------------------------------------------------------------------------------->|
        |              |                     |                                                |                 |                            |
        |              |                     |                                                |      Token, keys, etc for third party invite |
        |              |                     |<----------------------------------------------------------------------------------------------|
        |              |                     |                                                |                 |                            |
        |              |                     | (Federation) Emit m.room.third_party_invite    |                 |                            |
        |              |                     |----------------------------------------------->|                 |                            |
        |              |                     |                                                |                 |                            |
        |           Complete /invite request |                                                |                 |                            |
        |<-----------------------------------|                                                |                 |                            |
        |              |                     |                                                |                 |                            |
        |              | Verify identity     |                                                |                 |                            |
        |              |-------------------------------------------------------------------------------------------------------------------->|
        |              |                     |                                                |                 |                            |
        |              |                     |                                                |                 |          POST /3pid/onbind |
        |              |                     |                                                |                 |<---------------------------|
        |              |                     |                                                |                 |                            |
        |              |                     |                         PUT /exchange_third_party_invite/:roomId |                            |
        |              |                     |<-----------------------------------------------------------------|                            |
        |              |                     |                                                |                 |                            |
        |              |                     | Verify the request                             |                 |                            |
        |              |                     |-------------------                             |                 |                            |
        |              |                     |                  |                             |                 |                            |
        |              |                     |<------------------                             |                 |                            |
        |              |                     |                                                |                 |                            |
        |              |                     | (Federation) Emit m.room.member for invite     |                 |                            |
        |              |                     |----------------------------------------------->|                 |                            |
        |              |                     |                                                |                 |                            |
        |              |                     |                                                |                 |                            |
        |              |                     | (Federation) Emit the m.room.member event sent to H2             |                            |
        |              |                     |----------------------------------------------------------------->|                            |
        |              |                     |                                                |                 |                            |
        |              |                     | Complete /exchange_third_party_invite/:roomId request            |                            |
        |              |                     |----------------------------------------------------------------->|                            |
        |              |                     |                                                |                 |                            |
        |              |                     |                                                |                 | Participate in the room    |
        |              |                     |                                                |                 |------------------------    |
        |              |                     |                                                |                 |                       |    |
        |              |                     |                                                |                 |<-----------------------    |
        |              |                     |                                                |                 |                            |
```

Note that when H1 sends the `m.room.member` event to H2 and H3 it does
not have to block on either server's receipt of the event. Likewise, H1
may complete the `/exchange_third_party_invite/:roomId` request at the
same time as sending the `m.room.member` event to H2 and H3.
Additionally, H3 may complete the `/3pid/onbind` request it got from IS
at any time - the completion is not shown in the diagram.

H1 MUST verify the request from H3 to ensure the `signed` property is
correct as well as the `key_validity_url` as still being valid. This is
done by making a request to the [identity server
/isvalid](/identity-service-api/#get_matrixidentityv2pubkeyisvalid)
endpoint, using the provided URL rather than constructing a new one. The
query string and response for the provided URL must match the Identity
Service Specification.

The reason that no other homeserver may reject the event based on
checking `key_validity_url` is that we must ensure event acceptance is
deterministic. If some other participating server doesn't have a network
path to the keyserver, or if the keyserver were to go offline, or revoke
its keys, that other server would reject the event and cause the
participating servers' graphs to diverge. This relies on participating
servers trusting each other, but that trust is already implied by the
server-server protocol. Also, the public key signature verification must
still be performed, so the attack surface here is minimized.

#### Security considerations

There are a number of privacy and trust implications to this module.

It is important for user privacy that leaking the mapping between a
matrix user ID and a third party identifier is hard. In particular,
being able to look up all third party identifiers from a matrix user ID
(and accordingly, being able to link each third party identifier) should
be avoided wherever possible. To this end, the third party identifier is
not put in any event, rather an opaque display name provided by the
identity server is put into the events. Clients should not remember or
display third party identifiers from invites, other than for the use of
the inviter themself.

Homeservers are not required to trust any particular identity server(s).
It is generally a client's responsibility to decide which identity
servers it trusts, not a homeserver's. Accordingly, this API takes
identity servers as input from end users, and doesn't have any specific
trusted set. It is possible some homeservers may want to supply
defaults, or reject some identity servers for *its* users, but no
homeserver is allowed to dictate which identity servers *other*
homeservers' users trust.

There is some risk of denial of service attacks by flooding homeservers
or identity servers with many requests, or much state to store.
Defending against these is left to the implementer's discretion.
