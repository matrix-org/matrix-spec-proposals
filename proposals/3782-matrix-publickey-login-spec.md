# MSC3782: Add public/private key login as a new authentication type

Cryptographic signatures have played a pivotal role in blockchain. They are used to prove ownership of a public address
without exposing its private key. This property can be (and has been) used for decentralized authentication. A server
can use signature verification to prove that the user has possession of the private key to allow the user with that
public address to log in.

The proposal is to add a new login type for public key cryptography. Under this new login type, a specific
implementation can be supported, such as Ethereum and its signature algorithm - the Elliptic Curve Digital Signature
Algorithm (ECDSA).

This new login type would allow a Matrix server to authenticate a user without having to keep the user's secrets or
redirect the user to a central identity service.

## Proposal

New authentication type:

```text
m.login.publickey
```

The public address is the localpart of a user ID. It has the new type `m.id.publickey`.
Its username value is the public key, or a public address that is derived from the
private key. A user has to prove that he / she has the private key for this public
key or address. This is done by signing a specially designed message that is then
validated by the server during the login or registration flow.

```go
LoginIdentifier{
  Type: "m.id.publickey",
  User: "<public key or address as localpart>",
 }
```

Future proposals can map the user identifier to other identities such as
[MSC2787: Portable Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/2787).

Also, see additional notes on [Public key identifier](#public-key-identifier).

The next sections describe details of the login and registration flows.

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

1. User initiates a login. [More ...](#user-initiates-the-login-flow)

2. Matrix client requests a new user-interactive login session.
   [More ...](#client-requests-new-user-interactive-session)

3. Matrix server responds with a list of supported login flows, including a new session ID. [More ...](#server-responds-with-supported-login-flow)

4. Matrix client creates a new message for the user to sign. [More ...](#client-creates-message-to-sign)

5. Matrix client presents the message to the user. [More ...](#client-presents-message-to-the-user-for-signing)

6. User signs the message with the private key.

7. Matrix client has the signature of the message.

8. Matrix client sends a login request with the authentication data (message, signature, etc) to the server. [More ...](#client-sends-login-request-with-authenciation-data)

9. Matrix server performs validation checks such as signature verification, any message tampering, existence of the
   account, etc. [More ...](#server-validates-authentication-data)

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
services such as message signing.

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

- params."m.login.publickey.someAlgo" -- speficies the public key choice. E.g. `m.login.publickey.ethereum`

- "session" -- the session ID which acts as a nonce to prevent replay attacks. It is generated and tracked by the
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
      "chain_ids": ["1"]
    }
  },
  "session": "xxxxxx"
}
```

where

- params."m.login.publickey.ethereum" -- This means that the client should use the
  [personal_sign](https://geth.ethereum.org/docs/rpc/ns-personal#personal_sign) method to sign the message and its public
  address.

- params."m.login.publickey.ethereum".version -- the version of this spec that the server is willing to support. See
  [version number](#version-number).

- params."m.login.publickey.ethereum".chain_ids -- [blockchain network IDs](https://chainlist.org/) that the server
  will allow. Server is configured (via its configuration file) to allow login from a list of blockchain networks. For
  example, the server can have a production config that specifies chain ID 1 for the Ethereum mainnet; a development
  server can have a test config that specifies chain ID 4 for the rinkeby test network. Server should reject login
  attempts for any chain IDs that is not listed in the params.

## Client creates message to sign

Once the client has received the server's response, it prepares the authentication data as follows:

1. Create a JSON representation of the authentication data. This is meant for the server to process.

2. Create a text-friendly message for the user to sign. This representation is for the user to read, and so it needs to
   allow spaces, line-breaks, etc. to make it readable.

### JSON authentication data (general)

```json
{
  "domain": "home server domain",
  "address": "public address",
  "nonce": "session ID",
  "...": "..."
}
```

where

- domain -- is the home server domain. It is the
  [RFC 3986 authority](https://datatracker.ietf.org/doc/html/rfc3986#section-3)

- address -- is the public address of the user account

- nonce -- is the session ID from the server's response

### JSON authentication data (Ethereum)

Client prepares the following JSON data (aka `hashFields`):

```json
{
  "domain": "home server domain",
  "address": "Ethereum address. 0x...",
  "nonce": "session ID",
  "version": 1,
  "chainId": "blockchain network ID",
  "...": "..."
}
```

where

- domain -- is the home server domain. It is the
  [RFC 3986 authority](https://datatracker.ietf.org/doc/html/rfc3986#section-3) part of the URL.

- address -- is the
  [Externally-owned account (aka Ethereum address)](https://ethereum.org/en/developers/docs/accounts/). Address should
  start with "0x".

- nonce -- is the session ID from the server's response.

- version -- is the version the client is conforming to. MUST be 1 for this current specification.

- chainId -- is the EIP-155 Chain ID where any blockchain contract addresses must be resolved (as needed).

- "..." -- any other properties for the app. Ignored by the server.

Implementer's notes:
From the server's response, the client app should check the `chain_ids` list to make sure that the user has
selected the correct blockchain network. This gives the client a chance to show some UI to the user to switch to the
right network if needed.

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
      "chain_ids": ["1"]
    }
  },
  "session": "xxxxxx"
}
```

### Create a hash value from the JSON authentication data

The text message that the user signs is intended to be readable. It will have long sentences, paragraphs, line-breaks,
and so on. Not an optimal format for the server to process.

A JSON representation of the authentication data is much easier for the server to process. To make sure that the JSON
data is not tampered with, it needs to be covered by the message signature. i.e. when the user sees the message, some
representation of this JSON must be in the message that is signed. The server can then cryptographically check that it
has not been tampered with.

To do this, the JSON authentication data is converted into a hash value, and is then included in the message. The
conversion algorithm is as follows:

1. Convert the authentication data into a JSON string value. For example, in JavaScript, use the `JSON.stringify`
   function.

2. Apply Keccak256 function to the string value.

3. Base64-encode the hash value.

This base64-encoded value is the **Hash** value in the [message for the user to sign](#message-for-the-user-to-sign).

### Message for the user to sign

The message template is a simplified version of [EIP-4361](https://eips.ethereum.org/EIPS/eip-4361). The prescriptive
nature of the format is intended for regular expression extraction during server validation.

This message is shown to the user. The user signs the message with the private key to produce a signature. The message,
the signature, and other authentication data are then sent to the server to complete the login flow.

```text
${domain} wants you to sign in with your account:
${address}

${statement}

Hash: ${hash}
...
```

where

- ${domain} -- is the home server domain. It is the
  [RFC 3986 authority](https://datatracker.ietf.org/doc/html/rfc3986#section-3) part of the URL. It must be the first
  words in the first line of the message.

- ${address} -- is the user's public address performing the signing. It must be on the second line of the message and
  end with "\n".

- ${statement} -- is a text-friendly description of what the user is signing. It must begin with a "\n" and end with
  a "\n".

- ${hash} -- is the hash of the JSON authentication data. It must begin with a "\n" and end with a "\n". There should
  only be one and only one "\nHash: xxxx\n" string in the entire message.

- ... -- any other text content per application requirements. Ignored by the server.

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

For Ethereum, the `auth` JSON should look like this:

```json
{
  "type": "m.login.publickey",
  "auth": {
    "type": "m.login.publickey.ethereum",
    "address": "string",
    "session": "session ID",
    "message": "...",
    "signature": "...",
    "hashFields": {
      "...": "..."
    }
  }
}
```

where

- hashFields -- are the [JSON fields that were hashed](#json-authentication-data-ethereum).

## Server validates authentication data

The server performs login validation when it receives a POST request at the endpoint `/login` with an `auth`
JSON body.

### General validation

Refer to [login auth request from the client](#client-sends-login-request-with-authenciation-data) for the JSON format.

- Checks `auth.session` (session ID) exists.

- Checks `auth.address` account exists.

- Verifies the signature `auth.signature` is from `auth.address`, and the message `auth.message` has not
  been tampered with. This step is different for each cryptographic signature type. See [Ethereum-specific validation](#ethereum-specific-validation).

- Extract required information from the [message signed by the user](#message-for-the-user-to-sign):

  - ${domain} -- who is it addressed to?
  - ${address} -- who is it from?
  - ${hash} -- hash value of the JSON auth data. [More...](#create-a-hash-value-from-the-json-authentication-data)

- Verify that the HASH of the authentication data is legitimate:

  - Get the `auth.hashFields` as raw string.
  - Apply Keccak256 function to the byte values.
  - Base64-encode the hash value.
  - Compare the computed value with the Hash value extracted from the message. They should be the same.

- If the hash is verified, it means that the `auth.hashField` has not been tampered with. `auth.hashFields`
  string can now be converted to JSON. The rest of the validation can use the JSON directly. This JSON object will be
  referred to as `authData`.

- Verify that the message (signed by the user) is consistent with both the JSON `authData`, and the server's
  expectation:

| Signed message |     | `authData`       |     | Server's expectation |
| -------------- | --- | ---------------- | --- | -------------------- |
| ${domain}      | ==  | authData.domain  | ==  | home server name     |
| ${address}     | ==  | authData.address | ==  | `auth.address`       |
|                |     | authData.nonce   | ==  | session ID           |

- If all validation passes, the server completes the login flow, cleans up the session (by deleting the session ID),
  and sends back a HTTP OK response to the client like other authentication types:

  - access_token,
  - username, [(additional notes about the localpart)](#public-key-identifier)
  - device_id,
  - etc

- If any of the validation step fails, delete the session ID and send a HTTP Unauthorized response to the client
  (or some appropriate error response).

This completes the login flow.

### Ethereum-specific validation

In addition to the general validation, Ethereum has these type-specific validation:

1. Signature verification using the EDSA recovery function
2. Check the chain ID
3. Check the version number for spec compliance

**Signature verification** --
[Ethereum](http://gavwood.com/paper.pdf) uses the SECP-256k1 curve as its signing algorithm. It also defines an EDSA
recovery function. The message signer's public address can be recovered from this function.

Implementer's notes:
There is no need to implement the verification and recovery function from scratch. There are a number of Open Source
libraries that implement them, like [github ethereum/go-ethereum](https://github.com/ethereum/go-ethereum). Not all of
them work seamlessly. For the recovery function, double check that:

v = "recover id" is offset by -27 per the [Ethereum](http://gavwood.com/paper.pdf) spec.

**public address** -- after recovering the public key from the signature, derive its public address from the recovered
key. You can use one of the Open Source libraries to do that. Compare the message signer's public address with the
login address (who is attempting to login). It should match.

**chain ID** -- Server is configured (via its configuration file) to allow login from a list of blockchain networks.
For example, the production config allows chain ID 1 for the Ethereum mainnet; the test config allows chain ID 4 for
the rinkeby test network.

Server should reject login attempts for a chain ID that are not listed in its configurations. This avoids downstream
problems for supporting servers (like Application services) that need to resolve contracts on specific blockchain
networks.

**version** -- see [version number](#version-number) for the expected behavior.

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
              |                              |<----------10. ({ access_token, ...})------------|
              |                              |           user registered & logged in           |
              |                              |                                                 |
     +------------------+           +------------------+                             +------------------+
```

1. User initiates a new registration.

2. Matrix client requests a new registration session. [More ...](#client-requests-new-registration-session)

3. Matrix server responds with a list of supported registration flows, including a new session ID. [More ...](#server-responds-with-supported-registration-flow)

4. Matrix client creates a new message for the user to sign. [More ...](#client-creates-message-to-sign)

5. Matrix client presents the message to the user. [More ...](#client-presents-message-to-the-user-for-signing)

6. User signs the message with the private key.

7. Matrix client has the signature of the message.

8. Matrix client sends a registration request with the authentication data (message, signature, etc) to the server.
   [More ...](#client-sends-registration-request-with-authentication-data)

9. Matrix server performs validation checks such as signature verification, any message tampering, existence of the
   account, etc. [More ...](#server-validates-authentication-data-and-registers-user). It creates the account if
   validation checks are successful.

10. Matrix client receives an access_token, and other login information. User is registered and logged in.

The following sections describe each step in more detail.

## Client requests new registration session

Refer to [Client-server API](https://spec.matrix.org/v1.2/client-server-api/#post_matrixclientv3register)

```json
{
  "username": "string",
  "auth": {
    "type": "m.login.publickey"
  }
}
```

where

- auth.type -- is the type of authentication. `m.login.publickey` indicates that the user wants to register a
  public key account.

- username -- is the user ID to register. For Ethereum, this is the public address that starts with "0x".

## Server responds with supported registration flow

Refer to [Client-server API](https://spec.matrix.org/v1.2/client-server-api/#post_matrixclientv3register) in the
section 401 response.

```json
{
  "completed": [],
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

- params."m.login.publickey.someAlgo" -- specifies the public key choice. E.g. `m.login.public.ethereum`

- "session" -- the session ID which acts as a nonce to prevent replay attacks. It is generated and tracked by the
  server. It should be at least 8 alphanumeric characters. Client is expected to present the session ID in its following
  registration request for the same session. Session ID is deleted once the registration flow is completed.

This is the response for the `m.login.publickey.ethereum` type:

```json
{
  "completed": [],
  "flows": [
    {
      "stages": ["m.login.publickey.ethereum"]
    }
  ],
  "params": {
    "m.login.publickey.ethereum": {
      "version": 1,
      "chain_ids": ["1"]
    }
  },
  "session": "xxxxxx"
}
```

where

- params."m.login.publickey.ethereum" -- This means that the client should use the
  [personal_sign](https://geth.ethereum.org/docs/rpc/ns-personal#personal_sign) method to sign the message and its
  account address.

- params."m.login.publickey.ethereum".version -- the version of this spec that the server is willing to support.
  See [version number](#version-number).

- params."m.login.publickey.ethereum".chain_ids -- [blockchain network IDs](https://chainlist.org/) that the server
  will allow. Server is configured (via its configuration file) to allow login from a list of blockchain networks. For
  example, the production config allows chain ID 1 for the Ethereum mainnet; the test config allows chain ID 4 for the
  rinkeby test network. Server should reject login attempts for any chain IDs that are not listed in the params.

## Client sends registration request with authentication data

Refer to [Client-server API](https://spec.matrix.org/v1.2/client-server-api/#post_matrixclientv3register).

Client sends a HTTP POST message to the endpoint `/register` with a `username` and an `auth` JSON body.

```json
{
  "username": "string",
  "auth": {
    "type": "m.login.publickey",
    "session": "session ID",
    "public_key_response": {
      "...": "..."
    }
}
```

For Ethereum, the JSON should look like this:

```json
{
  "username": "0x...",
  "auth": {
    "type": "m.login.publickey",
    "session": "sessionId",
    "public_key_response": {
      "type": "m.login.publickey.ethereum",
      "address": "0x...",
      "session": "session ID",
      "message": "...",
      "signature": "...",
      "hashFields": {
        "...": "..."
      }
    }
  }
}
```

where

- hashFields -- are the [JSON fields that were hashed](#json-authentication-data-ethereum).

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

### Public key identifier

At the end of the login or registration flow, the server sends back a response with the access_token, username,
and other logged in data.

With respect to the username, the public address is the localpart of a user ID.
It has the new type `m.id.publickey`.

```go
LoginIdentifier{
  Type: "m.id.user",
  User: "<public key or address as localpart>",
 }
```

Note that using the public key / address as the user identifier has a potential security issue ---
account hijacking.

A new user can pick any username during account registration as long as it is still available.
It is possible that a malicious user fills in someone else's public key / address as the username during registration.
This is allowed for other types of authentication (such as password authentication). Doing this effectively hijacks
the account. It prevents the user with the actual public / private key from registering and logging in.

The following are suggested mitigations:

- Give the admin the consfiguration option to turn off other authentication types (such as password authentication).
  Configure the server to allow only public key login and registration.

- A user has to prove that he / she has the private key during account registration.
  See [End-to-end registration flow](#end-to-end-registration-flow).

- At the end of the registration flow, server should generate a random password, save the hash
  in the account database, and discard the password. This prevents any misconfiguration that may allow
  username + password login from happening.

### Private key security

Keeping private keys safe is out-of-scope for Matrix. Besides software wallet protections, there are hardware wallet
solutions which offer offline key storage.

There is an open issue with compromised private keys. This proposal does not address the problem. There is no "password
reset" solution. Needs a separate proposal to address compromised keys.

### Version number

Versioning gives the server a means to inform the client which version of this spec it must comply with. This is done
as part of the initial login flow. See
[Client requests new user interactive session](#client-requests-new-user-interactive-session) and
[Server responds with supported login flow](#server-responds-with-supported-login-flow). Within the server's response,
it has a params `version` number.

The semantics of the `version` is as follows:

Version number is incremented when there is breaking spec change that is not backward compatibility.

For a supported version n, the server should be able to handle all minor revisions.

A server that supports version n+1 should still handle version n. But it does not have to handle version n-1. It is
the server's sole discretion to handle versions lower than n. The client has no power to lower the supported version.

This gives the server the ability to raise the bar when it needs to elevate its security requirements.

This spec is version 1.

## References

- [Ethereum address](https://ethereum.org/en/developers/docs/accounts/)

- [JSON-RPC API](https://ethereum.org/en/developers/docs/apis/json-rpc/)

- [Ethereum personal_sign and personal_ecRecover](https://geth.ethereum.org/docs/rpc/ns-personal#personal_sign)

- [ETHEREUM: A SECURE DECENTRALISED GENERALISED TRANSACTION LEDGER](http://gavwood.com/paper.pdf)

- [github ethereum/go-ethereum](https://github.com/ethereum/go-ethereum)
