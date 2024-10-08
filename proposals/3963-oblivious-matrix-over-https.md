# MSC3963: Oblivious Matrix over HTTPS

## Deanonymization Threat Modelling

Some aspects of the security of the Matrix protocol are built upon the assumption
that a user reasonably trusts the homeserver which they choose to use. Although
the existing scheme of peer-to-peer encrypted rooms via Megolm is sufficient for
ensuring the confidentiality and integrity of messages when a homeserver which
has access to a room's history is malicious or compromised, the metadata within
the unencrypted portions of events, combined with the user's device history and
potentially any connection logs stored by the homeserver, poses a nontrivial
threat of deanonymization by a resourceful adversary.

Metadata accessible to any homeserver which an encrypted room's history is
synced to includes:
 * Matrix IDs of users participating, or having participated in the room
 * Unique Olm/Megolm key associated with device (and user-friendly name of
   device, if added)
 * Timestamps of all events
 * Approximate size of plaintext

In addition, metadata also accessible to a user's own homeserver includes:
 * List of all rooms that the user participates in
 * Email address and phone number of the user (if added)
 * Connecting IP address and last seen times of all devices (if implemented)
 * Metadata of all incoming connections (if logged)

Of these, the data accessible only to the user's homeserver is of particular
interest. Anonymization of a user's origin on the internet, whether proxied or
not, is lacking and relies too much on trust placed on the homeserver. Should
the homeserver be ever compromised, or legally compelled to disclose data,
an adversary may be able to trivially correlate the physical identity of a user
with their activities on Matrix, even if the user uses encrypted rooms and
follows best practices to validate device sessions.

(Note that of course Matrix by design does not offer plausible deniability of
data within events themselves; this is implemented by an overlaying application
layer such as OTR if required.)

