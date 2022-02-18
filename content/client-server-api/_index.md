---
title: "Client-Server API"
weight: 10
type: docs
---

The client-server API allows clients to
send messages, control rooms and synchronise conversation history. It is
designed to support both lightweight clients which store no state and
lazy-load data from the server as required - as well as heavyweight
clients which maintain a full local persistent copy of server state.

## API Standards

The mandatory baseline for client-server communication in Matrix is
exchanging JSON objects over HTTP APIs. HTTPS is recommended for
communication, although HTTP may be supported as a fallback to support
basic HTTP clients. More efficient optional transports will in future be
supported as optional extensions - e.g. a packed binary encoding over
stream-cipher encrypted TCP socket for low-bandwidth/low-roundtrip
mobile usage. For the default HTTP transport, all API calls use a
Content-Type of `application/json`. In addition, all strings MUST be
encoded as UTF-8.

Clients are authenticated using opaque `access_token` strings (see [Client
Authentication](#client-authentication) for details).

See also [Conventions for Matrix APIs](/appendices#conventions-for-matrix-apis)
in the Appendices for conventions which all Matrix APIs are expected to follow.

### Standard error response

Any errors which occur at the Matrix API level MUST return a "standard
error response". This is a JSON object which looks like:

```json
{
  "errcode": "<error code>",
  "error": "<error message>"
}
```

The `error` string will be a human-readable error message, usually a
sentence explaining what went wrong.

The `errcode` string will be a unique string which can be used to handle an
error message e.g.  `M_FORBIDDEN`. Error codes should have their namespace
first in ALL CAPS, followed by a single `_`. For example, if there was a custom
namespace `com.mydomain.here`, and a `FORBIDDEN` code, the error code should
look like `COM.MYDOMAIN.HERE_FORBIDDEN`. Error codes defined by this
specification should start `M_`.

Some `errcode`s define additional keys which should be present in the error
response object, but the keys `error` and `errcode` MUST always be present.

Errors are generally best expressed by their error code rather than the
HTTP status code returned. When encountering the error code `M_UNKNOWN`,
clients should prefer the HTTP status code as a more reliable reference
for what the issue was. For example, if the client receives an error
code of `M_NOT_FOUND` but the request gave a 400 Bad Request status
code, the client should treat the error as if the resource was not
found. However, if the client were to receive an error code of
`M_UNKNOWN` with a 400 Bad Request, the client should assume that the
request being made was invalid.

#### Common error codes

These error codes can be returned by any API endpoint:

`M_FORBIDDEN`
Forbidden access, e.g. joining a room without permission, failed login.

`M_UNKNOWN_TOKEN`
The access token specified was not recognised.

An additional response parameter, `soft_logout`, might be present on the
response for 401 HTTP status codes. See [the soft logout
section](#soft-logout) for more information.

`M_MISSING_TOKEN`
No access token was specified for the request.

`M_BAD_JSON`
Request contained valid JSON, but it was malformed in some way, e.g.
missing required keys, invalid values for keys.

`M_NOT_JSON`
Request did not contain valid JSON.

`M_NOT_FOUND`
No resource was found for this request.

`M_LIMIT_EXCEEDED`
Too many requests have been sent in a short period of time. Wait a while
then try again.

`M_UNKNOWN`
An unknown error has occurred.

#### Other error codes

The following error codes are specific to certain endpoints.

<!-- TODO: move them to the endpoints that return them -->.

`M_UNRECOGNIZED`
The server did not understand the request.

`M_UNAUTHORIZED`
The request was not correctly authorized. Usually due to login failures.

`M_USER_DEACTIVATED`
The user ID associated with the request has been deactivated. Typically
for endpoints that prove authentication, such as `/login`.

`M_USER_IN_USE`
Encountered when trying to register a user ID which has been taken.

`M_INVALID_USERNAME`
Encountered when trying to register a user ID which is not valid.

`M_ROOM_IN_USE`
Sent when the room alias given to the `createRoom` API is already in
use.

`M_INVALID_ROOM_STATE`
Sent when the initial state given to the `createRoom` API is invalid.

`M_THREEPID_IN_USE`
Sent when a threepid given to an API cannot be used because the same
threepid is already in use.

`M_THREEPID_NOT_FOUND`
Sent when a threepid given to an API cannot be used because no record
matching the threepid was found.

`M_THREEPID_AUTH_FAILED`
Authentication could not be performed on the third party identifier.

`M_THREEPID_DENIED`
The server does not permit this third party identifier. This may happen
if the server only permits, for example, email addresses from a
particular domain.

`M_SERVER_NOT_TRUSTED`
The client's request used a third party server, e.g. identity server,
that this server does not trust.

`M_UNSUPPORTED_ROOM_VERSION`
The client's request to create a room used a room version that the
server does not support.

`M_INCOMPATIBLE_ROOM_VERSION`
The client attempted to join a room that has a version the server does
not support. Inspect the `room_version` property of the error response
for the room's version.

`M_BAD_STATE`
The state change requested cannot be performed, such as attempting to
unban a user who is not banned.

`M_GUEST_ACCESS_FORBIDDEN`
The room or resource does not permit guests to access it.

`M_CAPTCHA_NEEDED`
A Captcha is required to complete the request.

`M_CAPTCHA_INVALID`
The Captcha provided did not match what was expected.

`M_MISSING_PARAM`
A required parameter was missing from the request.

`M_INVALID_PARAM`
A parameter that was specified has the wrong value. For example, the
server expected an integer and instead received a string.

`M_TOO_LARGE`
The request or entity was too large.

`M_EXCLUSIVE`
The resource being requested is reserved by an application service, or
the application service making the request has not created the resource.

`M_RESOURCE_LIMIT_EXCEEDED`
The request cannot be completed because the homeserver has reached a
resource limit imposed on it. For example, a homeserver held in a shared
hosting environment may reach a resource limit if it starts using too
much memory or disk space. The error MUST have an `admin_contact` field
to provide the user receiving the error a place to reach out to.
Typically, this error will appear on routes which attempt to modify
state (e.g.: sending messages, account data, etc) and not routes which
only read state (e.g.: `/sync`, get account data, etc).

`M_CANNOT_LEAVE_SERVER_NOTICE_ROOM`
The user is unable to reject an invite to join the server notices room.
See the [Server Notices](#server-notices) module for more information.

The client-server API typically uses `HTTP PUT` to submit requests with
a client-generated transaction identifier. This means that these
requests are idempotent. The scope of a transaction identifier is a
particular access token. It **only** serves to identify new requests
from retransmits. After the request has finished, the `{txnId}` value
should be changed (how is not specified; a monotonically increasing
integer is recommended).

Some API endpoints may allow or require the use of `POST` requests
without a transaction ID. Where this is optional, the use of a `PUT`
request is strongly recommended.

{{% http-api spec="client-server" api="versions" %}}

## Web Browser Clients

It is realistic to expect that some clients will be written to be run
within a web browser or similar environment. In these cases, the
homeserver should respond to pre-flight requests and supply Cross-Origin
Resource Sharing (CORS) headers on all requests.

Servers MUST expect that clients will approach them with `OPTIONS`
requests, allowing clients to discover the CORS headers. All endpoints
in this specification support the `OPTIONS` method, however the server
MUST NOT perform any logic defined for the endpoints when approached
with an `OPTIONS` request.

When a client approaches the server with a request, the server should
respond with the CORS headers for that route. The recommended CORS
headers to be returned by servers on all requests are:

    Access-Control-Allow-Origin: *
    Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
    Access-Control-Allow-Headers: X-Requested-With, Content-Type, Authorization

## Server Discovery

In order to allow users to connect to a Matrix server without needing to
explicitly specify the homeserver's URL or other parameters, clients
SHOULD use an auto-discovery mechanism to determine the server's URL
based on a user's Matrix ID. Auto-discovery should only be done at login
time.

In this section, the following terms are used with specific meanings:

`PROMPT`
Retrieve the specific piece of information from the user in a way which
fits within the existing client user experience, if the client is
inclined to do so. Failure can take place instead if no good user
experience for this is possible at this point.

`IGNORE`
Stop the current auto-discovery mechanism. If no more auto-discovery
mechanisms are available, then the client may use other methods of
determining the required parameters, such as prompting the user, or
using default values.

`FAIL_PROMPT`
Inform the user that auto-discovery failed due to invalid/empty data and
`PROMPT` for the parameter.

`FAIL_ERROR`
Inform the user that auto-discovery did not return any usable URLs. Do
not continue further with the current login process. At this point,
valid data was obtained, but no server is available to serve the client.
No further guess should be attempted and the user should make a
conscientious decision what to do next.

### Well-known URI

{{% boxes/note %}}
Servers hosting the `.well-known` JSON file SHOULD offer CORS headers,
as per the [CORS](#web-browser-clients) section in this specification.
{{% /boxes/note %}}

The `.well-known` method uses a JSON file at a predetermined location to
specify parameter values. The flow for this method is as follows:

1.  Extract the server name from the user's Matrix ID by splitting the
    Matrix ID at the first colon.
2.  Extract the hostname from the server name.
3.  Make a GET request to `https://hostname/.well-known/matrix/client`.
    1.  If the returned status code is 404, then `IGNORE`.
    2.  If the returned status code is not 200, or the response body is
        empty, then `FAIL_PROMPT`.
    3.  Parse the response body as a JSON object
        1.  If the content cannot be parsed, then `FAIL_PROMPT`.
    4.  Extract the `base_url` value from the `m.homeserver` property.
        This value is to be used as the base URL of the homeserver.
        1. If this value is not provided, then `FAIL_PROMPT`.
    5.  Validate the homeserver base URL:
        1. Parse it as a URL. If it is not a URL, then `FAIL_ERROR`.
        2. Clients SHOULD validate that the URL points to a valid
            homeserver before accepting it by connecting to the
            [`/_matrix/client/versions`](/client-server-api/#get_matrixclientversions) endpoint, ensuring that it does
            not return an error, and parsing and validating that the
            data conforms with the expected response format. If any step
            in the validation fails, then `FAIL_ERROR`. Validation is
            done as a simple check against configuration errors, in
            order to ensure that the discovered address points to a
            valid homeserver.
        3. It is important to note that the `base_url` value might include
           a trailing `/`. Consumers should be prepared to handle both cases.
    6.  If the `m.identity_server` property is present, extract the
        `base_url` value for use as the base URL of the identity server.
        Validation for this URL is done as in the step above, but using
        `/_matrix/identity/v2` as the endpoint to connect to. If the
        `m.identity_server` property is present, but does not have a
        `base_url` value, then `FAIL_PROMPT`.

{{% http-api spec="client-server" api="wellknown" %}}

## Client Authentication

Most API endpoints require the user to identify themselves by presenting
previously obtained credentials in the form of an `access_token` query
parameter or through an Authorization Header of `Bearer $access_token`.
An access token is typically obtained via the [Login](#login) or
[Registration](#account-registration-and-management) processes.

{{% boxes/note %}}
This specification does not mandate a particular format for the access
token. Clients should treat it as an opaque byte sequence. Servers are
free to choose an appropriate format. Server implementors may like to
investigate [macaroons](http://research.google.com/pubs/pub41892.html).
{{% /boxes/note %}}

### Using access tokens

Access tokens may be provided in two ways, both of which the homeserver
MUST support:

1.  Via a query string parameter, `access_token=TheTokenHere`.
2.  Via a request header, `Authorization: Bearer TheTokenHere`.

Clients are encouraged to use the `Authorization` header where possible
to prevent the access token being leaked in access/HTTP logs. The query
string should only be used in cases where the `Authorization` header is
inaccessible for the client.

When credentials are required but missing or invalid, the HTTP call will
return with a status of 401 and the error code, `M_MISSING_TOKEN` or
`M_UNKNOWN_TOKEN` respectively.

### Relationship between access tokens and devices

Client [devices](../index.html#devices) are closely related to access
tokens. Matrix servers should record which device each access token is
assigned to, so that subsequent requests can be handled correctly.

By default, the [Login](#login) and [Registration](#account-registration-and-management)
processes auto-generate a new `device_id`. A client is also free to
generate its own `device_id` or, provided the user remains the same,
reuse a device: in either case the client should pass the `device_id` in
the request body. If the client sets the `device_id`, the server will
invalidate any access token previously assigned to that device. There is
therefore at most one active access token assigned to each device at any
one time.

### Soft logout

When a request fails due to a 401 status code per above, the server can
include an extra response parameter, `soft_logout`, to indicate if the
client's persisted information can be retained. This defaults to
`false`, indicating that the server has destroyed the session. Any
persisted state held by the client, such as encryption keys and device
information, must not be reused and must be discarded.

When `soft_logout` is true, the client can acquire a new access token by
specifying the device ID it is already using to the login API. In most
cases a `soft_logout: true` response indicates that the user's session
has expired on the server-side and the user simply needs to provide
their credentials again.

In either case, the client's previously known access token will no
longer function.

### User-Interactive Authentication API

#### Overview

Some API endpoints require authentication that interacts with the user.
The homeserver may provide many different ways of authenticating, such
as user/password auth, login via a single-sign-on server (SSO), etc.
This specification does not define how homeservers should authorise
their users but instead defines the standard interface which
implementations should follow so that ANY client can log in to ANY
homeserver.

The process takes the form of one or more 'stages'. At each stage the
client submits a set of data for a given authentication type and awaits
a response from the server, which will either be a final success or a
request to perform an additional stage. This exchange continues until
the final success.

For each endpoint, a server offers one or more 'flows' that the client
can use to authenticate itself. Each flow comprises a series of stages,
as described above. The client is free to choose which flow it follows,
however the flow's stages must be completed in order. Failing to follow
the flows in order must result in an HTTP 401 response, as defined
below. When all stages in a flow are complete, authentication is
complete and the API call succeeds.

#### User-interactive API in the REST API

In the REST API described in this specification, authentication works by
the client and server exchanging JSON dictionaries. The server indicates
what authentication data it requires via the body of an HTTP 401
response, and the client submits that authentication data via the `auth`
request parameter.

A client should first make a request with no `auth` parameter.
The homeserver returns an HTTP 401 response, with a JSON body, as follows:

    HTTP/1.1 401 Unauthorized
    Content-Type: application/json

```json
{
  "flows": [
    {
      "stages": [ "example.type.foo", "example.type.bar" ]
    },
    {
      "stages": [ "example.type.foo", "example.type.baz" ]
    }
  ],
  "params": {
      "example.type.baz": {
          "example_key": "foobar"
      }
  },
  "session": "xxxxxx"
}
```

In addition to the `flows`, this object contains some extra information:

* `params`: This section contains any information that the client will
need to know in order to use a given type of authentication. For each
authentication type presented, that type may be present as a key in this
dictionary. For example, the public part of an OAuth client ID could be
given here.

* `session`: This is a session identifier that the client must pass back
to the homeserver, if one is provided, in subsequent attempts to authenticate
in the same API call.

The client then chooses a flow and attempts to complete the first stage.
It does this by resubmitting the same request with the addition of an
`auth` key in the object that it submits. This dictionary contains a
`type` key whose value is the name of the authentication type that the
client is attempting to complete. It must also contain a `session` key
with the value of the session key given by the homeserver, if one was
given. It also contains other keys dependent on the auth type being
attempted. For example, if the client is attempting to complete auth
type `example.type.foo`, it might submit something like this:

    POST /_matrix/client/v3/endpoint HTTP/1.1
    Content-Type: application/json

```json
{
  "a_request_parameter": "something",
  "another_request_parameter": "something else",
  "auth": {
      "type": "example.type.foo",
      "session": "xxxxxx",
      "example_credential": "verypoorsharedsecret"
  }
}
```

If the homeserver deems the authentication attempt to be successful but
still requires more stages to be completed, it returns HTTP status 401
along with the same object as when no authentication was attempted, with
the addition of the `completed` key which is an array of auth types the
client has completed successfully:

    HTTP/1.1 401 Unauthorized
    Content-Type: application/json

```json
{
  "completed": [ "example.type.foo" ],
  "flows": [
    {
      "stages": [ "example.type.foo", "example.type.bar" ]
    },
    {
      "stages": [ "example.type.foo", "example.type.baz" ]
    }
  ],
  "params": {
      "example.type.baz": {
          "example_key": "foobar"
      }
  },
  "session": "xxxxxx"
}
```

Individual stages may require more than one request to complete, in
which case the response will be as if the request was unauthenticated
with the addition of any other keys as defined by the auth type.

If the homeserver decides that an attempt on a stage was unsuccessful,
but the client may make a second attempt, it returns the same HTTP
status 401 response as above, with the addition of the standard
`errcode` and `error` fields describing the error. For example:

    HTTP/1.1 401 Unauthorized
    Content-Type: application/json

```json
{
  "errcode": "M_FORBIDDEN",
  "error": "Invalid password",
  "completed": [ "example.type.foo" ],
  "flows": [
    {
      "stages": [ "example.type.foo", "example.type.bar" ]
    },
    {
      "stages": [ "example.type.foo", "example.type.baz" ]
    }
  ],
  "params": {
      "example.type.baz": {
          "example_key": "foobar"
      }
  },
  "session": "xxxxxx"
}
```

If the request fails for a reason other than authentication, the server
returns an error message in the standard format. For example:

    HTTP/1.1 400 Bad request
    Content-Type: application/json

```json
{
  "errcode": "M_EXAMPLE_ERROR",
  "error": "Something was wrong"
}
```

If the client has completed all stages of a flow, the homeserver
performs the API call and returns the result as normal. Completed stages
cannot be retried by clients, therefore servers must return either a 401
response with the completed stages, or the result of the API call if all
stages were completed when a client retries a stage.

Some authentication types may be completed by means other than through
the Matrix client, for example, an email confirmation may be completed
when the user clicks on the link in the email. In this case, the client
retries the request with an auth dict containing only the session key.
The response to this will be the same as if the client were attempting
to complete an auth state normally, i.e. the request will either
complete or request auth, with the presence or absence of that auth type
in the 'completed' array indicating whether that stage is complete.

{{% boxes/note %}}
A request to an endpoint that uses User-Interactive Authentication never
succeeds without auth. Homeservers may allow requests that don't require
auth by offering a stage with only the `m.login.dummy` auth type, but they
must still give a 401 response to requests with no auth data.
{{% /boxes/note %}}

#### Example

At a high level, the requests made for an API call completing an auth
flow with three stages will resemble the following diagram:

```
    _______________________
    |       Stage 0         |
    | No auth               |
    |  ___________________  |
    | |_Request_1_________| | <-- Returns "session" key which is used throughout.
    |_______________________|
             |
             |
    _________V_____________
    |       Stage 1         |
    | type: "<auth type1>"  |
    |  ___________________  |
    | |_Request_1_________| |
    |_______________________|
             |
             |
    _________V_____________
    |       Stage 2         |
    | type: "<auth type2>"  |
    |  ___________________  |
    | |_Request_1_________| |
    |  ___________________  |
    | |_Request_2_________| |
    |  ___________________  |
    | |_Request_3_________| |
    |_______________________|
             |
             |
    _________V_____________
    |       Stage 3         |
    | type: "<auth type3>"  |
    |  ___________________  |
    | |_Request_1_________| | <-- Returns API response
    |_______________________|
```

#### Authentication types

This specification defines the following auth types:
-   `m.login.password`
-   `m.login.recaptcha`
-   `m.login.sso`
-   `m.login.email.identity`
-   `m.login.msisdn`
-   `m.login.dummy`
-   `m.login.registration_token`

##### Password-based


| Type               | Description                                                                    |
|--------------------|--------------------------------------------------------------------------------|
| `m.login.password` | The client submits an identifier and secret password, both sent in plain-text. |

To use this authentication type, clients should submit an auth dict as
follows:

```
{
  "type": "m.login.password",
  "identifier": {
    ...
  },
  "password": "<password>",
  "session": "<session ID>"
}
```

where the `identifier` property is a user identifier object, as
described in [Identifier types](#identifier-types).

For example, to authenticate using the user's Matrix ID, clients would
submit:

```json
{
  "type": "m.login.password",
  "identifier": {
    "type": "m.id.user",
    "user": "<user_id or user localpart>"
  },
  "password": "<password>",
  "session": "<session ID>"
}
```

Alternatively reply using a 3PID bound to the user's account on the
homeserver using the `/account/3pid`\_ API rather than giving the `user`
explicitly as follows:

```json
{
  "type": "m.login.password",
  "identifier": {
    "type": "m.id.thirdparty",
    "medium": "<The medium of the third party identifier.>",
    "address": "<The third party address of the user>"
  },
  "password": "<password>",
  "session": "<session ID>"
}
```

In the case that the homeserver does not know about the supplied 3PID,
the homeserver must respond with 403 Forbidden.

##### Google ReCaptcha

| Type                | Description                                          |
|---------------------|------------------------------------------------------|
| `m.login.recaptcha` | The user completes a Google ReCaptcha 2.0 challenge. |

To use this authentication type, clients should submit an auth dict as
follows:

```json
{
  "type": "m.login.recaptcha",
  "response": "<captcha response>",
  "session": "<session ID>"
}
```

##### Single Sign-On

| Type          | Description                                                                          |
|---------------|--------------------------------------------------------------------------------------|
| `m.login.sso` | Authentication is supported by authorising with an external single sign-on provider. |

A client wanting to complete authentication using SSO should use the
[Fallback](#fallback) mechanism. See [SSO during User-Interactive
Authentication](#sso-during-user-interactive-authentication) for more information.

##### Email-based (identity / homeserver)

| Type                     | Description                                                                                                      |
|--------------------------|------------------------------------------------------------------------------------------------------------------|
| `m.login.email.identity` | Authentication is supported by authorising an email address with an identity server, or homeserver if supported. |

Prior to submitting this, the client should authenticate with an
identity server (or homeserver). After authenticating, the session
information should be submitted to the homeserver.

To use this authentication type, clients should submit an auth dict as
follows:

```json
{
  "type": "m.login.email.identity",
  "threepid_creds": {
    "sid": "<identity server session id>",
    "client_secret": "<identity server client secret>",
    "id_server": "<url of identity server authed with, e.g. 'matrix.org:8090'>",
    "id_access_token": "<access token previously registered with the identity server>"
  },
  "session": "<session ID>"
}
```

Note that `id_server` (and therefore `id_access_token`) is optional if
the `/requestToken` request did not include them.

##### Phone number/MSISDN-based (identity / homeserver)

| Type             | Description                                                                                                    |
|------------------|----------------------------------------------------------------------------------------------------------------|
| `m.login.msisdn` | Authentication is supported by authorising a phone number with an identity server, or homeserver if supported. |

Prior to submitting this, the client should authenticate with an
identity server (or homeserver). After authenticating, the session
information should be submitted to the homeserver.

To use this authentication type, clients should submit an auth dict as
follows:

```json
{
  "type": "m.login.msisdn",
  "threepid_creds": {
    "sid": "<identity server session id>",
    "client_secret": "<identity server client secret>",
    "id_server": "<url of identity server authed with, e.g. 'matrix.org:8090'>",
    "id_access_token": "<access token previously registered with the identity server>"
  },
  "session": "<session ID>"
}
```

Note that `id_server` (and therefore `id_access_token`) is optional if
the `/requestToken` request did not include them.

##### Dummy Auth

| Type             | Description                                                            |
|------------------|------------------------------------------------------------------------|
| `m.login.dummy`  | Dummy authentication always succeeds and requires no extra parameters. |

The purpose of dummy authentication is to allow servers to not require any form of
User-Interactive Authentication to perform a request. It can also be
used to differentiate flows where otherwise one flow would be a subset
of another flow. e.g. if a server offers flows `m.login.recaptcha` and
`m.login.recaptcha, m.login.email.identity` and the client completes the
recaptcha stage first, the auth would succeed with the former flow, even
if the client was intending to then complete the email auth stage. A
server can instead send flows `m.login.recaptcha, m.login.dummy` and
`m.login.recaptcha, m.login.email.identity` to fix the ambiguity.

To use this authentication type, clients should submit an auth dict with
just the type and session, if provided:

```json
{
  "type": "m.login.dummy",
  "session": "<session ID>"
}
```

##### Token-authenticated registration

{{% added-in v="1.2" %}}

| Type                          | Description                                                       |
|-------------------------------|-------------------------------------------------------------------|
| `m.login.registration_token`  | Registers an account with a pre-shared token for authentication   |

{{% boxes/note %}}
The `m.login.registration_token` authentication type is only valid on the
[`/register`](#post_matrixclientv3register) endpoint.
{{% /boxes/note %}}

This authentication type provides homeservers the ability to allow registrations
to a limited set of people instead of either offering completely open registrations
or completely closed registration (where the homeserver administrators create
and distribute accounts).

The token required for this authentication type is shared out of band from
Matrix and is an opaque string with maximum length of 64 characters in the
range `[A-Za-z0-9._~-]`. The server can keep any number of tokens for any
length of time/validity. Such cases might be a token limited to 100 uses or
for the next 2 hours - after the tokens expire, they can no longer be used
to create accounts.

To use this authentication type, clients should submit an auth dict with just
the type, token, and session:

```json
{
  "type": "m.login.registration_token",
  "token": "fBVFdqVE",
  "session": "<session ID>"
}
```

To determine if a token is valid before attempting to use it, the client can
use the `/validity` API defined below. The API doesn't guarantee that a token
will be valid when used, but does avoid cases where the user finds out late
in the registration process that their token has expired.

{{% http-api spec="client-server" api="registration_tokens" %}}

#### Fallback

Clients cannot be expected to be able to know how to process every
single login type. If a client does not know how to handle a given login
type, it can direct the user to a web browser with the URL of a fallback
page which will allow the user to complete that login step out-of-band
in their web browser. The URL it should open is:

    /_matrix/client/v3/auth/<auth type>/fallback/web?session=<session ID>

Where `auth type` is the type name of the stage it is attempting and
`session ID` is the ID of the session given by the homeserver.

This MUST return an HTML page which can perform this authentication
stage. This page must use the following JavaScript when the
authentication has been completed:

```js
if (window.onAuthDone) {
    window.onAuthDone();
} else if (window.opener && window.opener.postMessage) {
    window.opener.postMessage("authDone", "*");
}
```

This allows the client to either arrange for the global function
`onAuthDone` to be defined in an embedded browser, or to use the HTML5
[cross-document
messaging](https://www.w3.org/TR/webmessaging/#web-messaging) API, to
receive a notification that the authentication stage has been completed.

Once a client receives the notification that the authentication stage
has been completed, it should resubmit the request with an auth dict
with just the session ID:

```json
{
  "session": "<session ID>"
}
```

##### Example

A client webapp might use the following JavaScript to open a popup
window which will handle unknown login types:

```js
/**
 * Arguments:
 *     homeserverUrl: the base url of the homeserver (e.g. "https://matrix.org")
 *
 *     apiEndpoint: the API endpoint being used (e.g.
 *        "/_matrix/client/v3/account/password")
 *
 *     loginType: the loginType being attempted (e.g. "m.login.recaptcha")
 *
 *     sessionID: the session ID given by the homeserver in earlier requests
 *
 *     onComplete: a callback which will be called with the results of the request
 */
function unknownLoginType(homeserverUrl, apiEndpoint, loginType, sessionID, onComplete) {
    var popupWindow;

    var eventListener = function(ev) {
        // check it's the right message from the right place.
        if (ev.data !== "authDone" || ev.origin !== homeserverUrl) {
            return;
        }

        // close the popup
        popupWindow.close();
        window.removeEventListener("message", eventListener);

        // repeat the request
        var requestBody = {
            auth: {
                session: sessionID,
            },
        };

        request({
            method:'POST', url:apiEndpoint, json:requestBody,
        }, onComplete);
    };

    window.addEventListener("message", eventListener);

    var url = homeserverUrl +
        "/_matrix/client/v3/auth/" +
        encodeURIComponent(loginType) +
        "/fallback/web?session=" +
        encodeURIComponent(sessionID);

   popupWindow = window.open(url);
}
```

#### Identifier types

Some authentication mechanisms use a user identifier object to identify
a user. The user identifier object has a `type` field to indicate the
type of identifier being used, and depending on the type, has other
fields giving the information required to identify the user as described
below.

This specification defines the following identifier types:
-   `m.id.user`
-   `m.id.thirdparty`
-   `m.id.phone`

##### Matrix User ID

| Type        | Description                                |
|-------------|--------------------------------------------|
| `m.id.user` | The user is identified by their Matrix ID. |

A client can identify a user using their Matrix ID. This can either be
the fully qualified Matrix user ID, or just the localpart of the user
ID.

```json
"identifier": {
  "type": "m.id.user",
  "user": "<user_id or user localpart>"
}
```

##### Third-party ID

| Type              | Description                                                               |
|-------------------|---------------------------------------------------------------------------|
| `m.id.thirdparty` | The user is identified by a third-party identifier in canonicalised form. |

A client can identify a user using a 3PID associated with the user's
account on the homeserver, where the 3PID was previously associated
using the `/account/3pid`\_ API. See the [3PID
Types](/appendices#3pid-types) Appendix for a list of Third-party
ID media.

```json
"identifier": {
  "type": "m.id.thirdparty",
  "medium": "<The medium of the third party identifier>",
  "address": "<The canonicalised third party address of the user>"
}
```

##### Phone number

| Type         | Description                               |
|--------------|-------------------------------------------|
| `m.id.phone` | The user is identified by a phone number. |

A client can identify a user using a phone number associated with the
user's account, where the phone number was previously associated using
the `/account/3pid`\_ API. The phone number can be passed in as entered
by the user; the homeserver will be responsible for canonicalising it.
If the client wishes to canonicalise the phone number, then it can use
the `m.id.thirdparty` identifier type with a `medium` of `msisdn`
instead.

```json
"identifier": {
  "type": "m.id.phone",
  "country": "<The country that the phone number is from>",
  "phone": "<The phone number>"
}
```

The `country` is the two-letter uppercase ISO-3166-1 alpha-2 country
code that the number in `phone` should be parsed as if it were dialled
from.

### Login

A client can obtain access tokens using the `/login` API.

Note that this endpoint does <span class="title-ref">not</span>
currently use the [User-Interactive Authentication
API](#user-interactive-authentication-api).

For a simple username/password login, clients should submit a `/login`
request as follows:

```json
{
  "type": "m.login.password",
  "identifier": {
    "type": "m.id.user",
    "user": "<user_id or user localpart>"
  },
  "password": "<password>"
}
```

Alternatively, a client can use a 3PID bound to the user's account on
the homeserver using the `/account/3pid`\_ API rather than giving the
`user` explicitly, as follows:

```json
{
  "type": "m.login.password",
  "identifier": {
    "medium": "<The medium of the third party identifier>",
    "address": "<The canonicalised third party address of the user>"
  },
  "password": "<password>"
}
```

In the case that the homeserver does not know about the supplied 3PID,
the homeserver must respond with `403 Forbidden`.

To log in using a login token, clients should submit a `/login` request
as follows:

```json
{
  "type": "m.login.token",
  "token": "<login token>"
}
```

As with [token-based]() interactive login, the `token` must encode the
user ID. In the case that the token is not valid, the homeserver must
respond with `403 Forbidden` and an error code of `M_FORBIDDEN`.

If the homeserver advertises `m.login.sso` as a viable flow, and the
client supports it, the client should redirect the user to the
`/redirect` endpoint for [client login via SSO](#client-login-via-sso). After authentication
is complete, the client will need to submit a `/login` request matching
`m.login.token`.

#### Appservice Login

{{% added-in v="1.2" %}}

An appservice can log in by providing a valid appservice token and a user within the appservice's
namespace.

{{% boxes/note %}}
Appservices do not need to log in as individual users in all cases, as they
can perform [Identity Assertion](/application-service-api#identity-assertion)
using the appservice token. However, if the appservice needs a scoped token
for a single user then they can use this API instead.
{{% /boxes/note %}}

This request must be authenticated by the [appservice `as_token`](/application-service-api#registration)
(see [Client Authentication](#client-authentication) on how to provide the token).

To use this login type, clients should submit a `/login` request as follows:

```json
{
  "type": "m.login.application_service",
  "identifier": {
    "type": "m.id.user",
    "user": "<user_id or user localpart>"
  }
}
```

If the access token is not valid, does not correspond to an appservice
or the user has not previously been registered then the homeserver will
respond with an errcode of `M_FORBIDDEN`.

If the access token does correspond to an appservice, but the user id does
not lie within its namespace then the homeserver will respond with an
errcode of `M_EXCLUSIVE`.

{{% http-api spec="client-server" api="login" %}}

{{% http-api spec="client-server" api="logout" %}}

#### Login Fallback

If a client does not recognize any or all login flows it can use the
fallback login API:

    GET /_matrix/static/client/login/

This returns an HTML and JavaScript page which can perform the entire
login process. The page will attempt to call the JavaScript function
`window.onLogin` when login has been successfully completed.

{{% added-in v="1.1" %}} Non-credential parameters valid for the `/login`
endpoint can be provided as query string parameters here. These are to be
forwarded to the login endpoint during the login process. For example:

    GET /_matrix/static/client/login/?device_id=GHTYAJCE

### Account registration and management

{{% http-api spec="client-server" api="registration" %}}

#### Notes on password management

{{% boxes/warning %}}
Clients SHOULD enforce that the password provided is suitably complex.
The password SHOULD include a lower-case letter, an upper-case letter, a
number and a symbol and be at a minimum 8 characters in length. Servers
MAY reject weak passwords with an error code `M_WEAK_PASSWORD`.
{{% /boxes/warning %}}

### Adding Account Administrative Contact Information

A homeserver may keep some contact information for administrative use.
This is independent of any information kept by any identity servers,
though can be proxied (bound) to the identity server in many cases.

{{% boxes/note %}}
This section deals with two terms: "add" and "bind". Where "add" (or
"remove") is used, it is speaking about an identifier that was not bound
to an identity server. As a result, "bind" (or "unbind") references an
identifier that is found in an identity server. Note that an identifier
can be added and bound at the same time, depending on context.
{{% /boxes/note %}}

{{% http-api spec="client-server" api="administrative_contact" %}}

### Current account information

{{% http-api spec="client-server" api="whoami" %}}

#### Notes on identity servers

Identity servers in Matrix store bindings (relationships) between a
user's third party identifier, typically email or phone number, and
their user ID. Once a user has chosen an identity server, that identity
server should be used by all clients.

Clients can see which identity server the user has chosen through the
`m.identity_server` account data event, as described below. Clients
SHOULD refrain from making requests to any identity server until the
presence of `m.identity_server` is confirmed as (not) present. If
present, the client SHOULD check for the presence of the `base_url`
property in the event's content. If the `base_url` is present, the
client SHOULD use the identity server in that property as the identity
server for the user. If the `base_url` is missing, or the account data
event is not present, the client SHOULD use whichever default value it
normally would for an identity server, if applicable. Clients SHOULD NOT
update the account data with the default identity server when the user
is missing an identity server in their account data.

Clients SHOULD listen for changes to the `m.identity_server` account
data event and update the identity server they are contacting as a
result.

If the client offers a way to set the identity server to use, it MUST
update the value of `m.identity_server` accordingly. A `base_url` of
`null` MUST be treated as though the user does not want to use an
identity server, disabling all related functionality as a result.

Clients SHOULD refrain from populating the account data as a migration
step for users who are lacking the account data, unless the user sets
the identity server within the client to a value. For example, a user
which has no `m.identity_server` account data event should not end up
with the client's default identity server in their account data, unless
the user first visits their account settings to set the identity server.

{{% event event="m.identity_server" %}}

## Capabilities negotiation

A homeserver may not support certain operations and clients must be able
to query for what the homeserver can and can't offer. For example, a
homeserver may not support users changing their password as it is
configured to perform authentication against an external system.

The capabilities advertised through this system are intended to
advertise functionality which is optional in the API, or which depend in
some way on the state of the user or server. This system should not be
used to advertise unstable or experimental features - this is better
done by the `/versions` endpoint.

Some examples of what a reasonable capability could be are:

-   Whether the server supports user presence.
-   Whether the server supports optional features, such as the user or
    room directories.
-   The rate limits or file type restrictions imposed on clients by the
    server.

Some examples of what should **not** be a capability are:

-   Whether the server supports a feature in the `unstable`
    specification.
-   Media size limits - these are handled by the
    [`/config`](#get_matrixmediav3config) API.
-   Optional encodings or alternative transports for communicating with
    the server.

Capabilities prefixed with `m.` are reserved for definition in the
Matrix specification while other values may be used by servers using the
Java package naming convention. The capabilities supported by the Matrix
specification are defined later in this section.

{{% http-api spec="client-server" api="capabilities" %}}

### `m.change_password` capability

This capability has a single flag, `enabled`, which indicates whether or
not the user can use the `/account/password` API to change their
password. If not present, the client should assume that password changes
are possible via the API. When present, clients SHOULD respect the
capability's `enabled` flag and indicate to the user if they are unable
to change their password.

An example of the capability API's response for this capability is:

```json
{
  "capabilities": {
    "m.change_password": {
      "enabled": false
    }
  }
}
```

### `m.room_versions` capability

This capability describes the default and available room versions a
server supports, and at what level of stability. Clients should make use
of this capability to determine if users need to be encouraged to
upgrade their rooms.

An example of the capability API's response for this capability is:

```json
{
  "capabilities": {
    "m.room_versions": {
      "default": "1",
      "available": {
        "1": "stable",
        "2": "stable",
        "3": "unstable",
        "custom-version": "unstable"
      }
    }
  }
}
```

This capability mirrors the same restrictions of [room
versions](/rooms) to describe which versions are
stable and unstable. Clients should assume that the `default` version is
`stable`. Any version not explicitly labelled as `stable` in the
`available` versions is to be treated as `unstable`. For example, a
version listed as `future-stable` should be treated as `unstable`.

The `default` version is the version the server is using to create new
rooms. Clients should encourage users with sufficient permissions in a
room to upgrade their room to the `default` version when the room is
using an `unstable` version.

When this capability is not listed, clients should use `"1"` as the
default and only stable `available` room version.

### `m.set_displayname` capability

This capability has a single flag, `enabled`, to denote whether the user
is able to change their own display name via profile endpoints. Cases for
disabling might include users mapped from external identity/directory
services, such as LDAP.

Note that this is well paired with the `m.set_avatar_url` capability.

When not listed, clients should assume the user is able to change their
display name.

An example of the capability API's response for this capability is:

```json
{
  "capabilities": {
    "m.set_displayname": {
      "enabled": false
    }
  }
}
```

### `m.set_avatar_url` capability

This capability has a single flag, `enabled`, to denote whether the user
is able to change their own avatar via profile endpoints. Cases for
disabling might include users mapped from external identity/directory
services, such as LDAP.

Note that this is well paired with the `m.set_displayname` capability.

When not listed, clients should assume the user is able to change their
avatar.

An example of the capability API's response for this capability is:

```json
{
  "capabilities": {
    "m.set_avatar_url": {
      "enabled": false
    }
  }
}
```

### `m.3pid_changes` capability

This capability has a single flag, `enabled`, to denote whether the user
is able to add, remove, or change 3PID associations on their account. Note
that this only affects a user's ability to use the
[Admin Contact Information](#adding-account-administrative-contact-information)
API, not endpoints exposed by an Identity Service. Cases for disabling
might include users mapped from external identity/directory  services,
such as LDAP.

When not listed, clients should assume the user is able to modify their 3PID
associations.

An example of the capability API's response for this capability is:

```json
{
  "capabilities": {
    "m.3pid_changes": {
      "enabled": false
    }
  }
}
```

## Filtering

Filters can be created on the server and can be passed as a parameter to
APIs which return events. These filters alter the data returned from
those APIs. Not all APIs accept filters.

### Lazy-loading room members

Membership events often take significant resources for clients to track.
In an effort to reduce the number of resources used, clients can enable
"lazy-loading" for room members. By doing this, servers will attempt to
only send membership events which are relevant to the client.

It is important to understand that lazy-loading is not intended to be a
perfect optimisation, and that it may not be practical for the server to
calculate precisely which membership events are relevant to the client.
As a result, it is valid for the server to send redundant membership
events to the client to ease implementation, although such redundancy
should be minimised where possible to conserve bandwidth.

In terms of filters, lazy-loading is enabled by enabling
`lazy_load_members` on a `RoomEventFilter` (or a `StateFilter` in the
case of `/sync` only). When enabled, lazy-loading aware endpoints (see
below) will only include membership events for the `sender` of events
being included in the response. For example, if a client makes a `/sync`
request with lazy-loading enabled, the server will only return
membership events for the `sender` of events in the timeline, not all
members of a room.

When processing a sequence of events (e.g. by looping on `/sync` or
paginating `/messages`), it is common for blocks of events in the
sequence to share a similar set of senders. Rather than responses in the
sequence sending duplicate membership events for these senders to the
client, the server MAY assume that clients will remember membership
events they have already been sent, and choose to skip sending
membership events for members whose membership has not changed. These
are called 'redundant membership events'. Clients may request that
redundant membership events are always included in responses by setting
`include_redundant_members` to true in the filter.

The expected pattern for using lazy-loading is currently:

-   Client performs an initial /sync with lazy-loading enabled, and
    receives only the membership events which relate to the senders of
    the events it receives.
-   Clients which support display-name tab-completion or other
    operations which require rapid access to all members in a room
    should call /members for the currently selected room, with an `?at`
    parameter set to the /sync response's from token. The member list
    for the room is then maintained by the state in subsequent
    incremental /sync responses.
-   Clients which do not support tab-completion may instead pull in
    profiles for arbitrary users (e.g. read receipts, typing
    notifications) on demand by querying the room state or `/profile`.

The current endpoints which support lazy-loading room members are:

-   [`/sync`](/client-server-api/#get_matrixclientv3sync)
-   [`/rooms/<room_id>/messages`](/client-server-api/#get_matrixclientv3roomsroomidmessages)
-   [`/rooms/{roomId}/context/{eventId}`](/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)

### API endpoints

{{% http-api spec="client-server" api="filter" %}}

## Events

The model of conversation history exposed by the client-server API can
be considered as a list of events. The server 'linearises' the
eventually-consistent event graph of events into an 'event stream' at
any given point in time:

    [E0]->[E1]->[E2]->[E3]->[E4]->[E5]

### Types of room events

Room events are split into two categories:

* **State events**: These are events which update the metadata state of the room (e.g. room
topic, room membership etc). State is keyed by a tuple of event `type`
and a `state_key`. State in the room with the same key-tuple will be
overwritten.

* **Message events**: These are events which describe transient "once-off" activity in a room:
typically communication such as sending an instant message or setting up
a VoIP call.

This specification outlines several events, all with the event type
prefix `m.`. (See [Room Events](#room-events) for the m. event
specification.) However, applications may wish to add their own type of
event, and this can be achieved using the REST API detailed in the
following sections. If new events are added, the event `type` key SHOULD
follow the Java package naming convention, e.g.
`com.example.myapp.event`. This ensures event types are suitably
namespaced for each application and reduces the risk of clashes.

{{% boxes/note %}}
Events are not limited to the types defined in this specification. New
or custom event types can be created on a whim using the Java package
naming convention. For example, a `com.example.game.score` event can be
sent by clients and other clients would receive it through Matrix,
assuming the client has access to the `com.example` namespace.
{{% /boxes/note %}}

### Room event format

The "federation" format of a room event, which is used internally by homeservers
and between homeservers via the Server-Server API, depends on the ["room
version"](/rooms) in use by the room. See, for example, the definitions
in [room version 1](/rooms/v1#event-format) and [room version
3](/rooms/v3#event-format).

However, it is unusual that a Matrix client would encounter this event
format. Instead, homeservers are responsible for converting events into the
format shown below so that they can be easily parsed by clients.

{{% boxes/warning %}}
Event bodies are considered untrusted data. This means that any application using
Matrix must validate that the event body is of the expected shape/schema
before using the contents verbatim.

**It is not safe to assume that an event body will have all the expected
fields of the expected types.**

See [MSC2801](https://github.com/matrix-org/matrix-doc/pull/2801) for more
detail on why this assumption is unsafe.
{{% /boxes/warning %}}

{{% definition path="api/client-server/definitions/client_event" %}}

### Stripped state

Stripped state events are simplified state events to help a potential
joiner identify the room. These state events can only have the `sender`,
`type`, `state_key` and `content` keys present.

These stripped state events typically appear on invites, knocks, and in
other places where a user *could* join the room under the conditions
available (such as a [`restricted` room](#restricted-rooms)).

Clients should only use stripped state events so long as they don't have
access to the proper state of the room. Once the state of the room is
available, all stripped state should be discarded. In cases where the
client has an archived state of the room (such as after being kicked)
and the client is receiving stripped state for the room, such as from an
invite or knock, then the stripped state should take precedence until
fresh state can be acquired from a join.

The following state events should be represented as stripped state when
possible:

* [`m.room.create`](#mroomcreate)
* [`m.room.name`](#mroomname)
* [`m.room.avatar`](#mroomavatar)
* [`m.room.topic`](#mroomtopic)
* [`m.room.join_rules`](#mroomjoin_rules)
* [`m.room.canonical_alias`](#mroomcanonical_alias)
* [`m.room.encryption`](#mroomencryption)

{{% boxes/note %}}
Clients should inspect the list of stripped state events and not assume any
particular event is present. The server might include events not described
here as well.
{{% /boxes/note %}}

{{% boxes/rationale %}}
The name, avatar, topic, and aliases are presented as aesthetic information
about the room, allowing users to make decisions about whether or not they
want to join the room.

The join rules are given to help the client determine *why* it is able to
potentially join. For example, annotating the room decoration with iconography
consistent with the respective join rule for the room.

The create event can help identify what kind of room is being joined, as it
may be a Space or other kind of room. The client might choose to render the
invite in a different area of the application as a result.

Similar to join rules, the encryption information is given to help clients
decorate the room with appropriate iconography or messaging.
{{% /boxes/rationale %}}

{{% boxes/warning %}}
Although stripped state is usually generated and provided by the server, it
is still possible to be incorrect on the receiving end. The stripped state
events are not signed and could theoretically be modified, or outdated due to
updates not being sent.
{{% /boxes/warning %}}

{{% event-fields event_type="stripped_state" %}}

### Size limits

The complete event MUST NOT be larger than 65536 bytes, when formatted
with the [federation event format](#room-event-format), including any
signatures, and encoded as [Canonical
JSON](/appendices#canonical-json).

There are additional restrictions on sizes per key:

-   `sender` MUST NOT exceed 255 bytes (including domain).
-   `room_id` MUST NOT exceed 255 bytes.
-   `state_key` MUST NOT exceed 255 bytes.
-   `type` MUST NOT exceed 255 bytes.
-   `event_id` MUST NOT exceed 255 bytes.

Some event types have additional size restrictions which are specified
in the description of the event. Additional keys have no limit other
than that implied by the total 64 KiB limit on events.

### Room Events

{{% boxes/note %}}
This section is a work in progress.
{{% /boxes/note %}}

This specification outlines several standard event types, all of which
are prefixed with `m.`

{{% event event="m.room.canonical_alias" %}}

{{% event event="m.room.create" %}}

{{% event event="m.room.join_rules" %}}

{{% event event="m.room.member" %}}

{{% event event="m.room.power_levels" %}}

#### Historical events

Some events within the `m.` namespace might appear in rooms, however
they serve no significant meaning in this version of the specification.
They are:

-   `m.room.aliases`

Previous versions of the specification have more information on these
events.

### Syncing

To read events, the intended flow of operation is for clients to first
call the [`/sync`](/client-server-api/#get_matrixclientv3sync) API without a `since` parameter. This returns the
most recent message events for each room, as well as the state of the
room at the start of the returned timeline. The response also includes a
`next_batch` field, which should be used as the value of the `since`
parameter in the next call to `/sync`. Finally, the response includes,
for each room, a `prev_batch` field, which can be passed as a `start`
parameter to the [`/rooms/<room_id>/messages`](/client-server-api/#get_matrixclientv3roomsroomidmessages) API to retrieve earlier
messages.

For example, a `/sync` request might return a range of four events
`E2`, `E3`, `E4` and `E5` within a given room, omitting two prior events
`E0` and `E1`. This can be visualised as follows:

```
    [E0]->[E1]->[E2]->[E3]->[E4]->[E5]
               ^                      ^
               |                      |
         prev_batch: '1-2-3'        next_batch: 'a-b-c'
```

Clients then receive new events by "long-polling" the homeserver via the
`/sync` API, passing the value of the `next_batch` field from the
response to the previous call as the `since` parameter. The client
should also pass a `timeout` parameter. The server will then hold open
the HTTP connection for a short period of time waiting for new events,
returning early if an event occurs. Only the `/sync` API (and the
deprecated `/events` API) support long-polling in this way.

Continuing the example above, an incremental sync might report
a single new event `E6`. The response can be visualised as:

```
    [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]
                                      ^     ^
                                      |     |
                                      |  next_batch: 'x-y-z'
                                    prev_batch: 'a-b-c'
```

Normally, all new events which are visible to the client will appear in
the response to the `/sync` API. However, if a large number of events
arrive between calls to `/sync`, a "limited" timeline is returned,
containing only the most recent message events. A state "delta" is also
returned, summarising any state changes in the omitted part of the
timeline. The client may therefore end up with "gaps" in its knowledge
of the message timeline. The client can fill these gaps using the
[`/rooms/<room_id>/messages`](/client-server-api/#get_matrixclientv3roomsroomidmessages) API.

Continuing our example, suppose we make a third `/sync` request asking for
events since the last sync, by passing the `next_batch` token `x-y-z` as
the `since` parameter. The server knows about four new events, `E7`, `E8`,
`E9` and `E10`, but decides this is too many to report at once. Instead,
the server sends a `limited` response containing `E8`, `E9` and `E10`but
omitting `E7`. This forms a gap, which we can see in the visualisation:

```
                                            | gap |
                                            | <-> |
    [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]->[E7]->[E8]->[E9]->[E10]
                                            ^     ^                  ^
                                            |     |                  |
                                 since: 'x-y-z'   |                  |
                                       prev_batch: 'd-e-f'       next_batch: 'u-v-w'
```

The limited response includes a state delta which describes how the state
of the room changes over the gap. This delta explains how to build the state
prior to returned timeline (i.e. at `E7`) from the state the client knows
(i.e. at `E6`). To close the gap, the client should make a request to
[`/rooms/<room_id>/messages`](/client-server-api/#get_matrixclientv3roomsroomidmessages)
with the query parameters `from=x-y-z` and `to=d-e-f`.

{{% boxes/warning %}}
Events are ordered in this API according to the arrival time of the
event on the homeserver. This can conflict with other APIs which order
events based on their partial ordering in the event graph. This can
result in duplicate events being received (once per distinct API
called). Clients SHOULD de-duplicate events based on the event ID when
this happens.
{{% /boxes/warning %}}

{{% boxes/note %}}
The `/sync` API returns a `state` list which is separate from the
`timeline`. This `state` list allows clients to keep their model of the
room state in sync with that on the server. In the case of an initial
(`since`-less) sync, the `state` list represents the complete state of
the room at the **start** of the returned timeline (so in the case of a
recently-created room whose state fits entirely in the `timeline`, the
`state` list will be empty).

In the case of an incremental sync, the `state` list gives a delta
between the state of the room at the `since` parameter and that at the
start of the returned `timeline`. (It will therefore be empty unless the
timeline was `limited`.)

In both cases, it should be noted that the events returned in the
`state` list did **not** necessarily take place just before the returned
`timeline`, so clients should not display them to the user in the
timeline.
{{% /boxes/note %}}

{{% boxes/rationale %}}
An early design of this specification made the `state` list represent
the room state at the end of the returned timeline, instead of the
start. This was unsatisfactory because it led to duplication of events
between the `state` list and the `timeline`, but more importantly, it
made it difficult for clients to show the timeline correctly.

In particular, consider a returned timeline \[M0, S1, M2\], where M0 and
M2 are both messages sent by the same user, and S1 is a state event
where that user changes their displayname. If the `state` list
represents the room state at the end of the timeline, the client must
take a copy of the state dictionary, and *rewind* S1, in order to
correctly calculate the display name for M0.
{{% /boxes/rationale %}}

{{% http-api spec="client-server" api="sync" %}}

{{% http-api spec="client-server" api="old_sync" %}}

### Getting events for a room

There are several APIs provided to `GET` events for a room:

{{% http-api spec="client-server" api="rooms" %}}

{{% http-api spec="client-server" api="message_pagination" %}}

{{% http-api spec="client-server" api="room_initial_sync" %}}

### Sending events to a room

{{% http-api spec="client-server" api="room_state" %}}

**Examples**

Valid requests look like:

```
PUT /rooms/!roomid:domain/state/m.example.event
{ "key" : "without a state key" }
```
```
PUT /rooms/!roomid:domain/state/m.another.example.event/foo
{ "key" : "with 'foo' as the state key" }
```

In contrast, these requests are invalid:

```
POST /rooms/!roomid:domain/state/m.example.event/
{ "key" : "cannot use POST here" }
```
```
PUT /rooms/!roomid:domain/state/m.another.example.event/foo/11
{ "key" : "txnIds are not supported" }
```

Care should be taken to avoid setting the wrong `state key`:

```
PUT /rooms/!roomid:domain/state/m.another.example.event/11
{ "key" : "with '11' as the state key, but was probably intended to be a txnId" }
```

The `state_key` is often used to store state about individual users, by
using the user ID as the `state_key` value. For example:

```
PUT /rooms/!roomid:domain/state/m.favorite.animal.event/%40my_user%3Aexample.org
{ "animal" : "cat", "reason": "fluffy" }
```

In some cases, there may be no need for a `state_key`, so it can be
omitted:

```
PUT /rooms/!roomid:domain/state/m.room.bgd.color
{ "color": "red", "hex": "#ff0000" }
```

{{% http-api spec="client-server" api="room_send" %}}

### Redactions

Since events are extensible it is possible for malicious users and/or
servers to add keys that are, for example offensive or illegal. Since
some events cannot be simply deleted, e.g. membership events, we instead
'redact' events. This involves removing all keys from an event that are
not required by the protocol. This stripped down event is thereafter
returned anytime a client or remote server requests it. Redacting an
event cannot be undone, allowing server owners to delete the offending
content from the databases. Servers should include a copy of the
`m.room.redaction` event under `unsigned` as `redacted_because`
when serving the redacted event to clients.

The exact algorithm to apply against an event is defined in the [room
version specification](/rooms), as are the criteria homeservers should
use when deciding whether to accept a redaction event from a remote
homeserver.

When a client receives an `m.room.redaction` event, it should change
the affected event in the same way a server does.

{{% boxes/note %}}
Redacted events can still affect the state of the room. When redacted,
state events behave as though their properties were simply not
specified, except those protected by the redaction algorithm. For
example, a redacted `join` event will still result in the user being
considered joined. Similarly, a redacted topic does not necessarily
cause the topic to revert to what it was prior to the event - it causes
the topic to be removed from the room.
{{% /boxes/note %}}

#### Events

{{% event event="m.room.redaction" %}}

#### Client behaviour

{{% http-api spec="client-server" api="redaction" %}}

## Rooms

### Types

{{% added-in v="1.2" %}}

Optionally, rooms can have types to denote their intended function. A room
without a type does not necessarily mean it has a specific default function,
though commonly these rooms will be for conversational purposes.

Room types are best applied when a client might need to differentiate between
two different rooms, such as conversation-holding and data-holding. If a room
has a type, it is specified in the `type` key of an [`m.room.create`](#mroomcreate)
event. To specify a room's type, provide it as part of `creation_content` on
the create room request.

In this specification the following room types are specified:

* [`m.space`](#spaces)

Unspecified room types are permitted through the use of
[Namespaced Identifiers](/appendices/#common-namespaced-identifier-grammar).

### Creation

The homeserver will create an `m.room.create` event when a room is
created, which serves as the root of the event graph for this room. This
event also has a `creator` key which contains the user ID of the room
creator. It will also generate several other events in order to manage
permissions in this room. This includes:

-   `m.room.power_levels` : Sets the power levels of users and required power
    levels for various actions within the room such as sending events.

-   `m.room.join_rules` : Whether the room is "invite-only" or not.

See [Room Events](#room-events) for more information on these events. To
create a room, a client has to use the following API.

{{% http-api spec="client-server" api="create_room" %}}

### Room aliases

Servers may host aliases for rooms with human-friendly names. Aliases
take the form `#friendlyname:server.name`.

As room aliases are scoped to a particular homeserver domain name, it is
likely that a homeserver will reject attempts to maintain aliases on
other domain names. This specification does not provide a way for
homeservers to send update requests to other servers. However,
homeservers MUST handle `GET` requests to resolve aliases on other
servers; they should do this using the federation API if necessary.

Rooms do not store a list of all aliases present on a room, though
members of the room with relevant permissions may publish preferred
aliases through the `m.room.canonical_alias` state event. The aliases in
the state event should point to the room ID they are published within,
however room aliases can and do drift to other room IDs over time.
Clients SHOULD NOT treat the aliases as accurate. They SHOULD be checked
before they are used or shared with another user. If a room appears to
have a room alias of `#alias:example.com`, this SHOULD be checked to
make sure that the room's ID matches the `room_id` returned from the
request.

{{% http-api spec="client-server" api="directory" %}}

### Permissions

{{% boxes/note %}}
This section is a work in progress.
{{% /boxes/note %}}

Permissions for rooms are done via the concept of power levels - to do
any action in a room a user must have a suitable power level. Power
levels are stored as state events in a given room. The power levels
required for operations and the power levels for users are defined in
`m.room.power_levels`, where both a default and specific users' power
levels can be set. By default all users have a power level of 0, other
than the room creator whose power level defaults to 100. Users can grant
other users increased power levels up to their own power level. For
example, user A with a power level of 50 could increase the power level
of user B to a maximum of level 50. Power levels for users are tracked
per-room even if the user is not present in the room. The keys contained
in `m.room.power_levels` determine the levels required for certain
operations such as kicking, banning and sending state events. See
[m.room.power\_levels](#room-events) for more information.

Clients may wish to assign names to particular power levels. A suggested
mapping is as follows: - 0 User - 50 Moderator - 100 Admin

### Room membership

Users need to be a member of a room in order to send and receive events
in that room. There are several states in which a user may be, in
relation to a room:

-   Unrelated (the user cannot send or receive events in the room)
-   Knocking (the user has requested to participate in the room, but has
    not yet been allowed to)
-   Invited (the user has been invited to participate in the room, but
    is not yet participating)
-   Joined (the user can send and receive events in the room)
-   Banned (the user is not allowed to join the room)

There are a few notable exceptions which allow non-joined members of the
room to send events in the room:

- Users wishing to reject an invite would send `m.room.member` events with
  `content.membership` of `leave`. They must have been invited first.

- If the room allows, users can send `m.room.member` events with `content.membership`
  of `knock` to knock on the room. This is a request for an invite by the user.

- To retract a previous knock, a user would send a `leave` event similar to
  rejecting an invite.

Some rooms require that users be invited to it before they can join;
others allow anyone to join. Whether a given room is an "invite-only"
room is determined by the room config key `m.room.join_rules`. It can
have one of the following values:

`public`
This room is free for anyone to join without an invite.

`invite`
This room can only be joined if you were invited.

`knock`
This room can only be joined if you were invited, and allows anyone to
request an invite to the room. Note that this join rule is only available
in room versions [which support knocking](/rooms/#feature-matrix).

{{% added-in v="1.2" %}} `restricted`
This room can be joined if you were invited or if you are a member of another
room listed in the join rules. If the server cannot verify membership for any
of the listed rooms then you can only join with an invite. Note that this rule
is only expected to work in room versions [which support it](/rooms/#feature-matrix).

The allowable state transitions of membership are:

![membership-flow-diagram](/diagrams/membership.png)

{{% http-api spec="client-server" api="list_joined_rooms" %}}

#### Joining rooms

{{% http-api spec="client-server" api="inviting" %}}

{{% http-api spec="client-server" api="joining" %}}

##### Knocking on rooms

{{% added-in v="1.1" %}}

<!--
This section is here because it's most similar to being invited/joining a
room, though has added complexity which needs to be explained. Otherwise
this will have been just the API definition and nothing more (like invites).
-->

If the join rules allow, external users to the room can `/knock` on it to
request permission to join. Users with appropriate permissions within the
room can then approve (`/invite`) or deny (`/kick`, `/ban`, or otherwise
set membership to `leave`) the knock. Knocks can be retracted by calling
`/leave` or otherwise setting membership to `leave`.

Users who are currently in the room, already invited, or banned cannot
knock on the room.

To accept another user's knock, the user must have permission to invite
users to the room. To reject another user's knock, the user must have
permission to either kick or ban users (whichever is being performed).
Note that setting another user's membership to `leave` is kicking them.

The knocking homeserver should assume that an invite to the room means
that the knock was accepted, even if the invite is not explicitly related
to the knock.

Homeservers are permitted to automatically accept invites as a result of
knocks as they should be aware of the user's intent to join the room. If
the homeserver is not auto-accepting invites (or there was an unrecoverable
problem with accepting it), the invite is expected to be passed down normally
to the client to handle. Clients can expect to see the join event if the
server chose to auto-accept.

{{% http-api spec="client-server" api="knocking" %}}

##### Restricted rooms

{{% added-in v="1.2" %}}

Restricted rooms are rooms with a `join_rule` of `restricted`. These rooms
are accompanied by "allow conditions" as described in the
[`m.room.join_rules`](#mroomjoin_rules) state event.

If the user has an invite to the room then the restrictions will not affect
them. They should be able to join by simply accepting the invite.

When joining without an invite, the server MUST verify that the requesting
user meets at least one of the conditions. If no conditions can be verified
or no conditions are satisfied, the user will not be able to join. When the
join is happening over federation, the remote server will check the conditions
before accepting the join. See the [Server-Server Spec](/server-server-api/#restricted-rooms)
for more information.

If the room is `restricted` but no valid conditions are presented then the
room is effectively invite only.

The user does not need to maintain the conditions in order to stay a member
of the room: the conditions are only checked/evaluated during the join process.

###### Conditions

Currently there is only one condition available: `m.room_membership`. This
condition requires the user trying to join the room to be a *joined* member
of another room (specifically, the `room_id` accompanying the condition). For
example, if `!restricted:example.org` wanted to allow joined members of
`!other:example.org` to join, `!restricted:example.org` would have the following
`content` for [`m.room.join_rules`](#mroomjoin_rules):

```json
{
  "join_rule": "restricted",
  "allow": [
    {
      "room_id": "!other:example.org",
      "type": "m.room_membership"
    }
  ]
}
```

#### Leaving rooms

A user can leave a room to stop receiving events for that room. A user
must have been invited to or have joined the room before they are
eligible to leave the room. Leaving a room to which the user has been
invited rejects the invite, and can retract a knock. Once a user leaves
a room, it will no longer appear in the response to the
[`/sync`](/client-server-api/#get_matrixclientv3sync) API unless it is
explicitly requested via a filter with the `include_leave` field set
to `true`.

Whether or not they actually joined the room, if the room is an
"invite-only" room the user will need to be re-invited before they can
re-join the room.

A user can also forget a room which they have left. Rooms which have
been forgotten will never appear the response to the [`/sync`](/client-server-api/#get_matrixclientv3sync) API,
until the user re-joins, is re-invited, or knocks.

A user may wish to force another user to leave a room. This can be done
by 'kicking' the other user. To do so, the user performing the kick MUST
have the required power level. Once a user has been kicked, the
behaviour is the same as if they had left of their own accord. In
particular, the user is free to re-join if the room is not
"invite-only".

{{% http-api spec="client-server" api="leaving" %}}

{{% http-api spec="client-server" api="kicking" %}}

##### Banning users in a room

A user may decide to ban another user in a room. 'Banning' forces the
target user to leave the room and prevents them from re-joining the
room. A banned user will not be treated as a joined user, and so will
not be able to send or receive events in the room. In order to ban
someone, the user performing the ban MUST have the required power level.
To ban a user, a request should be made to [`/rooms/<room_id>/ban`](/client-server-api/#post_matrixclientv3roomsroomidban)
with:

```json
{
  "user_id": "<user id to ban>",
  "reason": "string: <reason for the ban>"
}
````

Banning a user adjusts the banned member's membership state to `ban`.
Like with other membership changes, a user can directly adjust the
target member's state, by making a request to
`/rooms/<room id>/state/m.room.member/<user id>`:

```json
{
  "membership": "ban"
}
```

A user must be explicitly unbanned with a request to
[`/rooms/<room_id>/unban`](/client-server-api/#post_matrixclientv3roomsroomidunban) before they can re-join the room or be
re-invited.

{{% http-api spec="client-server" api="banning" %}}

### Listing rooms

{{% http-api spec="client-server" api="list_public_rooms" %}}

## User Data

### User Directory

{{% http-api spec="client-server" api="users" %}}

### Profiles

{{% http-api spec="client-server" api="profile" %}}

#### Events on Change of Profile Information

Because the profile display name and avatar information are likely to be
used in many places of a client's display, changes to these fields cause
an automatic propagation event to occur, informing likely-interested
parties of the new values. This change is conveyed using two separate
mechanisms:

-   an `m.room.member` event (with a `join` membership) is sent to every
    room the user is a member of, to update the `displayname` and
    `avatar_url`.
-   an `m.presence` presence status update is sent, again containing the
    new values of the `displayname` and `avatar_url` keys, in addition
    to the required `presence` key containing the current presence state
    of the user.

Both of these should be done automatically by the homeserver when a user
successfully changes their display name or avatar URL fields.

Additionally, when homeservers emit room membership events for their own
users, they should include the display name and avatar URL fields in
these events so that clients already have these details to hand, and do
not have to perform extra round trips to query it.

## Security

### Rate limiting

Homeservers SHOULD implement rate limiting to reduce the risk of being
overloaded. If a request is refused due to rate limiting, it should
return a standard error response of the form:

```json
{
  "errcode": "M_LIMIT_EXCEEDED",
  "error": "string",
  "retry_after_ms": integer (optional)
}
```

The `retry_after_ms` key SHOULD be included to tell the client how long
they have to wait in milliseconds before they can try again.

## Modules

Modules are parts of the Client-Server API which are not universal to
all endpoints. Modules are strictly defined within this specification
and should not be mistaken for experimental extensions or optional
features. A compliant server implementation MUST support all modules and
supporting specification (unless the implementation only targets clients
of certain profiles, in which case only the required modules for those
feature profiles MUST be implemented). A compliant client implementation
MUST support all the required modules and supporting specification for
the [Feature Profile](#feature-profiles) it targets.

### Feature Profiles

Matrix supports many different kinds of clients: from embedded IoT
devices to desktop clients. Not all clients can provide the same feature
sets as other clients e.g. due to lack of physical hardware such as not
having a screen. Clients can fall into one of several profiles and each
profile contains a set of features that the client MUST support. This
section details a set of "feature profiles". Clients are expected to
implement a profile in its entirety in order for it to be classified as
that profile.

#### Summary

| Module / Profile                                           | Web       | Mobile   | Desktop  | CLI      | Embedded |
|------------------------------------------------------------|-----------|----------|----------|----------|----------|
| [Instant Messaging](#instant-messaging)                    | Required  | Required | Required | Required | Optional |
| [Direct Messaging](#direct-messaging)                      | Required  | Required | Required | Required | Optional |
| [Mentions](#user-room-and-group-mentions)                  | Required  | Required | Required | Optional | Optional |
| [Presence](#presence)                                      | Required  | Required | Required | Required | Optional |
| [Push Notifications](#push-notifications)                  | Optional  | Required | Optional | Optional | Optional |
| [Receipts](#receipts)                                      | Required  | Required | Required | Required | Optional |
| [Fully read markers](#fully-read-markers)                  | Optional  | Optional | Optional | Optional | Optional |
| [Typing Notifications](#typing-notifications)              | Required  | Required | Required | Required | Optional |
| [VoIP](#voice-over-ip)                                     | Required  | Required | Required | Optional | Optional |
| [Ignoring Users](#ignoring-users)                          | Required  | Required | Required | Optional | Optional |
| [Reporting Content](#reporting-content)                    | Optional  | Optional | Optional | Optional | Optional |
| [Content Repository](#content-repository)                  | Required  | Required | Required | Optional | Optional |
| [Managing History Visibility](#room-history-visibility)    | Required  | Required | Required | Required | Optional |
| [Server Side Search](#server-side-search)                  | Optional  | Optional | Optional | Optional | Optional |
| [Room Upgrades](#room-upgrades)                            | Required  | Required | Required | Required | Optional |
| [Server Administration](#server-administration)            | Optional  | Optional | Optional | Optional | Optional |
| [Event Context](#event-context)                            | Optional  | Optional | Optional | Optional | Optional |
| [Third Party Networks](#third-party-networks)              | Optional  | Optional | Optional | Optional | Optional |
| [Send-to-Device Messaging](#send-to-device-messaging)      | Optional  | Optional | Optional | Optional | Optional |
| [Device Management](#device-management)                    | Optional  | Optional | Optional | Optional | Optional |
| [End-to-End Encryption](#end-to-end-encryption)            | Optional  | Optional | Optional | Optional | Optional |
| [Guest Accounts](#guest-access)                            | Optional  | Optional | Optional | Optional | Optional |
| [Room Previews](#room-previews)                            | Optional  | Optional | Optional | Optional | Optional |
| [Client Config](#client-config)                            | Optional  | Optional | Optional | Optional | Optional |
| [SSO Login](#sso-client-loginauthentication)               | Optional  | Optional | Optional | Optional | Optional |
| [OpenID](#openid)                                          | Optional  | Optional | Optional | Optional | Optional |
| [Stickers](#sticker-messages)                              | Optional  | Optional | Optional | Optional | Optional |
| [Server ACLs](#server-access-control-lists-acls-for-rooms) | Optional  | Optional | Optional | Optional | Optional |
| [Server Notices](#server-notices)                          | Optional  | Optional | Optional | Optional | Optional |
| [Moderation policies](#moderation-policy-lists)            | Optional  | Optional | Optional | Optional | Optional |
| [Spaces](#spaces)                                          | Optional  | Optional | Optional | Optional | Optional |

*Please see each module for more details on what clients need to
implement.*

#### Clients

##### Stand-alone web (`Web`)

This is a web page which heavily uses Matrix for communication.
Single-page web apps would be classified as a stand-alone web client, as
would multi-page web apps which use Matrix on nearly every page.

##### Mobile (`Mobile`)

This is a Matrix client specifically designed for consumption on mobile
devices. This is typically a mobile app but need not be so provided the
feature set can be reached (e.g. if a mobile site could display push
notifications it could be classified as a mobile client).

##### Desktop (`Desktop`)

This is a native GUI application which can run in its own environment
outside a browser.

##### Command Line Interface (`CLI`)

This is a client which is used via a text-based terminal.

##### Embedded (`Embedded`)

This is a client which is embedded into another application or an
embedded device.

###### Application

This is a Matrix client which is embedded in another website, e.g. using
iframes. These embedded clients are typically for a single purpose
related to the website in question, and are not intended to be
fully-fledged communication apps.

###### Device

This is a client which is typically running on an embedded device such
as a kettle, fridge or car. These clients tend to perform a few
operations and run in a resource constrained environment. Like embedded
applications, they are not intended to be fully-fledged communication
systems.

{{% cs-module name="instant_messaging" %}}
{{% cs-module name="voip_events" %}}
{{% cs-module name="typing_notifications" %}}
{{% cs-module name="receipts" %}}
{{% cs-module name="read_markers" %}}
{{% cs-module name="presence" %}}
{{% cs-module name="content_repo" %}}
{{% cs-module name="send_to_device" %}}
{{% cs-module name="device_management" %}}
{{% cs-module name="end_to_end_encryption" %}}
{{% cs-module name="secrets" %}}
{{% cs-module name="history_visibility" %}}
{{% cs-module name="push" %}}
{{% cs-module name="third_party_invites" %}}
{{% cs-module name="search" %}}
{{% cs-module name="guest_access" %}}
{{% cs-module name="room_previews" %}}
{{% cs-module name="tags" %}}
{{% cs-module name="account_data" %}}
{{% cs-module name="admin" %}}
{{% cs-module name="event_context" %}}
{{% cs-module name="sso_login" %}}
{{% cs-module name="dm" %}}
{{% cs-module name="ignore_users" %}}
{{% cs-module name="stickers" %}}
{{% cs-module name="report_content" %}}
{{% cs-module name="third_party_networks" %}}
{{% cs-module name="openid" %}}
{{% cs-module name="server_acls" %}}
{{% cs-module name="mentions" %}}
{{% cs-module name="room_upgrades" %}}
{{% cs-module name="server_notices" %}}
{{% cs-module name="moderation_policies" %}}
{{% cs-module name="spaces" %}}
