---
title: "Application Service API"
weight: 30
type: docs
---

The Matrix client-server API and server-server APIs provide the means to
implement a consistent self-contained federated messaging fabric.
However, they provide limited means of implementing custom server-side
behaviour in Matrix (e.g. gateways, filters, extensible hooks etc). The
Application Service API (AS API) defines a standard API to allow such
extensible functionality to be implemented irrespective of the
underlying homeserver implementation.

## Application Services

Application services are passive and can only observe events from
homeserver. They can inject events into rooms they are participating in.
They cannot prevent events from being sent, nor can they modify the
content of the event being sent. In order to observe events from a
homeserver, the homeserver needs to be configured to pass certain types
of traffic to the application service. This is achieved by manually
configuring the homeserver with information about the application
service.

### Registration

{{% boxes/note %}}
Previously, application services could register with a homeserver via
HTTP APIs. This was removed as it was seen as a security risk. A
compromised application service could re-register for a global `*` regex
and sniff *all* traffic on the homeserver. To protect against this,
application services now have to register via configuration files which
are linked to the homeserver configuration file. The addition of
configuration files allows homeserver admins to sanity check the
registration for suspicious regex strings.
{{% /boxes/note %}}

Application services register "namespaces" of user IDs, room aliases and
room IDs. These namespaces are represented as regular expressions. An
application service is said to be "interested" in a given event if one
of the IDs in the event match the regular expression provided by the
application service, such as the room having an alias or ID in the
relevant namespaces. Similarly, the application service is said to be
interested in a given event if one of the application service's
namespaced users is the target of the event, or is a joined member of
the room where the event occurred.

An application service can also state whether they should be the only
ones who can manage a specified namespace. This is referred to as an
"exclusive" namespace. An exclusive namespace prevents humans and other
application services from creating/deleting entities in that namespace.
Typically, exclusive namespaces are used when the rooms represent real
rooms on another service (e.g. IRC). Non-exclusive namespaces are used
when the application service is merely augmenting the room itself (e.g.
providing logging or searching facilities). Namespaces are represented
by POSIX extended regular expressions and look like:

    users:
      - exclusive: true
        regex: "@_irc_bridge_.*"

Application services may define the following namespaces (with none
being explicitly required):

| Name     | Description                                                |
|----------|------------------------------------------------------------|
| users    | Events which are sent from certain users.                  |
| aliases  | Events which are sent in rooms with certain room aliases.  |
| rooms    | Events which are sent in rooms with certain room IDs.      |

Each individual namespace MUST declare the following fields:

| Name       | Description                                                                                                                        |
|------------|------------------------------------------------------------------------------------------------------------------------------------|
| exclusive  | **Required** A true or false value stating whether this application service has exclusive access to events within this namespace.  |
| regex      | **Required** A regular expression defining which values this namespace includes.                                                   |

Exclusive user and alias namespaces should begin with an underscore
after the sigil to avoid collisions with other users on the homeserver.
Application services should additionally attempt to identify the service
they represent in the reserved namespace. For example, `@_irc_.*` would
be a good namespace to register for an application service which deals
with IRC.

The registration is represented by a series of key-value pairs, which
this specification will present as YAML. See below for the possible
options along with their explanation:


| Name              | Description                                                                                                                                   |
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| id                | **Required** A unique, user-defined ID of the application service which will never change.                                                    |
| url               | **Required** The URL for the application service. May include a path after the domain name. Optionally set to null if no traffic is required. |
| as_token          | **Required** A unique token for application services to use to authenticate requests to Homeservers.                                          |
| hs_token          | **Required** A unique token for Homeservers to use to authenticate requests to application services.                                          |
| sender_localpart  | **Required** The localpart of the user associated with the application service.                                                               |
| namespaces        | **Required** A list of `users`, `aliases` and `rooms` namespaces that the application service controls.                                       |
| rate_limited      | Whether requests from masqueraded users are rate-limited. The sender is excluded.                                                             |
| protocols         | The external protocols which the application service provides (e.g. IRC).                                                                     |

An example registration file for an IRC-bridging application service is
below:

    id: "IRC Bridge"
    url: "http://127.0.0.1:1234"
    as_token: "30c05ae90a248a4188e620216fa72e349803310ec83e2a77b34fe90be6081f46"
    hs_token: "312df522183efd404ec1cd22d2ffa4bbc76a8c1ccf541dd692eef281356bb74e"
    sender_localpart: "_irc_bot" # Will result in @_irc_bot:example.org
    namespaces:
      users:
        - exclusive: true
          regex: "@_irc_bridge_.*"
      aliases:
        - exclusive: false
          regex: "#_irc_bridge_.*"
      rooms: []

