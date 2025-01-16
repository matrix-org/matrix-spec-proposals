# MSC2966: Usage of OAuth 2.0 Dynamic Client Registration in Matrix

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC](https://github.com/matrix-org/matrix-spec-proposals/pull/3861).

This MSC specifies how Matrix clients should leverage the OAuth 2.0 Dynamic Client Registration Protocol ([RFC 7591](https://tools.ietf.org/html/rfc7591)) to register themselves before initiating an authorization flow.

## Proposal

### Prerequisites

This proposal requires the client to know the following authorization server metadata about the homeserver:

 - `registration_endpoint`: the URL where the client is able to register itself.

The discovery of the above metadata is out of scope for this MSC and is currently covered by [MSC2965](https://github.com/matrix-org/matrix-doc/pull/2965).

### Client metadata

In OAuth 2.0, clients have a set of metadata values associated with their client identifier at an authorization server.
These values are used to describe the client to the user and define how the client interacts with the authorization server.

This MSC specifies what metadata values are required by the Matrix specification and how a client can register itself with a Matrix homeserver to get a client identifier.

The metadata names are registered in the IANA [OAuth Dynamic Client Registration Metadata](https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#client-metadata) registry, and normative definitions of them are available in their respective RFCs in the registry.

#### Localizable metadata

#### `client_uri` and relationship with other URIs

The `client_uri` metadata is required to be a valid URI.
This URI must use the `https` scheme.

The host part of the URI must be a public hostname that is not a [public suffix](https://publicsuffix.org).
IP addresses and private hostnames like `localhost` are not allowed.

It is recommended that the `client_uri` is a web page that provides information about the client.
This page should be able to be accessed without requiring authentication.

This URI is a common base for all the other URIs in the metadata: those must be either on the same host or on a subdomain of the host of the `client_uri`.
For example, if the `client_uri` is `https://example.com/`, then one of the `redirect_uris` can be `https://example.com/callback` or `https://app.example.com/callback`, but not `https://app.com/callback`.

#### User-visible metadata values

The following metadata values should be used by clients to help users identify the client:

 - `client_name`: Human-readable name of the client to be presented to the user
 - `logo_uri`: URL that references a logo for the client
 - `tos_uri`: URL that points to a human-readable terms of service document for the client
 - `policy_uri`: URL that points to a human-readable policy document for the client

All the URIs must use the `https` scheme and use the `client_uri` as a common base.

If provided by the client, the homeserver should show or link to the `tos_uri` and `policy_uri` to the user.

All of these metadata values are optional.

As per [RFC 7591 sec. 2.2](https://tools.ietf.org/html/rfc7591#section-2.2), these metadata values may be localized.
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

The homeserver must support the `none` value for the `token_endpoint_auth_method`, as most Matrix clients are client-side only, do not have a server component, and therefore are public clients.

To use this grant:

 - the `redirect_uris` must have at least one value
 - the `response_types` must include `code`
 - the `grant_types` must include `authorization_code` and `refresh_token`

#### Redirect URI validation

The redirect URI plays a critical role in validating the authenticity of the client.
The client 'proves' its identity by demonstrating that it controls the redirect URI.
This is why it is critical to have strict validation of the redirect URI.

The `application_type` metadata is used to determine the type of client.
It defaults to `web` if not present, and can be set to `native` to indicate that the client is a native application.

In all cases, the redirect URI must not have a fragment component.

#### Web clients

`web` clients can use redirect URIs that:

 - must use the `https` scheme
 - must omit the port (to use the default port for https: 443)
 - must not use a user or password in the authority component of the URI
 - must use the client URI as a common base for the authority component

Examples of valid redirect URIs (with `https://example.com/` as the client URI):

 - `https://example.com/callback`
 - `https://app.example.com/callback`
 - `https://example.com/?query=value`

Examples of invalid redirect URIs (with `https://example.com/` as the client URI):

 - `https://example.com/callback#fragment`
 - `https://example.com:8080/callback`
 - `http://example.com/callback`
 - `http://localhost/`

#### Native clients

`native` clients can use three types of redirect URIs:

 1. Private-Use URI Scheme:
    - the scheme must be prefixed with the client URI hostname in reverse-DNS notation. For example, if the client URI is `https://example.com/`, then a valid custom URI scheme would be `com.example.app:/`.
    - the URI must not have an authority component. This means that it must have either a single slash or none immediately following the scheme, with no hostname, username, or port.
 2. "http" URIs on the loopback interface:
    - it must use the `http` scheme
    - the host part must be `localhost`, `127.0.0.1`, or `[::1]`
    - it must have no port registered. The homeserver must then accept any port number during the authorization flow.
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

Before initiating an authorization flow, the client must advertise its metadata to the homeserver to get back a `client_id`.

This is done through the `registration_endpoint` as described by [RFC7591 sec. 3](https://tools.ietf.org/html/rfc7591#section-3).

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
  "grant_types": ["authorization_code", "refresh_token"],
  "application_type": "web"
}
```

The server replies with a JSON object containing the `client_id` allocated, as well as all the metadata values that the server registered.

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
  "response_types": ["code"],
  "grant_types": ["authorization_code", "refresh_token"],
  "application_type": "web"
}
```

**Note**: in this example, the server has not registered the locale-specific values for `client_name`, `tos_uri`, and `policy_uri`, which is why they are not present in the response.

The client must store the `client_id` for future use.

## Potential issues

Because each client on each user device will do its own registration, they will all have different `client_id`s.
This means that the number of client registrations will grow exponentially.
A subsequent MSC could be proposed to identify multiple instances of the same client using signed client metadata.

## Alternatives

An alternative approach would be to have the client host a JSON file containing its metadata and use that URL as the `client_id`.
This is what the following [*OAuth Client ID Metadata Document* draft](https://datatracker.ietf.org/doc/html/draft-parecki-oauth-client-id-metadata-document) proposes.

This approach has the advantage of being able to use the same `client_id` for different instances of the same client, but it has the disadvantage of requiring the client to host a JSON file on its own domain, as well as difficulties in handling updates to the metadata.

## Security considerations

TBD

## Unstable prefix

None relevant.

[RFC7591]: https://tools.ietf.org/html/rfc7591
[MSC2964]: https://github.com/matrix-org/matrix-spec-proposals/pull/2964
