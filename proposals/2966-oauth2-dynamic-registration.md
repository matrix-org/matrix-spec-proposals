# MSC2966: Usage of OAuth 2.0 Dynamic Client Registration in Matrix

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC][MSC3861].

This MSC specifies how Matrix clients SHOULD leverage the OAuth 2.0 Dynamic Client Registration Protocol ([RFC 7591](https://tools.ietf.org/html/rfc7591)) to register themselves before initiating an authorization flow.

In brief, once a client has obtained the homeserver's OAuth 2.0 metadata per [MSC2965], and before it can initiate an authorization request per [MSC2964], the client needs a `client_id`, which it can obtain by registering itself with that homeserver.

## Proposal

### Prerequisites

This proposal requires the client to know the following authorization server metadata about the homeserver:

 - `registration_endpoint`: the URL where the client is able to register itself.

The discovery of the above metadata is out of scope for this MSC and is currently covered by [MSC2965].

### Client metadata

In OAuth 2.0, clients have a set of metadata values associated with their client identifier at an authorization server.
These values are used to describe the client to the user and define how the client interacts with the authorization server.

This MSC specifies what metadata values are required by the Matrix specification and how a client can register itself with a Matrix homeserver to get a client identifier.

None of the metadata values are specific to Matrix: they are all registered by various specifications in the [OAuth Dynamic Client Registration Metadata](https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#client-metadata) registry, and normative definitions of them are available in their respective RFCs in the registry.


#### `client_uri` and relationship with other URIs

Per [RFC 7591](https://tools.ietf.org/html/rfc7591), the `client_uri` MUST point to a valid web page that SHOULD give the user more information about the client.
This URL MUST use the `https` scheme and SHOULD NOT require authentication to access.
It MUST NOT use a user or password in the authority component of the URI.

The `client_uri` is required and the server MAY reject client registrations with an invalid or missing `client_uri`.
This URI is a common base for all the other URIs in the metadata: those MUST be either on the same host or on a subdomain of the host of the `client_uri`.
The port number, path and query components MAY be different.
For example, if the `client_uri` is `https://example.com/`, then one of the `redirect_uris` can be `https://example.com/callback` or `https://app.example.com/callback`, but not `https://app.com/callback`.

#### User-visible metadata values

The following metadata values SHOULD be used by clients to help users identify the client:

 - `client_name`: Human-readable name of the client to be presented to the user
 - `logo_uri`: URL that references a logo for the client
 - `tos_uri`: URL that points to a human-readable terms of service document for the client
 - `policy_uri`: URL that points to a human-readable policy document for the client

All the URIs MUST use the `https` scheme and use the `client_uri` as a common base, as defined by the previous section.

If provided by the client, the homeserver SHOULD show or link to the `tos_uri` and `policy_uri` to the user.
They MUST NOT use a user or password in the authority component of the URI.
They MUST point to a valid web page and SHOULD NOT require authentication to access.

All of these metadata values are optional.

##### Metadata localization

As per [RFC 7591 sec. 2.2](https://tools.ietf.org/html/rfc7591#section-2.2), these metadata values MAY be localized.
For example:

```json
{
  "client_name": "Digital mailbox",
  "client_name#en-US": "Digital mailbox",
  "client_name#en-GB": "Digital postbox",
  "client_name#fr": "Boîte aux lettres numérique",
  "tos_uri": "https://example.com/tos.html",
  "tos_uri#fr": "https://example.com/fr/tos.html",
  "policy_uri": "https://example.com/policy.html",
  "policy_uri#fr": "https://example.com/fr/policy.html"
}
```

#### Metadata values required by the OAuth 2.0 authorization grant flow

The following metadata values are required to be present to use the OAuth 2.0 authorization code grant and refresh token grant, as described in [MSC2964]:

 - `redirect_uris`: Array of redirection URIs for use in redirect-based flows
 - `response_types`: Array of the OAuth 2.0 response types that the client may use
 - `grant_types`: Array of OAuth 2.0 grant types that the client may use
 - `token_endpoint_auth_method`: String indicator of the requested authentication method for the token endpoint

The homeserver MUST support the `none` value for the `token_endpoint_auth_method`, as most Matrix clients are client-side only, do not have a server component, and therefore are public clients.

To use this grant:

 - the `redirect_uris` MUST have at least one value
 - the `response_types` MUST include `code`
 - the `grant_types` MUST include `authorization_code` and `refresh_token`

#### Redirect URI validation

The redirect URI plays a critical role in validating the authenticity of the client.
The client 'proves' its identity by demonstrating that it controls the redirect URI.
This is why it is critical to have strict validation of the redirect URI.

The `application_type` metadata is used to determine the type of client.
It defaults to `web` if not present, and can be set to `native` to indicate that the client is a native application.

In all cases, the redirect URI MUST NOT have a fragment component.

##### Web clients

`web` clients can use redirect URIs that:

 - MUST use the `https` scheme
 - MUST NOT use a user or password in the authority component of the URI
 - MUST use the client URI as a common base for the authority component, as defined previously
 - MAY include an `application/x-www-form-urlencoded` formatted query component

Examples of valid redirect URIs (with `https://example.com/` as the client URI):

 - `https://example.com/callback`
 - `https://app.example.com/callback`
 - `https://example.com:5173/?query=value`

Examples of invalid redirect URIs (with `https://example.com/` as the client URI):

 - `https://example.com/callback#fragment`
 - `http://example.com/callback`
 - `http://localhost/`

##### Native clients

`native` clients can use three types of redirect URIs:

 1. Private-Use URI Scheme:
    - the scheme MUST be prefixed with the client URI hostname in reverse-DNS notation. For example, if the client URI is `https://example.com/`, then a valid custom URI scheme would be `com.example.app:/`.
    - the URI MUST NOT have an authority component. This means that it MUST have either a single slash or none immediately following the scheme, with no hostname, username, or port.
 2. "http" URIs on the loopback interface:
    - it MUST use the `http` scheme
    - the host part MUST be `localhost`, `127.0.0.1`, or `[::1]`
    - it MUST have no port in the registered redirect URI. The homeserver MUST then accept any port number during the authorization flow.
 3. Claimed "https" Scheme URI:
    - some operating systems allow apps to claim "https" scheme URIs in the domains they control
    - when the browser encounters a claimed URI, instead of the page being loaded in the browser, the native app is launched with the URI supplied as a launch parameter
    - the same rules as for `web` clients apply

These restrictions are the same as defined by [RFC8252 sec. 7](https://tools.ietf.org/html/rfc8252#section-7).

Examples of valid redirect URIs (with `https://example.com/` as the client URI):

 - `com.example.app:/callback`
 - `com.example:/`
 - `com.example:callback`
 - `http://localhost/callback`
 - `http://127.0.0.1/callback`
 - `http://[::1]/callback`

Examples of invalid redirect URIs (with `https://example.com/` as the client URI):

 - `example:/callback`
 - `com.example.app://callback`
 - `https://localhost/callback`
 - `http://localhost:1234/callback`

### Dynamic client registration

Before initiating an authorization flow, the client MUST advertise its metadata to the homeserver to get back a `client_id`.

This is done through the `registration_endpoint` as described by [RFC7591 sec. 3](https://tools.ietf.org/html/rfc7591#section-3).

**Note**: Nothing in the usage of the `registration_endpoint` is specific to Matrix. The behaviours described here are the same as the ones defined in [RFC7591 sec. 3](https://tools.ietf.org/html/rfc7591#section-3).

To register, the client sends an HTTP POST to the `registration_endpoint` with its metadata as JSON in the body.
For example, the client could send the following registration request:

```http
POST /register HTTP/1.1
Content-Type: application/json
Accept: application/json
Server: auth.example.com
```

```json
{
  "client_name": "My App",
  "client_name#fr": "Mon application",
  "client_uri": "https://example.com/",
  "logo_uri": "https://example.com/logo.png",
  "tos_uri": "https://example.com/tos.html",
  "tos_uri#fr": "https://example.com/fr/tos.html",
  "policy_uri": "https://example.com/policy.html",
  "policy_uri#fr": "https://example.com/fr/policy.html",
  "redirect_uris": ["https://app.example.com/callback"],
  "token_endpoint_auth_method": "none",
  "response_types": ["code"],
  "grant_types": [
    "authorization_code",
    "refresh_token",
    "urn:ietf:params:oauth:grant-type:token-exchange"
  ],
  "application_type": "web"
}
```

The server MUST ignore `grant_types` and `response_types` that it does not understand.

Upon successful registration, the server replies with an *HTTP 201 Created* response, with a JSON object containing the allocated `client_id` and all the registered metadata values.

With the previous registration request, the server would reply with:

```json
{
  "client_id": "s6BhdRkqt3",
  "client_name": "My App",
  "client_uri": "https://example.com/",
  "logo_uri": "https://example.com/logo.png",
  "tos_uri": "https://example.com/tos.html",
  "policy_uri": "https://example.com/policy.html",
  "redirect_uris": ["https://app.example.com/callback"],
  "token_endpoint_auth_method": "none",
  "response_types": ["code"],
  "grant_types": ["authorization_code", "refresh_token"],
  "application_type": "web"
}
```

**Note**: in this example, the server has not registered the locale-specific values for `client_name`, `tos_uri`, and `policy_uri`, which is why they are not present in the response. The server also does not support the `urn:ietf:params:oauth:grant-type:token-exchange` grant type, which is why it is not present in the response.

The client MUST store the `client_id` for future use.

To avoid the number of client registrations growing over time, the server MAY choose to delete client registrations that don't have an active session.
The server MUST NOT delete client registrations that have an active session.

Clients MUST perform a new client registration at the start of each authorization flow.

## Potential issues

Because each client on each user device will do its own registration, they may all have different `client_id`s.
This means that the server may store the same client registration multiple times, which could lead to a large number of client registrations.

This can be mitigated by de-duplicating client registrations that have identical metadata.
By doing so, different users on different devices using the same client can share a single `client_id`, reducing the overall number of registrations.

A subsequent MSC could be proposed to reliably identify multiple instances of the same client beyond a strict comparison using signed client metadata.

## Alternatives

An alternative approach would be to have the client host a JSON file containing its metadata and use that URL as the `client_id`.
This is what the [*OAuth Client ID Metadata Document* draft](https://datatracker.ietf.org/doc/html/draft-parecki-oauth-client-id-metadata-document) proposes.

This approach has the advantage of being able to use the same `client_id` for different instances of the same client, but it has the disadvantage of requiring the client to host a JSON file on its own domain, as well as difficulties in handling updates to the metadata.

## Security considerations

The restrictions on the metadata values laid out in this MSC are a best effort to prevent client impersonation, but they are not flawless.

For web clients, it relies on the client's ability to prove ownership of the redirect URI, which can be guaranteed to some extent by sane DNS management and its use of TLS.
If a client-related domain name hosts an open redirector, it could be used to impersonate the client.

For native clients, because they can use private-use URI schemes and localhost redirectors, it relies more on the underlying operating system's security model and their application distribution model.
A good example of this is if a mobile client distributed through an app store registers the `app.acme.corp:` scheme in an effort to impersonate "ACME Corp's" app, then "ACME Corp" would have a valid case to take down the malicious app from the app store.

In both cases, it is crucial for the server to strictly enforce these restrictions and to show as much information about the client as possible to the user so they can make an informed decision.

## Unstable prefix

None relevant.

[RFC7591]: https://tools.ietf.org/html/rfc7591
[RFC7592]: https://tools.ietf.org/html/rfc7592
[RFC9126]: https://tools.ietf.org/html/rfc9126
[MSC2964]: https://github.com/matrix-org/matrix-spec-proposals/pull/2964
[MSC2965]: https://github.com/matrix-org/matrix-spec-proposals/pull/2965
[MSC3861]: https://github.com/matrix-org/matrix-spec-proposals/pull/3861