{{% boxes/warning %}}
If the homeserver in question has multiple application services, each
`as_token` and `id` MUST be unique per application service as these are
used to identify the application service. The homeserver MUST enforce
this.
{{% /boxes/warning %}}

### Homeserver -&gt; Application Service API

#### Authorization

Homeservers MUST include a query parameter named `access_token`
containing the `hs_token` from the application service's registration
when making requests to the application service. Application services
MUST verify the provided `access_token` matches their known `hs_token`,
failing the request with an `M_FORBIDDEN` error if it does not match.

#### Legacy routes

Previous drafts of the application service specification had a mix of
endpoints that have been used in the wild for a significant amount of
time. The application service specification now defines a version on all
endpoints to be more compatible with the rest of the Matrix
specification and the future.

Homeservers should attempt to use the specified endpoints first when
communicating with application services. However, if the application
service receives an HTTP status code that does not indicate success
(i.e.: 404, 500, 501, etc) then the homeserver should fall back to the
older endpoints for the application service.

The older endpoints have the exact same request body and response
format, they just belong at a different path. The equivalent path for
each is as follows:

-   `/_matrix/app/v1/transactions/{txnId}` should fall back to
    `/transactions/{txnId}`
-   `/_matrix/app/v1/users/{userId}` should fall back to
    `/users/{userId}`
-   `/_matrix/app/v1/rooms/{roomAlias}` should fall back to
    `/rooms/{roomAlias}`
-   `/_matrix/app/v1/thirdparty/protocol/{protocol}` should fall back to
    `/_matrix/app/unstable/thirdparty/protocol/{protocol}`
-   `/_matrix/app/v1/thirdparty/user/{user}` should fall back to
    `/_matrix/app/unstable/thirdparty/user/{user}`
-   `/_matrix/app/v1/thirdparty/location/{location}` should fall back to
    `/_matrix/app/unstable/thirdparty/location/{location}`
-   `/_matrix/app/v1/thirdparty/user` should fall back to
    `/_matrix/app/unstable/thirdparty/user`
-   `/_matrix/app/v1/thirdparty/location` should fall back to
    `/_matrix/app/unstable/thirdparty/location`

Homeservers should periodically try again for the newer endpoints
because the application service may have been updated.

#### Pushing events

The application service API provides a transaction API for sending a
list of events. Each list of events includes a transaction ID, which
works as follows:

```
    Typical
    HS ---> AS : Homeserver sends events with transaction ID T.
       <---    : Application Service sends back 200 OK.
```

```
    AS ACK Lost
    HS ---> AS : Homeserver sends events with transaction ID T.
       <-/-    : AS 200 OK is lost.
    HS ---> AS : Homeserver retries with the same transaction ID of T.
       <---    : Application Service sends back 200 OK. If the AS had processed these
                 events already, it can NO-OP this request (and it knows if it is the
                 same events based on the transaction ID).
```

The events sent to the application service should be linearised, as if
they were from the event stream. The homeserver MUST maintain a queue of
transactions to send to the application service. If the application
service cannot be reached, the homeserver SHOULD backoff exponentially
until the application service is reachable again. As application
services cannot *modify* the events in any way, these requests can be
made without blocking other aspects of the homeserver. Homeservers MUST
NOT alter (e.g. add more) events they were going to send within that
transaction ID on retries, as the application service may have already
processed the events.

{{% http-api spec="application-service" api="transactions" %}}

#### Querying

The application service API includes two querying APIs: for room aliases
and for user IDs. The application service SHOULD create the queried
entity if it desires. During this process, the application service is
blocking the homeserver until the entity is created and configured. If
the homeserver does not receive a response to this request, the
homeserver should retry several times before timing out. This should
result in an HTTP status 408 "Request Timeout" on the client which
initiated this request (e.g. to join a room alias).

{{% boxes/rationale %}}
Blocking the homeserver and expecting the application service to create
the entity using the client-server API is simpler and more flexible than
alternative methods such as returning an initial sync style JSON blob
and get the HS to provision the room/user. This also meant that there
didn't need to be a "backchannel" to inform the application service
about information about the entity such as room ID to room alias
mappings.
{{% /boxes/rationale %}}

{{% http-api spec="application-service" api="query_user" %}}

{{% http-api spec="application-service" api="query_room" %}}

#### Third party networks

Application services may declare which protocols they support via their
registration configuration for the homeserver. These networks are
generally for third party services such as IRC that the application
service is managing. Application services may populate a Matrix room
directory for their registered protocols, as defined in the
Client-Server API Extensions.