At the moment, the threat model of Matrix may consider this to be an acceptable
risk, as anonymity-aware users will take measures to hide their physical IP from
their homeserver anyways, such as through proxies or Tor. However, there are
several arguments which could be made against the sustainability of such a
status quo:
 * As a homeserver grows, traffic from popular proxies or Tor exit relays may be
   rate-limited, making authentication and registration more difficult.
 * Certain users may not have the technical knowledge to use these tools while
   following best practices for security. Bad security is worse than no security.
 * Configuring native Matrix clients to *safely* use a proxy or Tor can be
   difficult, be not supported at all, or in the worst case leak traffic through
   insecure channels, which only creates an illusion of security. As an example,
   currently on the native Element client for Windows, macOS, and Linux,
   configuring a SOCKS proxy via command-line argument may [silently fail](https://github.com/vector-im/element-web/issues/3320).
   * Due to this, most anonymous users may opt to use web-based Matrix clients
     exclusively. As verifying the integrity of web client mirrors is far more
     difficult compared to native source code, this can cause them to become
     central points of failure which mostly concerns anonymity-aware users!
 * Some users may live in locations where access to such tools is restricted or
   unavailable (internet censorship).
   * Some users may also require plausible deniability for their internet
     traffic being associated with anonymity services.
 * If users are forced to create their own solutions to anonymizing Matrix
   client traffic, the non-uniformity of such solutions presents additional
   potential vectors for fingerprinting. (For example, a malicious homeserver
   may prioritize analyzing traffic from Tor users, simply due to the fact that
   most of these users must have some reason to pay special attention to their
   privacy.)

Although it can be argued that it is not within the scope of the Matrix protocol
itself to implement measures to defeat such a theoretical adversary, the Matrix
protocol itself is placed in the best position to offer a solution to the
deanonymization problem. As the Matrix network grows, more and more attacks will
be directed at homeservers and Matrix users, so an ideal solution would offer
some level of "future-proofing" against costly leaks that might undermine the
confidence of the typical user in the reliability of Matrix for sensitive
applications.

### Theoretical Examples

 * Alice is a whistleblower. Through her work, she discovers evidence related to
   a major scandal in the local government, which she forwards through an
   encrypted Matrix room to another independent journalist Bob to be published.
   Here, Alice used an identity on Homeserver A to send it to Bob, who has an
   identity on Homeserver B. The authorities obtains a search warrant for the
   organization operating Homeserver B that Bob uses, which through event
   metadata reveals that an account which ostensibly belongs to Alice sent a
   large attachment to Bob some time before Bob had published his article
   relating to the evidence provided by Alice. Through a second search warrant
   to Homeserver A which the account resides on, the IP addresses associated to
   Alice's devices are revealed, and Alice is prosecuted despite following best
   practices for security on Matrix.
   * Alice may have avoided deanonymization by utilizing a proxy or Tor when
     connecting to Homeserver A at all times. However, this may have been
     impractical for reasons highlighted earlier. Additionally, Alice may not
     have been aware that her homeserver did not protect or encrypt her physical
     identity, or was misled by an idea that all activities were encrypted and
     thus protected when messaging with Matrix.

 * Carol is an online activist. Some comments they've made online has attracted
   threats from certain hate groups on the internet, so they maintain a
   pseudonymous identity online, while using a Matrix identity on Homeserver A
   for instant messaging. Later on, a data leak occurs at Homeserver A,
   resulting in all plaintext data stored on Homeserver A being dumped and made
   publicly available. A member of a hate group then uses the leaked data to
   trace an IP address back to Carol through device sessions and doxxes them.
   * Carol may also have avoided deanonymization by utilizing a proxy or Tor,
     but the same considerations from before also apply. This case also differs
     in that Carol was the target of an implicitly illegal activity, but one
     which is usually difficult to prosecute due to criminals hiding their own
     identities online.

In both cases, responsibility of protecting user anonymity is upheld purely by
the integrity of the user's homeserver. Although, again, protection against such
threats may not be within scope for the Matrix protocol in general as of yet, it
is still a significant aspect for any anonymity-minded users to consider, and
mitigation solutions offered by the Matrix protocol itself allows less
tech-savvy users to take confidence in knowing that their anonymity can also be
protected when using Matrix.

## Proposal

**Oblivious MoH** (Matrix over HTTPS, or OMoH) is inspired by Oblivious DoH
(DNS over HTTPS, see also [RFC9230](https://www.rfc-editor.org/rfc/rfc9230)).

Oblivious MoH creates a first layer of protection for anonymity-minded users, by
relaying their Matrix traffic through a secondary homeserver first, thus never
exposing both the user's physical IP address and the user's Matrix identity to a
single party at any given time.

Oblivious MoH is a relatively novel concept as it is integrated directly into an
instant messaging platform, as opposed to existing as network level software.
As the Matrix network expands and matures, it will begin to benefit immensely
from the decentralized and diverse nature of homeserver federation(s), allowing
users to route sensitive Matrix traffic through anonymous, ephemeral paths via
existing Matrix homeservers around the world directly from the client, with some
level of plausible deniability for using OMoH by default (see
[OMoH Threat Model](#oblivious-moh-threat-model)).

Integration of Oblivious MoH would in theory place Matrix far ahead of many
other competing instant messaging platforms with core privacy and security
focuses, such as Signal, Telegram, Whatsapp, XMPP etc., by also isolating the
user's physical identity from any trusted "central server" (the user's
homeserver in the case of Matrix). Matrix would uniquely become the first IM
protocol and ecosystem to support minimal configuration anonymity
*out-of-the-box*, while also supporting feature-rich instant messaging and
other application integrations.

Oblivious MoH is also optional for homeservers to implement and/or use.
Homeservers which are not OMoH-aware by default reject requests gracefully
(404). Furthermore, a homeserver can choose to only relay OMoH traffic, to only
accept incoming OMoH traffic (in addition to normal Matrix traffic), or both at
once. A relay also does not necessarily need to implement the Matrix protocol at
all, and can theoretically operate standalone.

More technically speaking, Oblivious MoH is an optional Module for the Matrix
protocol specification. It does not create a new custom data protocol, but
instead is implemented as new stateless HTTP APIs which makes it easy to
integrate into existing client and homeserver implementations:

 * `/.well-known/matrix/moh` (GET, Returns server MoH capabilities; extensible)
 * `/_matrix/client/v1/obliviousMoh/`
   * `/relay` (POST, Relay a Matrix request to another homeserver)
   * `/getCapabilities` (GET, Retrieves well-known MoH capabilities from another
     homeserver on the client's behalf, as well as TLS certificate info)
 * `/_matrix/server/v1/obliviousMoh/`
   * `/incoming` (POST, Receives a OMoH request from another homeserver)

Typical usage flow of Oblivious MoH:
1. A client has an identity on Homeserver A, but would like to connect through
   Homeserver B. It knows the domain name of both.
2. The client first needs to initialize OMoH by obtaining a trusted ephemeral
   public key from Homeserver A.
   * First, as a sanity check the client will query Homeserver B for its OMoH
     capabilities.
     `GET /.well-known/matrix/moh` -> `200 OK; application/json`
   * Verifying that Homeserver B declares support for both the `/relay` and
     `/getCapabilities` endpoint, the client requests Homeserver B to fetch OMoH
     capabilities from Homeserver A. The response is signed using the X.509 TLS
     certificate of Homeserver A.
     `GET /_matrix/client/v1/obliviousMoh/getCapabilities` ->
     `200 OK; application/json`
   * The client verifies that the cryptographic signature is valid, does match
     Homeserver A's domain, and is issued by a trusted Certificate Authority. It
     then caches the returned ephemeral public key.
3. The client initializes a OMoH request by encapsulating a regular Matrix API
   request inside a JSON container which details the nature of the HTTP request
   (method, headers, MIME, path). It encrypts this payload with AES, and
   attaches the randomly generated key and IV / nonce to the container. It is
   then encrypted a second time with RSA using Homeserver A's ephemeral public
   key, and forwarded to Homeserver B's OMoH relay endpoint as a blob. The
   client specifies Homeserver A's domain as the target homeserver in a HTTP
   header, "Target".
   `POST /_matrix/client/v1/obliviousMoh/relay;`
   `application/oblivious-moh-request`
   * Homeserver B now decides whether the request should be forwarded. It first
     checks a cached list of homeservers recently queried via `/getCapabilities`
     for a valid match, and failing that, queries the target homeserver directly
     for its `.well-known` MoH capabilities before proceeding. It will forward the
     request only if the target homeserver validly declares support for the
     `/incoming` endpoint; otherwise the request is dropped and a 502 Bad
     Gateway is returned.
   * Homeserver B relays the OMoH request to Homeserver A.
     `POST /_matrix/server/v1/obliviousMoh/incoming;`
     `application/oblivious-moh-request`
4. Homeserver A has now received an anonymous OMoH request and attempts to
   decrypt it using every ephemeral keypair it currently considers valid. If a
   valid OMoH header is detected, it will attempt to decrypt the payload using
   the specified key and nonce.It then validates that the plaintext content is
   indeed valid JSON, and converts the container back to a normal HTTP request.
   The request is then looped back to the destination API endpoint.
5. The endpoint returns a response to the request, which is then encapsulated
   inside a JSON container similar to before, and encrypted using the key and
   ciphersuite requested by the client. The homeserver returns the encrypted
   blob as a response to Homeserver B's OMoH request.
   `200 OK; application/oblivious-moh-request`
6. Homeserver B passes the response back to the client.
   `200 OK; application/oblivious-moh-request`
7. The client decrypts the blob using the key specified in the request, and
   converts the container back to a normal HTTP response, which is transparently
   returned to the function or program which initiated the request.

The OMoH endpoints are stateless throughout. One to two requests occur when a
client attempts OMoH connection to a homeserver domain which it does not have
a current ephemeral key for. Afterwards, all Matrix client requests are
translated transparently into OMoH requests, which makes a client using OMoH
functionally almost indistinguishable compared to a client using the relay
homeserver directly without Oblivious MoH.

```
|Alice              |                   |
|(a user)           |Homeserver B       |
|                   |(a relay HS)       |Homeserver A
|                   |                   |(Alice's actual HS, the "remote" HS)
|[Alice openes her  |                   |
| Matrix client, and|                   |
| chooses to enable |                   |
| Oblivious MoH.]   |                   |
|                   |                   |
|[Alice chooses     |                   |
| Homeserver B as   |                   |
| her OMoH relay.]  |                   |
|                   |                   |
|                   |                   |
|                   |                   |
|-HTTPS 1.1 GET---->|                   |
|/.well-known/matrix/moh                |
|                   |                   |
|<-----------200 OK-|                   |
|MIME application/json                  |
|{                                      |
|  "capabilities": {                    |
|    "specs": {                         |
|       "v1": {                         |
|        "oblivious_moh": {             |
|          "relay": true                |
|          "incoming": true             |
|          "getCapabilities": true      |
|        }                              |
|      }                                |
|    },                                 |
|    "base_url": "matrix.homeserver-..",|
|    "ephemeral_key": {                 |
|      "keys": {                        |
|        "MOH_RSA_AES...": "Ki0YT07cS.."|
|      },                               |
|      "expires": 2147483648            |
|    }                                  |
|  },                                   |
|  "signature": "xnO0EgRWzCB5ZQJGPSJ.." |
|}                                      |
|                   |                   |
|                   |                   |
|                   |                   |
|-HTTPS 1.1 GET---->|                   |
|/_matrix/client/v1/obliviousMoh/getCapabilities
|Target: matrix.homeserver-a.example    |
|                   |                   |
|                   |-HTTPS 1.1 GET---->|
|                   |/.well-known/matrix/moh
|                   |                   |
|                   |<-----------200 OK-|
|                   |MIME application/json
|                   |                   |
|<-----------200 OK-|                   |
|MIME application/json                  |
|{                                      |
|  "certificate": "LS0tLS1CRUdJTiBDR.." |
|  "capabilities": {                    |
|    "versions": {...},                 |
|    "base_url": "matrix.homeserver-..",|
|    "ephemeral_key": {...}             |
|  },                                   |
|  "signature": "+XvM68ws913g+E0FcsC.." |
|}                                      |
|                   |                   |
|                   |                   |
|                   |                   |
|[Matrix client     |[HS B can now cache|
| verifies through  | the capabilities  |
| signature that    | until key expiry] |
| the capabilities  |                   |
| are from HS A]    |                   |
|                   |                   |
|[Matrix client     |                   |
| generates request]|                   |
|                   |                   |
|                   |                   |
|                   |                   |
|-> GET             |                   |
|/_matrix/client/v3/sync                |
|MIME application/json                  |
|{                                      |
|  "since": "s72595_4483_1934",         |
|  "full_state": true                   |
|}                                      |
|      \/           |                   |
| Encode HTTP,      |                   |
| attach an         |                   |
| ephemeral nonce   |                   |
| for server        |                   |
| response          |                   |
|      \/                               |
|{                                      |
|  "path": "/_matrix/client/v3/sync",   |
|  "method": "GET",                     |
|  "response_nonce": "9C4d0GFwwtyyqt..",|
|  "headers": {                         |
|    "Authorization": "Bearer foo_12..",|
|    "Content-Type": "application/json" |
|  },                                   |
|  "payload": {                         |
|    "since": "s72595_4483_1934",       |
|    "full_state": true                 |
|  }                                    |
|}                                      |
|      \/           |                   |
| Encrypt with HS   |                   |
| A's TLS public key|                   |
|      \/           |                   |
|97e62d2f522112a0d1a|                   |
|5403b1a5b05cef570..|                   |
|      \/           |                   |
|<- Relay request   |                   |
|                   |                   |
|-HTTPS 1.1 POST--->|                   |
|/_matrix/client/v1/obliviousMoh/relay  |
|MIME application/oblivious-moh-request |
|Target: matrix.homeserver-a.example    |
|Nonce: hOCBvgGrWMSQj81OzGIukQ          |
|Scheme: MOH_RSA_AES256_GCM_SHA256      |
|97e62d2f522112a0d1a|                   |
|5403b1a5b05cef570..|                   |
|                   |                   |
|                   |-HTTPS 1.1 POST--->|
|                   |/_matrix/server/v1/obliviousMoh/incoming
|                   |MIME application/oblivious-moh-request
|                   |Nonce: hOCBvgGrWMSQj81OzGIukQ
|                   |Scheme: MOH_RSA_AES256_GCM_SHA256
|                   |97e62d2f522112a0d1a|
|                   |5403b1a5b05cef570..|
|                   |                   |
|                   |                   |-> Decrypt json via ephemeral key
|                   |                   |      \/
|                   |                   |{
|                   |                   |  "path": "/_matrix/client/v3/sync",
|                   |                   |  "method": "GET",
|                   |                   |  "response_nonce": "9C4d0GFwwtyyq...",
|                   |                   |  "headers": {                         
|                   |                   |    "Authorization": "Bearer foo_12..",
|                   |                   |    "Content-Type": "application/json"
|                   |                   |  },
|                   |                   |  "payload": {
|                   |                   |    "since": "s72595_4483_1934",
|                   |                   |    "full_state": true
|                   |                   |  }
|                   |                   |}
|                   |                   |      \/
|                   |                   |<- Forward to endpoint
|                   |                   |
|                   |                   |<- GET
|                   |                   |/_matrix/client/v3/sync
|                   |                   |MIME application/json
|                   |                   |
|                   |                   |[Endpoint processes request as normal]
|                   |                   |
|                   |                   |[Endpoint returns response]
|                   |                   |-> 200 OK
|                   |                   |MIME application/json
|                   |                   |
|                   |                   |-> Encrypt json using negotiated key
|                   |                   |      \/
|                   |                   |{
|                   |                   |  "status": 200,
|                   |                   |  "headers": {
|                   |                   |    "Content-Type": "application/json"
|                   |                   |  },
|                   |                   |  "payload": {
|                   |                   |    "account_data": {...},
|                   |                   |    "next_batch": {...},
|                   |                   |    "presence": {...},
|                   |                   |    "rooms": {...},
|                   |                   |    ...
|                   |                   |  }
|                   |                   |}
|                   |                   |      \/
|                   |                   |13d01e6a31b910f89c8
|                   |                   |08f771a0e9a4f6653be
|                   |                   |f3743b84107bd2817..
|                   |                   |      \/
|                   |                   |<- Relay response
|                   |                   |
|                   |<-----------200 OK-|
|                   |MIME application/oblivious-moh-request
|                   |Nonce: qxIX4kuOaWdv1IIr/4Yn/w
|                   |13d01e6a31b910f89c8|
|                   |08f771a0e9a4f6653be|
|                   |f3743b84107bd2817..|
|                   |[HS B now forgets  |
|                   | about Alice as    |
|                   | request succeeded]|
|                   |                   |
|<-----------200 OK-|                   |
|MIME application/oblivious-moh-request |
|Nonce: qxIX4kuOaWdv1IIr/4Yn/w          |
|13d01e6a31b910f89c8|                   |
|08f771a0e9a4f6653be|                   |
|f3743b84107bd2817..|                   |
|                   |                   |
|-> Decrypt json    |                   |
|      \/           |                   |
|{                                      |
|  "status": 200,                       |
|  "headers": {                         |
|    "Content-Type": "application/json" |  
|  },                                   |
|  "payload": {                         |
|    "account_data": {...},             |
|    "next_batch": {...},               |
|    "presence": {...},                 |
|    "rooms": {...},                    |
|    ...                                |
|  }                                    |
|}                                      |
|      \/           |                   |
| Translate back to |                   |
| HTTP for client   |                   |
| SDK usage         |                   |
|      \/           |                   |
|<- 200 OK          |                   |
|MIME application/json                  |
|{                                      |
|  "account_data": {...},               |
|  "next_batch": {...},                 |
|  "presence": {...},                   |
|  "rooms": {...},                      |
|  ...                                  |
|}                                      |
```

## Oblivious MoH Threat Model

Oblivious MoH is designed to:
 * Hinder deanonymization of the user, by avoiding a direct connection to the
   user's homeserver which would reveal their physical IP address;
 * Hinder adversaries from determining that the user is using Oblivious MoH;
 * Hinder adversaries from disrupting the user's ability to reach the greater
   Matrix federation network;
 * Hinder adversaries from abusing Oblivious MoH to attack other aspects of the
   threat model of the Matrix protocol;
 * Synergize with other anonymity solutions such as proxies or Tor, when
   properly implemented, for defense-in-depth.

Oblivious MoH is **NOT** designed to:
 * Directly protect VoIP traffic (yet);
 * Prevent adversaries from identifying that the user is using Matrix;
 * Prevent deanonymization of the user when the adversary controls both the
   relay and remote homeservers;
 * Prevent deanonymization of the user when the adversary can view and correlate
   events within publicly available rooms with the user's traffic;
 * Fully defend against deanonymization of the user when the adversary has the
   means to implement an effective, large scale timing attack;
 * Protect the user when a client which does not implement Oblivious MoH
   properly is used.

Oblivious MoH is designed to reasonably protect against:
 * Client adversaries (malicious Matrix users)
 * Network adversaries (malicious Matrix homeservers and OMoH relays)
 * Local adversaries (insecure networks, cybercriminals, ISPs)
 * Global adversaries (intelligence agencies and other state-level adversaries;)

Oblivious MoH cannot protect against adversaries which can compromise your
Matrix client. **It is possible, but not recommended to use Oblivious MoH with a**
**web Matrix client. Use a native, open-source client whenever possible.**

The Oblivious MoH threat model may partially change with future specifications.

## API Specification

### GET `/.well-known/matrix/moh`

Returns information about the local homeserver's Matrix over HTTPS capabilities.

 * 200 OK: The request succeeded, and a capabilities JSON is returned.
 * 404 Not Found: This homeserver does not implement Matrix over HTTPS.

#### 200 Response
| Name           | Type         | Description                                                          |
| -------------- | ------------ | -------------------------------------------------------------------- |
| `capabilities` | Capabilities | MoH capabilities of the server.                                      |
| `signature`    | string       | Cryptographic signature of `capabilities` object, encoded in base64. |

#### Capabilities
| Name            | Type           | Description                                                |
| --------------- | -------------- | ---------------------------------------------------------- |
| `specs`         | Specifications | The specs supported by the server.                         |
| `base_url`      | string         | Base URL to use for MoH endpoints.                         |
| `ephemeral_key` | Ephemeral Key  | Rotating ephemeral public key to be used for MoH requests. |

#### Specification (v1)
| Name            | Type              | Description                      |
| --------------- | ----------------- | -------------------------------- |
| `oblivious_moh` | OMoH Capabilities | OMoH capabilities of the server. |

#### OMoH Capabilities
| Name              | Type    | Description                                                                                    |
| ----------------- | ------- | ---------------------------------------------------------------------------------------------- |
| `relay`           | boolean | True if the server supports relaying OMoH requests.                                            |
| `incoming`        | boolean | True if the server supports receiving OMoH requests.                                           |
| `getCapabilities` | boolean | True if the server supports requesting this endpoint of another server on the client's behalf. |

#### Ephemeral Key
| Name            | Type    | Description                                                                  |
| --------------- | ------- | ---------------------------------------------------------------------------- |
| `keys`          | object  | Most current ephemeral public keys. See [Blob Encryption](#blob-encryption). |
| `expires`       | number  | Timestamp for when the current `keys` are no longer accepted by the server.  |

A client attempting to use Oblivious MoH **MUST** not continue if it does not
support any specifications which the server declares support for.

`signature` should be derived from the X.509 TLS certificate used by the
homeserver. A client attempting to use Oblivious MoH **MUST** not continue, and
discard the capabilities specified in the response, if the signature of the
`capabilities` object cannot be verified to match a valid TLS certificate
bearing the domain of the server.

A specification-compliant server which implements `relay` **MUST** also
implement `getCapabilities`.

When using a version string which ends in `-relay-only`, clients *should* not
attempt to use the server for any Matrix endpoints, other than the Oblivious MoH
endpoints. (A server probably should not also need to declare both a normal and
a relay spec version at the same time.)

The Specifications object can be adapted by any other specification which
implements Matrix over HTTPS.

The `/moh` endpoint **MUST** not implement HTTP caching, due to serving the
rotating ephemeral public key used by Matrix over HTTPS.

> Oblivious MoH uses a "versionless" `/.well-known/` endpoint to declare its
capabilities. This slightly reduces fingerprintable vectors of OMoH users, by
simulating an initial request to `/.well-known/matrix/client`, against potential
middlemen in the user's network connection.

```json
{
  "capabilities": {
    "specs": {
      "v1": {
        "oblivious_moh": {
          "relay": true,
          "incoming": true,
          "getCapabilities": true
        }
      },
      "v1-relay-only": {
        "oblivious_moh": {
          "relay": true,
          "incoming": false,
          "getCapabilities": true
        }
      },
      "msc3963": {
        "oblivious_moh": {
          "relay": true,
          "incoming": true,
          "getCapabilities": true
        },
        "experimental_parameter": "foo_bar"
      }
    },
    "base_url": "https://matrix-client.matrix.org",
    "ephemeral_key": {
      "keys":{
        "MOH_ED25519_AES256_GCM_SHA256": "Ki0YT07cS2myJzQnqLmY/4TU1/AK..."
      },
      "expires": 2147483648
    }
  },
  "signature": "TL2gUN7PP+PCixyDp0NLI7REUELZPvYC2tTIELsRcBylixd6HsHVfM1+1Vm..."
}
```


### POST `/_matrix/client/v1/obliviousMoh/relay`

Requests the server to forward an Oblivious MoH request to another homeserver.
Request body **MUST** be an encrypted blob of MIME Content-Type
`application/oblivious-moh-request`.

The HTTP request header "Target" is the domain name of the remote homeserver to
receive the request.

The HTTP request header "Nonce" is the cryptographic nonce associated with the
encrypted blob. This **MUST** be included in the `/incoming` request verbatim.

The HTTP response header "Nonce" is the cryptographic nonce associated with the
encrypted blob. This **MUST** be included in the `/incoming` response verbatim.

 * 200 OK: The request succeeded, and the encrypted blob from the remote
   homeserver is returned.
 * 404 Not Found: This server does not implement OMoH relaying.
 * 502 Bad Gateway: The remote homeserver does not implement OMoH receiving, or
   the remote homeserver returned an error. If the remote homeserver included a
   response, it is returned as the response body.
 * 504 Gateway Timeout: The remote homeserver did not respond in a timely manner.
 * 429 Too Many Requests: Rate-limited by either this server or the remote
   homeserver.

The plaintext of the encrypted blob should be well-formed JSON.

#### Plaintext
| Name              | Type   | Description                                                                                                              |
| ----------------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| `path`            | string | URL of the destination API endpoint.                                                                                     |
| `method`          | enum   | HTTP method of the request. One of ["GET", "POST", "PUT", "HEAD", "OPTIONS", "DELETE"].                                  |
| `response_nonce`  | string | One-time nonce which the remote homeserver should use in response encryption, encoded in base64.                         |
| `headers`         | object | HTTP headers associated with the request. Each JSON key corresponds to a header key. Includes "Content-Type" by default. |
| `payload`         | object | HTTP body associated with the request. Usually a JSON object, or a JSON key containing a base64 encoding of the payload. |

The `payload` object should be a simple JSON object representing the original
JSON request when the `Content-Type` header is `application/json`. For any other
`Content-Type`, `payload` will be an object which contains a key with its name
as the file name and value as the file data encoded in base64.

For specifications on how to encrypt the JSON container, see [Blob Encryption](#blob-encryption).

```json
{
  "path": "/_matrix/client/v3/sync",
  "method": "GET",
  "response_nonce": "qxIX4kuOaWdv1IIr/4Yn/w",
  "headers": {
    "Authorization": "Bearer foo_1234567890",
    "Content-Type": "application/json"
  },
  "payload": {
    "since": "s72595_4483_1934",
    "full_state": true
  }
}
```

### POST `/_matrix/server/v1/obliviousMoh/incoming`

Requests the server to accept an Oblivious MoH request from another homeserver.
Request and response body **MUST** be an encrypted blob of MIME Content-Type
`application/oblivious-moh-request`, unless the request fails in which case the
response may be `text/html` or `application/json`.

The HTTP request header "Nonce" is the cryptographic nonce associated with the
encrypted blob, randomly generated by the client.

 * 200 OK: The request succeeded, and the destination API endpoint's response as
   an encrypted blob is returned. Returned even if the requested API endpoint
   returns any errors, except for 429.
 * 404 Not Found: This server does not implement OMoH receiving.
 * 422 Unprocessable Entity: The server could not decode well-formed JSON from
   the request body, likely due to a cryptographic error.
 * 429 Too Many Requests: Rate-limited.

For request JSON specification, see [/relay](#post-_matrixclientv1obliviousmohrelay).

In this version of Oblivious MoH, homeservers **MUST** also reject any requests
destined for any OMoH relay endpoint via its `path` JSON key (e.g.
`/obliviousMoh/relay`), using 422 Unprocessable Entity, to avoid creating OMoH
routes with more than 1 relay.

For specifications on how to decrypt the JSON container, see [Blob Encryption](#blob-encryption).

#### 200 Response (Plaintext)
| Name      | Type   | Description                                                                                                              |
| --------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| `status`  | number | HTTP response code associated with the request.                                                                          |
| `headers` | object | HTTP headers associated with the request. Each JSON key corresponds to a header key. Includes "Content-Type" by default. |
| `payload` | object | HTTP body associated with the request. Usually a JSON object, or a JSON key containing a base64 encoding of the payload. |

```json
{
  "status": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "payload": {
    "account_data": {...},
    "next_batch": {...},
    "presence": {...},
    "rooms": {...}
  }
}
```

### GET `/_matrix/client/v1/obliviousMoh/getCapabilities`

Requests the server to fetch another server's `/.well-known/matrix/moh` on
behalf of the client, alongside the TLS certificate and public key it provides.
If the homeserver's base URL resides on a different domain, it attempts to fetch
`/.well-known/matrix/moh` from that base URL instead.

The HTTP request header "Target" is the domain name of the remote homeserver to
query.

 * 200 OK: The request succeeded, and the capabilities JSON of the remote
   homeserver is returned.
 * 404 Not Found: The server does not implement delegated OMoH capabilities
   fetching.
 * 502 Bad Gateway: The remote homeserver did not return a success code. If the
   remote homeserver included a response, it is returned as the response body.
   Usually this means that the remote homeserver does not implement MoH.
 * 508 Loop Detected: The remote homeserver's `base_url` resulted in a redirect
   chain which was too lengthy.

A client attempting to use Oblivious MoH **MUST** not continue if it does not
support any versions which the server declares support for.

A client attempting to use Oblivious MoH **MUST** not continue, and discard the
capabilities specified in the response, if the signature of the `capabilities`
object cannot be verified to match a valid TLS certificate bearing the domain of
the remote homeserver.

#### 200 Response
| Name            | Type          | Description                                                       |
| --------------- | ------------- | ----------------------------------------------------------------- |
| `certificate`   | string        | TLS certificate used by the remote homeserver, encoded in base64. |
| `capabilities`  | Capabilities  | Forwarded from the remote homeserver's JSON response.             |
| `signature`     | string        | Forwarded from the remote homeserver's JSON response.             |

```json
{
  "certificate": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tDQpNSUlGTWpDQ0JObWdBd...",
  "capabilities": {
    "specs": {
      "v1": {
        "oblivious_moh": {
          "relay": true,
          "incoming": true,
          "getCapabilities": true
        }
      }
    },
    "base_url": "https://matrix-client.matrix.org",
    "ephemeral_key": {
      "keys":{
        "MOH_ED25519_AES256_GCM_SHA256": "Ki0YT07cS2myJzQnqLmY/4TU1/AK"
      },
      "expires": 2147483648
    }
  },
  "signature": "+XvM68ws913g+E0FcsCNpWm1UZ2H0g7xjhobJQMa2GWyFN33NOuVRQyykwm..."
}
```

## Blob Encryption

Due to the risky nature of custom cryptography implementations, the following
draft should currently be treated as a recommendation rather than an actual
specification. Before the MSC is merged into the stable spec, it is **highly**
**recommended** for an independent audit to be conducted on the security of the
proposed encryption scheme.

The communication model of Oblivious MoH poses severe constraints on the design
of a secure encryption scheme between the user and the remote homeserver.
 * The scheme is (almost) stateless throughout. The user's client and remote
   homeserver only need to keep track of the intermediate public keys.
 * The scheme involves minimal exchange of traffic between the user and remote
   homeserver. Requests and responses are one-to-one and no additional
   negotiation can occur. This immediately rules out many key exchange schemes.
   * Existing schemes used within Matrix such as *Double Ratchet* (Olm) are thus
     unusable, especially considering that the client is always unauthenticated.
 * The client can obtain an intermediate trusted public key from the remote
   homeserver signed by its TLS certificate.

It may be beneficial to draw an analogy to PGP which operates off of a very
similar communication scheme (known public key, encrypt and forget), though in
this case the concept of a web of trust is ignored and trust within the remote
homeserver's Certificate Authority is assumed by default. Additionally, the
remote homeserver cannot obtain a public key of the *user* until they send their
first request, and even then the remote homeserver cannot retain it for future
communications as it is ephemeral.

It should also be noted that encryption of the JSON container is solely used for
defeating a network adversary of a malicious relay server. As the Oblivious MoH
requests happen fully over TLS, it is not expected for theoretical weaknesses
within this encryption scheme to affect client, local, and global adversaries
significantly.

In the interest of simplicity of implementation, the first version of Oblivious
MoH will only feature **Weak (eventual) Forward Secrecy**, due to the complex
nature of non-interactive forward secrecy. Certain novel techniques such as
puncturable encryption may be implemented in future versions of Oblivious MoH to
guarantee Perfect Forward Secrecy (see [Future Work & Extensions](#future-work-&-extensions)).

### Rotating Ephemeral Public Key

To achieve weak forward secrecy, a homeserver which implements the `/incoming`
endpoint issues rotating MoH public keys on a cycle. The remote homeserver
*should* only accept the current key, as well as one or two keys immediately
before it; any expired keypairs must be discarded as soon as possible. When
implemented correctly, an adversary which compromises the homeserver can only
decrypt past messages within a reasonably small time window. Messages which were
encrypted with keypairs which were already discarded should theoretically become
permanently undecryptable (until a plaintext recovery attack becomes feasible
against the ciphersuite used).

The most current ephemeral key is provided by the `keys` object from the
`/.well-known/matrix/moh` endpoint. Each JSON key bears the ciphersuite string
as its name, and the public key encoded in Base64 as its value:

```json
{
  "keys":{
    "MOH_ED25519_AES256_GCM_SHA256": "Ki0YT07cS2myJzQnqLmY/4TU1/AKXo0JdelIC...",
    "MOH_ECDSA_AES256_GCM_SHA256": "yC9TwIb7qkfXQK4UCMph381luV1VNhrXlu9FL5O...",
    "MOH_RSA_AES256_GCM_SHA256": "l3apK+KV4q0H6VyDWsLPhLWjcnMnMrjiWnUOtGbFi...",
    "MOH_SOME_OTHER_CIPHERSUITE": "a1ujSIEJPU79Z9+d33rrDRd7L123INk3q3o63B+u..."
  },
  "expires": 2147483648
}
```

`expires` is the Unix timestamp of the expiry time of the public keys, in
seconds since 00:00:00 UTC, January 1st, 1970.

Homeservers **MUST** be aware of at least 2 public keys per ciphersuite which
have not expired at any given time, and also not issue any more keys if there
are at least 4 valid keys already issued. Keys **MUST** expire at least 200
seconds and no more than 300 seconds after they are first issued, and this
duration **MUST** also be randomly determined at time of issue. A new key **MUST**
be issued 60 seconds before the oldest one expires, unless this would exceed the
limit of 3 keys. Expired private keys **MUST** be immediately purged by the
homeserver.

A client **MUST** request a new key via `/getCapabilities`, randomly between 100
to 50 seconds before the current one expires. If a client has more than 1 valid
key available, it **MUST** use the oldest one until 30 seconds before it
expires, when it should switch to the second oldest one. If a client receives a
422 Unprocessable Entity indicating a decryption failure, it should try a newer
key if it already has one available; otherwise, it should stop making requests
until the next public key fetch is scheduled.

> Although this may result in service interruption if the private keys on the
  remote homeserver update suddenly, adversarial control over the client's key
  usage and traffic patterns is hopefully minimized.

Servers **MUST** ensure that the time is synced at least to second-level
precision before issuing any keys. If the time on the server changes, the server
**MUST** immediately issue a new key (and invalidate the oldest one if this
would exceed the key limit). Clients *should* ensure that time is synced at
least to second-level precision before establishing an Oblivious MoH route, to
improve homogeneity between clients as keys rotate.

MSC3963 does not enforce using any particular cryptographic scheme, but the
following is a sample specification for a scheme
"`MOH_RSA_AES256_GCM_SHA256`".

(**To reiterate with emphasis**, this sample implementation is a draft and may
not yet follow all best security practices. Ensure that the scheme is well-
audited before using in production implementations.)

### MOH_RSA_AES256_GCM_SHA256

This sample scheme implements RSA for the message header, and AES-256 in Galois/
Counter Mode for the message content, using SHA3-256 for hash operations.

Cryptographic Primitives:
 * [RSA](https://dl.acm.org/doi/10.1145/359340.359342)
 * [AES-256 GCM](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
 * [SHA3-256](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.202.pdf)

The client first generates the Initialization Vector (IV) to be used for the GCM
encrypt operation. In this scheme, part of it is the nonce sent in plaintext via
HTTP header (see [/relay](#post-_matrixclientv1obliviousmohrelay)).
Then, the client generates the symmetric encryption key (K) for the encrypt
operation.

PIV **MUST** be 16 bytes long, generated via a cryptograpically suitable
randomness source by the client, hashed via SHA-256 and truncated to 16 bytes.
The truncated 16 bytes (second segment) is used as Nonce.

K **MUST** be 32 bytes long, generated via a cryptographically suitable
randomness source by the client, hashed via SHA-256.

The message content JSON or data is then encrypted via AES-256 GCM using
PIV+Nonce (PIV with Nonce appended, for 32 bytes) as its Initialization Vector,
and K as its encryption key. Plaintext at the end of the plaintext body which
does not align with the AES block size should be padded with `0x00` (␀) bytes.

The client then generates the *plaintext header* as follows:

| Bytes | 1  | 16  | 32 | * |
| ----- | -- | --- | -- | - |
| Data  | PL | PIV | K  | P |

 * `PL` : Padding Length. 1 byte, randomly generated by client. **MUST** be
          within range `0x10` to `0x78`. Unencrypted.
 * `PIV`: Partial IV. 16 bytes.
 * `K`  : AES Key. 32 bytes.
 * `PB` : Padding. Zero **bits**, length specified by `PL`.

> Beware that `PL` has a length of __bits__ and padded data will often be
  misaligned!

The client then encrypts the header (except for the first byte `PL`) using the
server's ephemeral public key via RSA, and appends the encrypted payload to it,
thus generating the complete *Oblivious MoH request ciphertext*, or "encrypted
blob". It is then forwarded to the remote server.

Before decryption, the server **MUST** fail the request immediately if the Nonce
was used by any Oblivious MoH request which was used for a request which it
successfully decrypted using a ephemeral keypair which is *still* valid.

> One way of implementing this is keeping a list of Nonces already used for each
  keypair, and discarding that list whenever the keypair expires. This method
  could present unknown security risks however, by introducing additional logged
  fingerprintable entropy to incoming Oblivious MoH connections.

To decrypt the header, the server uses the first byte `0x01` as `PL`, and
attempts to decrypt bits from range `9` to `392` + `PL` sequentially using every
ephemeral RSA private key it currently recognizes. The header is considered
valid if all bits in the plaintext from `392` to `392` + `PL` are zero bits.

The server then attempts to decrypt the payload appended after the header
length, using PIV + Nonce (PIV with Nonce appended) as Initialization Vector and
K as key for AES-256 GCM.

If the payload is valid JSON, the server processes it as requested.

When the server encrypts its response to be forwarded back to the client, it
encrypts the payload using AES-GCM.
 * `PIV` is substituted by the `response_nonce` requested by the client,
 * `K` is substituted by the `K` used in the request header.

Note that the server does not use a header in its encrypted response.

The client thus decrypts the encrypted blob response from the server similarly
to before, using the `response_nonce` and `K` that it generated when creating
the initial JSON container.

## Security Considerations

### API Endpoint Whitelisting / Blacklisting

As Oblivious MoH is designed to interact with Matrix homeservers exclusively, it
is imperative that server implementations of OMoH are locked down so they cannot
route traffic to HTTP endpoints which are not relevant to usage of the Matrix
protocol, especially to non-homeserver HTTP services.

Specific implementation is left up to the homeserver, but in general a way for
homeserver administrators to configure which `path`s on the homeserver's domain
are be reachable via Oblivious MoH should be exposed via the homeserver's
configurations. A whitelist approach is recommended (such as by default only
allowing `/.well-known/matrix/*` and `/_matrix/client/*` except for
`/_matrix/client/*/obliviousMoh/*`). Although a homeserver *may* expose
non-Matrix HTTP endpoints through Oblivious MoH, this is not recommended for
security and implementation parity reasons.

Oblivious MoH requests to disallowed endpoints *should* return 403 Forbidden via
`/incoming`.

### Choosing Relay and Remote Homeservers

Users **MUST** take every precaution to ensure that both the relay server and
the remote homeserver that they choose are not controlled by one party, and that
an adversary will need considerable effort to compromise both at once.
Otherwise, colluding homeservers can trivially correlate the user's relay and
actual Matrix traffic, and associate the user's physical IP address with the
user's Matrix identity, thereby defeating Oblivious MoH entirely.

Ideally, Matrix clients which implement Oblivious MoH securely *should* also
implement behaviour that allows users to identify approximate geographical
locations of servers they choose (e.g. via a local GeoIP database), and warn
against picking servers located within the same country or general legal
jurisdiction.

Clients *should* also strongly warn against picking servers which reside on the
same /24 IPv4 subnet.

In the future, Oblivious MoH specifications should include a way for server
operators to declare other homeservers or OMoH relays that they control, and
specification-compliant clients **MUST** not use any OMoH route that includes
servers which both reference one another in this declaration (similar to Tor's
`MyFamily` relay configuration).

### Rate Limiting

Oblivious MoH presents a new potential vector for Denial of Service (DoS)
attacks against homeservers, using OMoH relays to blend in with normal anonymous
users. In general, it may be very well impossible to rate-limit requests from
Oblivious MoH relays in a satisfactory manner, due to the inherent anonymous
nature of the traffic.

Oblivious MoH relays may receive 422 Too Many Request responses in plaintext.
In these cases, the relay *should* temporarily block `/relay` requests from the
client's IP to the remote homeserver's host until the specified time indicated
within the response is reached. Individual blocks **MUST** be limited to 1 hour
or less to minimize data retention.

Homeservers which implement Oblivious MoH `/incoming` *should* ideally first
rate-limit users by their `Authorization` token whenever available. For
unauthenticated users, the receiving homeserver *should* send back 422 Too Many
Request in plaintext, but not actually block the IP of the Oblivious MoH relay.
Only when a relay sends excessive traffic which should already be rate-limited
should it be temporarily blocked. Specific implementation is left to the
homeserver.

### User Education

It is important for Matrix users to understand the limitations of Oblivious MoH,
and not to grow to rely on it as a "catch-all" privacy solution. The following
best practices are recommended when utilizing Oblivious MoH:

 * Oblivious MoH does not magically make you completely anonymous. It should be
   treated as a first line of defense for your anonymity at best, and it only
   works if you follow the necessary precautions while using it:
 * Avoid giving personally identifiable information to your homeserver unless
   it's encrypted (encrypted rooms, or Secrets). This includes username, display
   name, profile image, and email or phone associated with an identity server.
 * Avoid sending messages containing personally identifiable information to
   unencrypted rooms, or to peers that you don't trust.
 * Do not mix between using Matrix with Oblivious MoH and using Matrix normally
   over a single identity. Either connect anonymously or not; a single login
   request may make a malicious homeserver aware of your physical IP address.
 * Do not use VoIP over Oblivious MoH yet as it is not implemented.
 * Don't use an identity server as this may make your data available to more
   parties.
 * Do not rotate relays excessively; this makes it probabilistically easier for
   an adversary to become your Oblivious MoH relay at some point, and can make
   local adversaries suspicious of your traffic. Ideally, a single relay should
   be retained for at least several weeks at a time.
 * Ensure that your Oblivious MoH relay and your remote homeserver are most
   certainly controlled by different parties, ideally in different countries,
   and best if also in politically distinct jurisdictions, to minimize the
   chances of a global adversary being able to compromise both at the same time.
 * Use distinct identities for using Matrix for instant messaging, and using
   Matrix for third-party applications.
 * It is best to implement defense-in-depth. Consider using OMoH over a proxy or
   Tor if you are knowledgeable enough to configure it securely.
 * Avoid using Oblivious MoH over a web client, as it is significantly more
   difficult to verify the integrity of a web client compared to a native one.

### Server Network Logging

Many homeservers currently keep logs of incoming connections to Matrix
endpoints, and sometimes may associate them with authenticated Matrix
identities.

Although Oblivious MoH by design defeats deanonymization through such traffic
analytics, it is wise for homeservers to minimize logs they keep on Oblivious
MoH connections regardless, as this can provide additional fingerprintable
vectors of Oblivious MoH users should the homeserver's network logs be
compromised.

### Deep Packet Inspection Fingerprinting Resistance

Oblivious MoH by design blends in with regular Matrix requests to the relay
server, to fool intelligent firewalls controlled by network adversaries. There
are some challenges to this approach associated with the current specification:

 * Requests are always slightly inflated in size due to additional overhead from
   JSON encapsulation. This may be impossible to optimize without breaking the
   "oblivious-ness" of Oblivious MoH, unless a custom data protocol is
   implemented which compresses the necessary HTTP parameters.
 * Requests are always slightly slower than normal Matrix requests, due to
   increased latency from relaying.
 * The initial setup phase of obtaining a server's TLS certificate, public key,
   and canonical homeserver URL triggers 1 or 2 more requests compared to normal
   Matrix clients.
 * Sending non-JSON data further inflates requests and responses due to the need
   to encode binary data with Base64.

These vectors could theoretically provide additional entropy for a local or
global adversary with access to powerful network analytics to identify Oblivious
MoH users. This could prove problematic in the future for users who reside in
regions with strong internet censorship, such as China (especially with its new
[machine-learning based approach to internet censorship](https://github.com/net4people/bbs/issues/129)).

### DNS Domain Mismatch

In rare cases the relay server may not resolve the hostname of the remote
homeserver properly, due to various DNS issues or attacks, which will often
cause a mismatch between the domain name that the client expects, and the domain
name specified by TLS certificate served by the remote homeserver, resulting in
Oblivious MoH failing to initialize. It may be possible to instead target the
remote homeserver via its IP address directly, but the action of resolving the
remote homeserver's domain from the client may reveal to a local or global
adversary that the user may be using Oblivious MoH, and the remote homeserver
they use.

For now, it is assumed that the relay server has good DNS resolution, as
otherwise it would also fail to connect to many members of the Matrix homeserver
federation. This may be a point to address in the future, using solutions such
as Distributed Hash Tables.

## Limitations

Existing major limitations of Oblivious MoH:
 * No VoIP. Calls must be routed peer-to-peer, or via the remote homeserver's
   TURN server directly.
 * No automatic discovery of relays. Users must manually choose an OMoH relay
   by its domain, obtained from an out-of-band source.
 * Only 1 hop. The probability of both servers maliciously colluding is
   nontrivial.

These problems are addressed in [Extensions & Future Work](#future-work--extensions).

## Future Work & Extensions

### VoIP over Oblivious MoH

VoIP is a major feature of Matrix, and rendering it inaccessible over Oblivious
MoH would greatly hinder many of its use cases. A future version of Oblivious
MoH should allow for OMoH relays to act as anonymous TURN servers, though this
approach has its own issues associated with deanonymization through in-depth
traffic analysis, as well as denial of service attacks.

### Relay Discovery

To improve the homogeneity of Oblivious MoH users, it may be wise to implement a
decentralized system for discovery of OMoH relays, similar to the directory
authority consensus implemented in Tor.

### Longer OMoH Routes

Implementing routes with more hops through Oblivious MoH relays can improve
anonymity, at an approximate exponentially growing cost to the complexity of the
protocol, complexity of client and server implementation, and by extension, the
number of potential security and usability issues within Oblivious MoH. As OMoH
begins to offer anonymity levels closer to onion routers and other similar
services, users will grow to rely on it for many aspects of privacy and
security, thus making a watertight specification and implementation much more
important.

### Non-Interactive Immediate Perfect Forward Secrecy

Future implementations can use novel techniques such as [puncturable encryption](https://en.wikipedia.org/wiki/Forward_secrecy#Non-interactive_forward_secrecy)
to achieve immediate perfect forward secrecy. The current blob encryption scheme
offers weak forward secrecy only, by regularly rotating the intermediate
ephemeral keypair signed by the remote homeserver, which is probably somewhat
insufficient for the threat model which Oblivious MoH adopts.

### Extensions: Non-Anonymous Matrix over HTTPS

The `/.well-known/matrix/moh` endpoint is designed to be extensible for
accommodating a variety of relayed traffic over Matrix, not just for Oblivious
MoH. Future MSCs can take advantage of the existing frameworks laid out by OMoH.
For example, a new MSC can add endpoints which allows for authenticated Matrix
over HTTPS traffic, for controlling authorized access to an isolated Matrix
network via "edge" homeservers.

### Extensions: Other Traffic over OMoH / MoH

It may be possible to send other types of traffic through Matrix homeservers for
custom applications. These will likely not make it into the standard Matrix spec
due to security considerations, but implementations for customized use cases
will likely appear in the wild.

### Extensions: "Hidden Service" Homeservers

If Oblivious MoH is adapted to allow transport of `/server` traffic with proper
anonymization measures, it may be theoretically possible to host a homeserver
which does not directly interact with any other homeserver, thus concealing its
physical location. This is a similar concept to Hidden Services implemented by
Tor.

### Extensions: Store And Forward

Some users may have extreme privacy requirements that requires resisting large-
scale timing attacks. A future Oblivious MoH specification could theoretically
add a parameter which allows clients to request that relays store their message
for an arbitrary amount of time before forwarding to the relay homeserver, or
other relays along the path. Although this method could have unknown security or
usability repercussions, it is simple implement due to the already (almost-)
stateless nature of Oblivious MoH.

## On P2P Matrix / Pinecone

The primary reason to use Oblivious MoH instead of P2P Matrix for anonymity is
aptly conveyed by the Pinecone README FAQ:

> ### Does Pinecone provide anonymity?
>
> No, it is not a goal of Pinecone to provide anonymity. Pinecone packets will
> be routed using the most direct paths possible (in contrast to Tor and
> friends, which deliberately send traffic well out of their way) and Pinecone
> packets do contain source and destination information in their headers
> currently. It is likely that we will be able to seal some of this information,
> in particular the source addresses, to reduce traffic correlation, but this is
> not done today.

It is likely that a future version of Pinecone will indeed be designed to
provide stronger anonymity, but as a P2P network without enforced onion routing
by design, this would greatly impact the original usability scopes of the
project. If the tradeoff is instead made to not enforce anonymization via relays
which would allow discerning between anonymized and non-anonymized traffic on
the Pinecone network, this provides a highly significant fingerprinting vector
which greatly weakens any potential anonymity it could offer.

Oblivious MoH inherently tackles a different issue within Matrix by providing
user anonymity with minimal implementation complexity and blending in with
existing traffic, while Pinecone prioritizes decentralization and reachability
before privacy as a data transport backbone.

That being said, this is not a binary choice; Oblivious MoH and Pinecone can
easily coexist, and it is likely also possible to utilize Oblivious MoH *over*
Pinecone. Oblivious MoH (or more likely Matrix over HTTPS in general) could also
become a bridge protocol between the Matrix P2P network and any existing Matrix
federations over HTTP, both public and internal.

## Unstable Prefix

During the MSC stage, all endpoints *except* for `/.well-known/matrix/moh` will
use the unstable version prefix `/unstable/org.matrix.msc3963`. The Oblivious
MoH version shall be `msc3963`.

MSC Endpoints:
 * `/_matrix/client/unstable/org.matrix.msc3963/obliviousMoh/relay`
 * `/_matrix/server/unstable/org.matrix.msc3963/obliviousMoh/incoming`
 * `/_matrix/client/unstable/org.matrix.msc3963/obliviousMoh/getCapabilities`
