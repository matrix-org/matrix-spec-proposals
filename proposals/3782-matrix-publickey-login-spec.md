# MSC3782: Add public/private key login as a new authentication type to support decentralized authentication and decentralized identifiers

## Proposal

Cryptographic signatures have played a pivotal role in digital security and blockchain. They are used to prove
ownership of a public key without exposing its private key. This property can be (and has been) used for
decentralized authentication. A server can use signature verification to prove that the user has possession
of the private key to allow the user with that public key / identifier to log in.

The proposal is to add public key cryptography to Matrix as a new login type. This new login type would
enable two new features on the server:

1. Decentralized authentication

2. Decentralized user identifier

Decentrlized authentication gives the server the ability to cryptographically authenticate
a user without having to keep the user's secret or redirect the user to a central
identity service.

Decentralized user identifiers are verifiable, digital identities. They are represented
in a standard-conformant way. i.e. the identity is made up of parts according to
some standard specification. Once the identity is verified, the server can use
the identifier to find more information about the user from other servers in a
decentralized infrastructure, such as the blockchain networks.

The mapping between a decentralized identifier and the Matrix ID is explained
in more details in the section
[Decentralized identifier and Matrix ID](#decentralized-identifier-and-matrix-id).

Note that decentralized identifier and infrastructue are actively being piloted and
used by enterprises and governments. The following are some active specs being worked
on:

- [ChainAgnostic/CAIPs/caip-10](https://github.com/ChainAgnostic/CAIPs/blob/master/CAIPs/caip-10.md)
- [W3C Decentralized Identifiers](https://www.w3.org/TR/did-core/)
- [W3C Decentralized Identifiers for public key hashes](https://github.com/w3c-ccg/did-pkh/blob/main/did-pkh-method-draft.md)

Enbling both features in Matrix would pave the way for our ecosystem to eventually
participate in some of these projects.

## New login type

The proposed new login type is:

```text
m.login.publickey
```

Under the framework of this new login type, a specific implementation can be supported,
such as Ethereum:

```text
m.login.publickey.ethereum
```

This convention refers to a set of implementation choices such as the signature and verification
algorithm, and the decentralized identifier
representation:

- signature and verification algorithm is [EIP-4361: Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361)

- decentralized identifier is [Chain Agnostic ID](https://github.com/ChainAgnostic/CAIPs/blob/master/CAIPs/caip-10.md).

## Decentralized identifier and Matrix ID

During the login or registration flow, the "input" from the client is the signature,
the signed message, and other authentication data.

The "output" response from the server is the `access_token`, `username`, etc. The
`username` is the Matrix user ID. This Matrix ID is also the decentralized
identifier.

The mapping from the input data to the output Matrix ID is as follows:

### Step 1

The client signs the login message according to the chosen public key login type.
The client then sends the signed message, its signature and other authentication
data to the server.

### Step 2

The server cryptographically verifies the signature of the authentication
message. The server must be able to get the public key, or derive the public address
from the signature.

The server then derives the decentralized identifier using the public
address and information in the signed message according to the decentralized
identifier specification.

### Step 3

Any characters in the identifier that is disallowed according to the
[Matrix user identifier](https://spec.matrix.org/v1.2/appendices/#user-identifiers)
must be escaped:

```text
Encode any remaining bytes outside the allowed character set, as well as =, as their
hexadecimal value, prefixed with =. For example, # becomes =23; á becomes =c3=a1.
```

At the end of the flow, the server should represent the Matrix ID as:

```go
LoginIdentifier{
  Type: "m.id.decentralizedid",
  User: "<decentralized identifier as localpart>",
 }
```

To illustrate a specific login type, here is the implementation for
`m.login.publickey.ethereum`:

### Step 1 (Ethereum)

The client signs a message according to the specification:
[EIP-4361: Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361). This
is the "input" to the login flow.

### Step 2 (Ethereum)

When the server receives the login request, it performs a serious of steps to
validate the login message, derive the user's identity from the signature, and
signed message. Then it maps the identity to a Matrix ID.

a) Verify the signature and signed message

The server verifies the signature according to
[EIP-191](https://eips.ethereum.org/EIPS/eip-191) (_personal_sign_ message).
It recovers the public address from the signature; it does not require
any blockchain look up. This is baked into the design of the
[Ethereum address](https://ethereum.org/en/developers/docs/accounts/).

The server also verifies the rest of the message according to
[EIP-4361: Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361).

b) Derive the user's decentralized identifier

The server derives the decentralized identifier according to
[CAIP-10](https://github.com/ChainAgnostic/CAIPs/blob/master/CAIPs/caip-10.md) in
the format:

`eip155:chain_id:account_address`

where

- `chain_id` comes from the signed
  message in [EIP-4361](https://eips.ethereum.org/EIPS/eip-4361).

- `account_address`
  is the Ethereum address recovered from the signature.

Example: `eip155:1:0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb`

#### Chain ID attestation

An important note about `chain_id`. When the user signs this message, the
user is attesting to the fact that he / she is logging in with the intention to
access resources on this specific blockchain network only.

The server, after signature and message integrity verifications, will trust this
attestation. It will derive a decentralized identifier according to the
[CAIP-10](https://github.com/ChainAgnostic/CAIPs/blob/master/CAIPs/caip-10.md)
specification.

Thus, the decentralized identifier represents a statement from the server that it
has verified the user's intention for this chain ID only, and for not any other
chain ID.

### Step 3 (Ethereum)

#### Decentralized Matrix ID (Ethereum)

[CAIP-10](https://github.com/ChainAgnostic/CAIPs/blob/master/CAIPs/caip-10.md)
decentralized identifier is in the format:

`eip155:chain_id:account_address`

According to the [Matrix ID grammar](https://spec.matrix.org/v1.2/appendices/#user-identifiers),
the character `:` is not allowed in the localpart. Replace the character with the
escape rules by changing `:` to `=3a`.

For example,

`eip155:1:0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb`

becomes

`eip155=3a1=3a0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb`.

On the server, this is represented as:

```go
LoginIdentifier{
  Type: "m.id.decentralizedid",
  User: "eip155=3a1=3a0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb",
 }
```

Using this identifier, a Matrix Appservice has enough information to bridge into
a decentralized infrastructure like the blockchain network for additional services.
In the above example, this user is on:

- Ethereum blockchain `eip155`
- chain_id `1` (mainnet)
- account address `0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb`.

The next sections describe details about the login and registration flows.

## Summary of the end-to-end login flow

These are the steps at a high-level:

1. Client asks the server what login flow it supports.

2. Server responds with its supported login flow and a session ID.

3. Client prepares the authentication data, and a text-friendly message for the user to sign.

4. The user signs the message with the private key.

5. Client sends a login request with the signed message, and other authentication data.

6. Server checks the signed message for authenticity, any data tampering, public address matches with the signed
   message, etc.

7. If the validation passes, the server issues a new access_token (along with other information). The user is now
   logged in.

## Login flow details

```text
           { User }                   { Matrix client }                                   { Matrix server }
     +------------------+           +------------------+                                +------------------+
              |                              |                                                    |
              |-----1. (clicks login)------->|                                                    |
              |                              |          User-Interactive Authentication API       |
              |                              |--------------------2. (/login {})----------------->|
              |                              |                                                    |
              |                              |<--3. ({session, m.login.publickey.someAlgo, ...})--|
              |                              |                                                    |
              |                              |---+                                                |
              |                              |   |  4. createMessageToSign(session, ...)          |
              |                              |<--+                                                |
              |                              |                                                    |
              |<----5. (message to sign)-----|                                                    |
              |                              |                                                    |
          +---|                              |                                                    |
6. (sign) |   |                              |                                                    |
          +-->|                              |                                                    |
              |                              |                                                    |
              |-----7. (signed message)----->|                                                    |
              |                              |                                                    |
              |                              |--------------8. (/login { auth })----------------->|
              |                              |                                                    |
              |                              |                                                    |---+
              |                              |                                                    |   | 9. (server
              |                              |                                                    |<--+    validation)
              |                              |                                                    |
              |                              |<------------10. ({ access_token, ...})-------------|
              |                              |                    user logged in                  |
              |                              |                                                    |
     +------------------+           +------------------+                                +------------------+
```

1. User initiates a login.
   [More ...](#user-initiates-the-login-flow)

2. Matrix client requests a new user-interactive login session.
   [More ...](#client-requests-new-user-interactive-session)

3. Matrix server responds with a list of supported login flows, including a new session ID.
   [More ...](#server-responds-with-supported-login-flow)

4. Matrix client creates a new message for the user to sign.
   [More ...](#client-creates-message-to-sign)

5. Matrix client presents the message to the user.
   [More ...](#client-presents-message-to-the-user-for-signing)

6. User signs the message with the private key.

7. Matrix client has the signature of the message.

8. Matrix client sends a login request with the authentication data (message,
   signature, etc) to the server.
   [More ...](#client-sends-login-request-with-authenciation-data)

9. Matrix server performs validation checks such as signature verification, any
   message tampering, existence of the account, etc.
   [More ...](#server-validates-authentication-data)

10. Matrix client receives an access_token, and other login information. User is logged in.

The following sections describe each step in more detail.

## User initiates the login flow

In order to support the new authentication type, the client will need additional tools.

First, the user is expected to install a client tool that is capable of signing a message cryptographically. In the
case of Ethereum, the user can install a crypto wallet like [MetaMask](https://metamask.io/) or use the
[Brave browser](https://brave.com/), which has a native wallet feature. These tools are familiar to the blockchain
community.

Next, a Matrix client (or a Matrix sdk) needs to be extended to integrate with the crypto tool. For Ethereum, these
crypto wallets can be accessed via the [JSON-RPC API](https://ethereum.org/en/developers/docs/apis/json-rpc/) for
services like message signing.

Thus, a user can initiate the new login flow if a crypto wallet is installed, and the user is using a Matrix client
that has support for wallet integration.

## Client requests new user interactive session

Refer to [User-interactive API](https://spec.matrix.org/v1.2/client-server-api/#user-interactive-api-in-the-rest-api).

Client sends a HTTP POST request to the server endpoint `/login` with no `auth` parameter. It should get back a
HTTP/1.1 401 Unauthorized response with a JSON body detailing the supported login flows, params, and a session ID. The
semantics of the JSON response body is explained in the next section.

## Server responds with supported login flow

Refer to [User-interactive API](https://spec.matrix.org/v1.2/client-server-api/#user-interactive-api-in-the-rest-api).

When the server receives a request at the endpoint `/login` with no `auth` parameter, it should respond with a
HTTP/1.1 401 Unauthorized with the following JSON body:

```json
{
  "flows": [
    {
      "stages": ["m.login.publickey.someAlgo"]
    }
  ],
  "params": {
    "m.login.publickey.someAlgo": {
      "...": "..."
    }
  },
  "session": "xxxxxx"
}
```

where

- `params."m.login.publickey.someAlgo"` -- speficies the public key choice. E.g. `"m.login.publickey.ethereum"`

- `session` -- the session ID which acts as a nonce to prevent replay attacks. It is generated and tracked by the
  server. It should be at least 8 alphanumeric characters. Client is expected to present the session ID in its following
  authentication request for the same session. Session ID is deleted once the login flow is completed.

This is the response for the `m.login.publickey.ethereum` type:

```json
{
  "flows": [
    {
      "stages": ["m.login.publickey.ethereum"]
    }
  ],
  "params": {
    "m.login.publickey.ethereum": {
      "version": 1,
      "chain_ids": [1],
      "nonce": "yyyyyyyy"
    }
  },
  "session": "xxxxxx"
}
```

where

- `params."m.login.publickey.ethereum"` -- the client should follow the signature
  algorithm in [EIP-4361: Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361).
  The spec also describes the message format to be shown to the user.

- `params."m.login.publickey.ethereum".version` -- the version of this spec that the server is willing to support. See
  [version number](#version-number).

- `params."m.login.publickey.ethereum".chain_ids` -- [blockchain network IDs](https://chainlist.org/) that the server
  will allow. Server is configured (via its configuration file) to allow login from a list of blockchain networks. For
  example, the server can have a production config that specifies chain ID `1` for the Ethereum mainnet; a development
  server can have a test config that specifies chain ID `4` for the Rinkeby test network. Server should reject login
  attempts for any chain IDs that is not listed in the params.

- `params."m.login.publickey.ethereum".nonce` - is the nonce value described in
  [EIP-4361: Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361)

## Client creates message to sign

Once the client has received the server's response, it prepares a message for the user
to sign. Each sign-in specification would have its own message-to-sign format, and
signature algorithm.

To better illustrate the sign-in flow, this section uses the specification for
[EIP-4361 Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361). Other
sign-in specifications should follow a similar pattern.

### Message for the user to sign (EIP-4361)

Refer to [EIP-4361](https://eips.ethereum.org/EIPS/eip-4361) for details. The
following message template is copied from the specification. Reproduced here to
explain different parts of the message:

```text
${domain} wants you to sign in with your Ethereum account:
${address}

${statement}

URI: ${uri}
Version: ${version}
Chain ID: ${chain-id}
Nonce: ${nonce}
...
```

where

- ${domain} -- is the home server domain. It is the
  [RFC 3986 authority](https://datatracker.ietf.org/doc/html/rfc3986#section-3)
  part of the URL. It must be the first words in the first line of the message.

- ${address} -- is the user's public address performing the signing. It must be
  on the second line of the message and end with "\n".

- ${statement} -- is a text-friendly description of what the user is signing. It
  `must begin with a "\n" and end with a "\n".

- ${uri} - is an RFC 3986 URI referring to the resource that is the subject of the
  signing.

- ${version} - is the current version of the message, which MUST be 1 for the current
  version of EIP-4361.

- ${chain-id} - is the EIP-155 Chain ID to which the login session is bound. See
  important note about [Chain ID attestation](#chain-id-attestation)

- ${nonce} - is a randomized alphanumeric string with at least 8 characters.
  The nonce comes from the server's initial response. Example
  `params."m.login.publickey.ethereum".nonce`: `"yyyyyyyy"` (see below)):

```json
{
  "flows": [
    {
      "stages": ["m.login.publickey.ethereum"]
    }
  ],
  "params": {
    "m.login.publickey.ethereum": {
      "...": "...",
      "nonce": "yyyyyyyy"
    }
  },
  "session": "xxxxxx"
}
```

- ... -- other fields defined in the specification.

This message is shown to the user. The user signs the message with the private key
to produce a signature. The message, the signature, and other authentication data
are then sent to the server to complete the login flow.

**_Note: EIP-4316 libraries are available in various programming languages. The
libraries implement functions like the message construction, as well as message
and signature verification. Visit <https://docs.login.xyz/>._**

## Client presents message to the user for signing

This part depends on the integration between the Matrix client and the chosen public/private key tool. For Ethereum,
signing requests can be made via the [JSON-RPC API](https://ethereum.org/en/developers/docs/apis/json-rpc/). Specific
parameters are:

```json
{
  "jsonrpc": "2.0",
  "id": "incremental number",
  "method": "personal_sign",
  "params": ["the message", "the address", ""]
}
```

This should work with MetaMask, the Brave browser, or any other blockchain key management tools that support Ethereum.
It should pop up the tools' UI. The user interacts with it to sign the message. The RPC function should return a
signature.

The signature, the message, the wallet address, and other authentication data are sent to the server in the next step
as the login data.

## Client sends login request with authentication data

Refer to [User-interactive API](https://spec.matrix.org/v1.2/client-server-api/#user-interactive-api-in-the-rest-api).

Client sends a HTTP POST message to the endpoint `/login` with an `auth` JSON body.

The general format should look like this:

```json
{
  "type": "m.login.publickey",
  "auth": {
    "type": "m.login.publickey.someAlgo",
    "address": "<decentralized identifier for someAlgo>",
    "session": "xxxxxx",
    "message": "...",
    "signature": "..."
  }
}
```

For Ethereum, the `auth` JSON should look like this:

```json
{
  "type": "m.login.publickey",
  "auth": {
    "type": "m.login.publickey.ethereum",
    "address": "<decentralized identifier>",
    "session": "xxxxxx",
    "message": "...",
    "signature": "..."
  }
}
```

where

- `address` - the decentralized identifier as defined in
  [Decentralized Matrix ID (Ethereum)](#decentralized-matrix-id-ethereum)

- `session` - the session ID in the initial session response from the server.
  Example `session`: `"xxxxxx"` (see below):

```json
{
  "flows": [
    {
      "stages": ["m.login.publickey.ethereum"]
    }
  ],
  "params": {
    "m.login.publickey.ethereum": {
      "...": "...",
      "nonce": "yyyyyyyy"
    }
  },
  "session": "xxxxxx"
}
```

- `message` and `signature` are the output from
  [Message for the user to sign](#message-for-the-user-to-sign-eip-4361) and
  [Client presents message to the user for signing](#client-presents-message-to-the-user-for-signing)

## Server validates authentication data

The server performs login validation when it receives a POST request at the endpoint `/login` with an `auth`
JSON body.

### General validation

Refer to [login auth request from the client](#client-sends-login-request-with-authenciation-data) for the JSON format.

- Checks `auth.session` (session ID) exists.

- Checks `auth.address` account exists.

- Verifies the signature `auth.signature` is from `auth.address`, and the message
  `auth.message` has not been tampered with. This step is different for each
  cryptographic signature type. See [Ethereum-specific validation](#ethereum-specific-validation).

- If all validation passes, the server adds a completed stage to the login flow,
  cleans up the session (by deleting the session ID), and sends back a HTTP OK response
  to the client like other authentication types:

  - access_token,
  - username, [(Decentralized identifier and Matrix ID)](#decentralized-identifier-and-matrix-id)
  - device_id,
  - etc

- If any of the validation step fails, delete the session ID and send a HTTP Unauthorized response to the client
  (or some appropriate error response).

### Ethereum-specific validation

In addition to the general validation, Ethereum has these type-specific validation:

1. Verify the signature using the EDSA recovery function.
2. Check that the chain ID is allowed by the server.
3. Check that the decentralized identifier matches `auth.address` in the login
   auth request.

**Signature verification** -- [Ethereum](http://gavwood.com/paper.pdf) uses the
SECP-256k1 curve as its signing algorithm. It also defines an EDSA recovery function.
The message signer's public address can be recovered from this function.

There are available EIP-4316 libraries for various programming languages that
message and signature verification. Visit <https://docs.login.xyz/>.

**Chain ID verification** -- Server is configured (via its configuration file)
to allow login from a list of blockchain networks. For example, the production
config allows chain ID `1` for the Ethereum mainnet; the test config allows chain
ID `4` for the Rinkeby test network.

Server should reject login attempts for a chain ID that are not listed in its
configurations. This avoids downstream problems for supporting servers (like
Application services) that need to resolve contracts on specific blockchain
networks.

**Decentralized identifier verification** -- derive the decentralized
identifier from the signature and the signed message
See [Decentralized Matrix ID (Ethereum)](#decentralized-matrix-id-ethereum).
The derived identifier should match the `auth.address` in the login auth request:

```json
{
  "type": "m.login.publickey",
  "auth": {
    "type": "m.login.publickey.ethereum",
    "address": "<decentralized identifier>",
    "...": "..."
  }
}
```

**Supported version check** -- see [version number](#version-number) for the expected behavior.

This concludes the login flow.

## End-to-end registration flow

Registers a new user account. It is similar to the login flow.

```text
           { User }                   { Matrix client }                                  { Matrix server }
     +------------------+           +------------------+                                +------------------+
              |                              |                                                    |
              |-----1. (clicks register)---->|                                                    |
              |                              |                   Client-server API                |
              |                              |------------------2. (/register {...})------------->|
              |                              |                                                    |
              |                              |<--3. ({session, m.login.publickey.someAlgo, ...})--|
              |                              |                                                    |
              |                              |---+                                                |
              |                              |   |  4. createMessageToSign(session, ...)          |
              |                              |<--+                                                |
              |                              |                                                    |
              |<----5. (message to sign)-----|                                                    |
              |                              |                                                    |
          +---|                              |                                                    |
6. (sign) |   |                              |                                                    |
          +-->|                              |                                                    |
              |                              |                                                    |
              |-----7. (signed message)----->|                                                    |
              |                              |                                                    |
              |                              |--------------8. (/register { auth })-------------->|
              |                              |                                                    |
              |                              |                                                    |---+
              |                              |                                                    |   | 9. (server
              |                              |                                                    |<--+    validation &
              |                              |                                                    |        registration)
              |                              |<-------------10. ({ access_token, ...})------------|
              |                              |              user registered & logged in           |
              |                              |                                                    |
     +------------------+           +------------------+                                +------------------+
```

1. User initiates a new registration.

2. Matrix client requests a new registration session.
   [More ...](#client-requests-new-registration-session)

3. Matrix server responds with a list of supported registration flows, including a new session ID.
   [More ...](#server-responds-with-supported-registration-flow)

4. Matrix client creates a new message for the user to sign.
   [More ...](#client-creates-message-to-sign)

5. Matrix client presents the message to the user.
   [More ...](#client-presents-message-to-the-user-for-signing)

6. User signs the message with the private key.

7. Matrix client has the signature of the message.

8. Matrix client sends a registration request with the authentication data (message, signature, etc) to the server.
   [More ...](#client-sends-registration-request-with-authentication-data)

9. Matrix server performs validation checks such as signature verification, any message tampering, existence of the
   account, etc. It creates the account if validation checks are successful.
   [More ...](#server-validates-authentication-data-and-registers-user)

10. Matrix client receives an access_token, and other login information. User is registered and logged in.

The following sections describe each step in more detail.

## Client requests new registration session

Refer to [Client-server API](https://spec.matrix.org/v1.2/client-server-api/#post_matrixclientv3register)

```json
{
  "username": "<decentralized identifier>",
  "auth": {
    "type": "m.login.publickey"
  }
}
```

where

- `auth.type` -- is the type of authentication. `m.login.publickey` indicates that the user wants to register a
  public key account.

- `username` -- is the user ID to register. This is the decentralized identifier.

## Server responds with supported registration flow

Refer to [Client-server API](https://spec.matrix.org/v1.2/client-server-api/#post_matrixclientv3register) in the
section 401 response.

```json
{
  "completed": ["m.login.publickey.newregistration"],
  "flows": [
    {
      "stages": ["m.login.publickey.someAlgo"]
    }
  ],
  "params": {
    "m.login.someAlgo": {
      "...": "..."
    }
  },
  "session": "xxxxxx"
}
```

where

- `completed: ["m.login.publickey.newregistration"]` -- a new registration
  session is started.

- `params."m.login.publickey.someAlgo"` -- specifies the public key choice. E.g. `m.login.public.ethereum`

- `session` -- the session ID is a nonce to prevent replay attacks. It is generated and tracked by the
  server. It should be at least 8 alphanumeric characters. Client is expected to present the session ID in its following
  registration request for the same session. Session ID is deleted once the registration flow is completed.

This is the response for the `m.login.publickey.ethereum` type:

```json
{
  "completed": ["m.login.publickey.newregistration"],
  "flows": [
    {
      "stages": ["m.login.publickey.ethereum"]
    }
  ],
  "params": {
    "m.login.publickey.ethereum": {
      "version": 1,
      "chain_ids": [1],
      "nonce": "yyyyyyyy"
    }
  },
  "session": "xxxxxx"
}
```

where

- `completed: ["m.login.publickey.newregistration"]` -- a new registration
  session is started.

- `params."m.login.publickey.ethereum"` -- This means that the client should use the
  [personal_sign](https://geth.ethereum.org/docs/rpc/ns-personal#personal_sign) method to sign the message and its
  account address.

- `params."m.login.publickey.ethereum".version` -- the version of this spec that the server is willing to support.
  See [version number](#version-number).

- `params."m.login.publickey.ethereum".chain_ids` -- [blockchain network IDs](https://chainlist.org/) that the server
  will allow. Server is configured (via its configuration file) to allow login from a list of blockchain networks. For
  example, the production config allows chain ID `1` for the Ethereum mainnet; the test config allows chain ID `4`
  for the Rinkeby test network. Server should reject login attempts for any chain IDs that are not listed in the params.

## Client sends registration request with authentication data

Refer to [Client-server API](https://spec.matrix.org/v1.2/client-server-api/#post_matrixclientv3register).

Client sends a HTTP POST message to the endpoint `/register` with a `username` and an `auth` JSON body.

```json
{
  "username": "<decentralized identifier for someAlgo>",
  "auth": {
    "type": "m.login.publickey",
    "session": "xxxxxx",
    "public_key_response": {
      "type": "m.login.publickey.someAlgo",
      "...": "..."
    }
}
```

For Ethereum, the JSON should look like this:

```json
{
  "username": "<decentralized identifier>",
  "auth": {
    "type": "m.login.publickey",
    "session": "xxxxxx",
    "public_key_response": {
      "type": "m.login.publickey.ethereum",
      "address": "<decentralized identifier>",
      "session": "xxxxxx",
      "message": "...",
      "signature": "..."
    }
  }
}
```

The JSON content of `public_key_response` is the same as the
[client login request](#client-sends-login-request-with-authentication-data).

## Server validates authentication data and registers user

Refer to the [JSON body](#client-sends-registration-request-with-authentication-data) that the client sent.

The validation steps are:

- Get the `response` from the JSON body.

- [Validate the response](#server-validates-authentication-data). This is the same validation as the login flow.

- If validation is successful, complete the registration stage. Create the account, and send a HTTP OK response to the
  client with the access_token, username, device_id, etc.

- If any of the validation steps fails, delete the session ID and send a HTTP error response to the client.

This concludes the registration flow.

## Alternatives

Our first attempt at supporting public key login was to implement it as an SSO
flow. A lot of code was written to handle the basics of the flow such as
processing various options a client might send, handling possible error
states, and ensuring enough data validation is done to thwart attackers.

In a typical SSO scenario where the identity server holds the secret hash, this
makes sense because a Matrix server has no means to prove that the user
possesses the secret key. It has to redirect the user to the identity server
for authentication.

In public key cryptography, by design, no server holds the private key. Verifying
if a user possesses the private key is straight forward. It is usually done by
verifying the signature of a message with the public key. Any server can easily
perform the function.

We concluded that there is no advantage to implement an SSO flow
for public key cryptography. In fact, if the Matrix server does this directly, the
complexity of an SSO flow is unnecessary.

Public key cryptography also opens up the possibility of a decentralized
authentication system. If such a system were available, a client can authenticate
with any server that supports it. The client does not need to authenticate with
a specific home server, or be redirected to some centralized identity service.

## Security Considerations

### Mitigations against hijacking user identifier

Using decentralized identifier as the user identifier has a potential security issue
--- account hijacking.

A new user can pick any username during account registration as long as it is still available.
This is allowed for other authentication types (like password authentication).
It is possible that a malicious user fills in someone else's decentralized identifier
as the username during registration. Doing this effectively hijacks the account.
It prevents the user with the actual public / private key from registering and logging in.

The following are suggested mitigations:

- Give the admin the consfiguration option to turn off other authentication types
  (such as password authentication). Configure the server to allow only public key
  login and registration.

- A user has to prove that he / she has the private key during account registration.
  See [End-to-end registration flow](#end-to-end-registration-flow).

- At the end of the registration flow, server should generate a random password,
  save the hash in the account database, and discard the password. This prevents
  any misconfiguration that may allow username + password login from happening.

### Private key security

Keeping private keys safe is out-of-scope. Besides software wallet protections,
there are hardware wallet solutions which offer offline key storage.

There is an open issue with compromised private keys. This proposal does not
address the problem. There is no "password reset" solution. A separate proposal
is needed to address compromised keys.

### Version number

Versioning gives the server a means to inform the client which version of this
spec it must comply with. This is done as part of the initial login flow. See
[Client requests new user interactive session](#client-requests-new-user-interactive-session) and
[Server responds with supported login flow](#server-responds-with-supported-login-flow).
Within the server's response, it has a params `version` number.

The semantics of the `version` is as follows:

Version number is incremented when there is breaking spec change that is not backward compatibility.

For a supported version n, the server should be able to handle all minor revisions.

A server that supports version n+1 should still handle version n. But it does not have to handle version n-1. It is
the server's sole discretion to handle versions lower than n. The client has no power to lower the supported version.

This gives the server the ability to raise the bar when it needs to elevate its security requirements.

This spec is version 1.

## References

- [EIP-4361: Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361)

- [Ethereum address](https://ethereum.org/en/developers/docs/accounts/)

- [JSON-RPC API](https://ethereum.org/en/developers/docs/apis/json-rpc/)

- [Ethereum personal_sign and personal_ecRecover](https://geth.ethereum.org/docs/rpc/ns-personal#personal_sign)

- [ETHEREUM: A SECURE DECENTRALISED GENERALISED TRANSACTION LEDGER](http://gavwood.com/paper.pdf)

- [github ethereum/go-ethereum](https://github.com/ethereum/go-ethereum)

- [ChainAgnostic/CAIPs/caip-10](https://github.com/ChainAgnostic/CAIPs/blob/master/CAIPs/caip-10.md); or

- [W3C Decentralized Identifiers for public key hashes](https://github.com/w3c-ccg/did-pkh/blob/main/did-pkh-method-draft.md)

- [W3C Decentralized Identifiers](https://www.w3.org/TR/did-core/)