Each protocol may have several "locations" (also known as "third party
locations" or "3PLs"). A location within a protocol is a place in the
third party network, such as an IRC channel. Users of the third party
network may also be represented by the application service.

Locations and users can be searched by fields defined by the application
service, such as by display name or other attribute. When clients
request the homeserver to search in a particular "network" (protocol),
the search fields will be passed along to the application service for
filtering.

{{% http-api spec="application-service" api="protocols" %}}

### Client-Server API Extensions

Application services can use a more powerful version of the
client-server API by identifying itself as an application service to the
homeserver.

Endpoints defined in this section MUST be supported by homeservers in
the client-server API as accessible only by application services.

#### Identity assertion

The client-server API infers the user ID from the `access_token`
provided in every request. To avoid the application service from having
to keep track of each user's access token, the application service
should identify itself to the Client-Server API by providing its
`as_token` for the `access_token` alongside the user the application
service would like to masquerade as.

Inputs:
-   Application service token (`as_token`)
-   User ID in the AS namespace to act as.

Notes:
-   This applies to all aspects of the Client-Server API, except for
    Account Management.
-   The `as_token` is inserted into `access_token` which is usually
    where the client token is, such as via the query string or
    `Authorization` header. This is done on purpose to allow application
    services to reuse client SDKs.
-   The `access_token` should be supplied through the `Authorization`
    header where possible to prevent the token appearing in HTTP request
    logs by accident.

The application service may specify the virtual user to act as through
use of a `user_id` query string parameter on the request. The user
specified in the query string must be covered by one of the application
service's `user` namespaces. If the parameter is missing, the homeserver
is to assume the application service intends to act as the user implied
by the `sender_localpart` property of the registration.

An example request would be:

    GET /_matrix/client/v3/account/whoami?user_id=@_irc_user:example.org
    Authorization: Bearer YourApplicationServiceTokenHere

#### Timestamp massaging

Previous drafts of the Application Service API permitted application
services to alter the timestamp of their sent events by providing a `ts`
query parameter when sending an event. This API has been excluded from
the first release due to design concerns, however some servers may still
support the feature. Please visit [issue
\#1585](https://github.com/matrix-org/matrix-doc/issues/1585) for more
information.

#### Server admin style permissions

The homeserver needs to give the application service *full control* over
its namespace, both for users and for room aliases. This means that the
AS should be able to manage any users and room alias in its namespace. No additional API
changes need to be made in order for control of room aliases to be
granted to the AS.

Creation of users needs API changes in order to:

-   Work around captchas.
-   Have a 'passwordless' user.

This involves bypassing the registration flows entirely. This is
achieved by including the `as_token` on a `/register` request, along
with a login type of `m.login.application_service` to set the desired
user ID without a password.

    POST /_matrix/client/v3/register
    Authorization: Bearer YourApplicationServiceTokenHere

    Content:
    {
      type: "m.login.application_service",
      username: "_irc_example"
    }

Similarly, logging in as users needs API changes in order to allow the AS to
log in without needing the user's password. This is achieved by including the
`as_token` on a `/login` request, along with a login type of
`m.login.application_service`:

{{% added-in v="1.2" %}}

    POST /_matrix/client/%CLIENT_MAJOR_VERSION%/login
    Authorization: Bearer YourApplicationServiceTokenHere

    Content:
    {
      type: "m.login.application_service",
      "identifier": {
        "type": "m.id.user",
        "user": "_irc_example"
      }
    }

Application services which attempt to create users or aliases *outside*
of their defined namespaces, or log in as users outside of their defined
namespaces will receive an error code `M_EXCLUSIVE`.
Similarly, normal users who attempt to create users or aliases *inside*
an application service-defined namespace will receive the same
`M_EXCLUSIVE` error code, but only if the application service has
defined the namespace as `exclusive`.

#### Using `/sync` and `/events`

Application services wishing to use `/sync` or `/events` from the
Client-Server API MUST do so with a virtual user (provide a `user_id`
via the query string). It is expected that the application service use
the transactions pushed to it to handle events rather than syncing with
the user implied by `sender_localpart`.

#### Application service room directories

Application services can maintain their own room directories for their
defined third party protocols. These room directories may be accessed by
clients through additional parameters on the `/publicRooms`
client-server endpoint.

{{% http-api spec="client-server" api="appservice_room_directory" %}}

### Referencing messages from a third party network

Application services should include an `external_url` in the `content`
of events it emits to indicate where the message came from. This
typically applies to application services that bridge other networks
into Matrix, such as IRC, where an HTTP URL may be available to
reference.

Clients should provide users with a way to access the `external_url` if
it is present. Clients should additionally ensure the URL has a scheme
of `https` or `http` before making use of it.

The presence of an `external_url` on an event does not necessarily mean
the event was sent from an application service. Clients should be wary
of the URL contained within, as it may not be a legitimate reference to
the event's source.
