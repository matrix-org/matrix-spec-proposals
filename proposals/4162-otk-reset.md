## MSC4162: One-Time Key Reset Endpoint


### Context
One-time keys (OTKs) consist of two parts: a public part which is stored on the server and a private part which is stored on the client device. One-time keys can be uploaded to the server with the `/keys/upload` endpoint. They can then be consumed via the `/keys/claim` endpoint. The client is kept informed of the total number of OTKs stored on the server via the `/sync` endpoint, with the JSON key `device_one_time_keys_count`. It is critical that the set of keys on the client and server remain in-sync, otherwise an encrypted channel between two devices cannot be established. "In-sync" is defined by the set of public keys on the server having their matching private keys on the client.

OTKs can be "in-flight". This describes the scenario where a OTK has been claimed by another device via `/keys/claim`, but a message encrypted with this key has not been received yet. There are many valid reasons for why the message has not been received yet, but it is also a potential attack vector if the client is forced to remember all keys for all time.

### Desync causes
In practice, OTKs desync for a myriad of reasons, some of which are outlined below.

#### Client issues

 - If the request to `/keys/upload` fails, the client must retry (including over restarts) the _same set of keys_ as it is not possible to know if the server received the request and has stored them already. If this doesn't happen, the server may return HTTP 400 errors indicating this. [[issue](https://github.com/matrix-org/matrix-rust-sdk/issues/1415)]
 - If the client runs across multiple processes, both processes can upload different sets of OTKs in response to some trigger event (e.g being notified that a OTK has been consumed via `/sync`). [[issue](https://github.com/matrix-org/matrix-rust-sdk/issues/3110)]
 - Clients should only delete a OTK once the key has been successfully used. [[issue](https://github.com/matrix-org/matrix-rust-sdk/issues/1761)]
 - Client databases may become corrupted due to hardware failure.
 - Client databases may be rolled back (e.g full phone backups).

#### Server issues
 - Server databases may become corrupted due to hardware failure.
 - Server databases may be rolled back (e.g during a bad upgrade process).

#### Protocol issues
 - Clients only store a limited set of OTKs. When they delete excess OTKs they have no mechanism to tell the server to delete those old OTKs.
 - Multiple users could hit `/keys/claim` at the same time as a client is uploading OTKs, which creates race conditions which can cause the same key to be sent to multiple users. [[issue](https://github.com/matrix-org/matrix-spec/issues/1124)]

### Proposal

#### Reset endpoint
 A new endpoint `POST /keys/reset` is added. It accepts the following request body:

 ```js
 {
    "all": true|false
    "key_ids": [
        "<algorithm>:<key_id>", ...
    ]
 }
 ```
- If `all` is `true`, all stored one-time keys for the calling device are deleted on the server, and `key_ids` is ignored.
- If `all` is `false`, every key specified in `key_ids` is deleted from the database. An example key ID is `signed_curve25519:AAAAHQ`.

The server will then return the following response:
```js
{
    "device_one_time_keys_count": {
       "<algorithm>": 0 // or whatever the count value is after this operation is applied
    }
}
```

#### Claiming keys ordering
In addition to these changes, the semantics around `/keys/claim` has been slightly modified. Currently, the semantics are simply:

> Claims one-time keys for use in pre-key messages.

This does not define a sort ordering (i.e _which_ key should be given out to the caller). This MSC proposes tweaking this wording to be:

> Claims one-time keys for use in pre-key messages. The key claimed MUST be the lowest lexicographically sorted key ID for that algorithm. For example, given two key IDs of `AAAAAu` and `AAAAHg`, `AAAAAu` MUST be returned before `AAAAHg`.

### Rationale

The primary motivation of this endpoint is to provide a way for a client and server to resync OTKs. To do this, a client would call `/keys/reset` with `all: true` to delete all OTKs on the server. Once this 200 OKs, the client is then safe to perform `/keys/upload` with a fresh set of OTKs. This functionality is particularly important for existing clients who currently have desynced OTKs.

A secondary motivation of this endpoint is to provide a way for clients to tell servers to delete OTKs which the client has decided to delete (e.g due to low disk space). To do this, a client would call `/keys/reset` with `key_ids: [ the, keys, being, deleted, from, the, client ]`. Once this 200 OKs, the client is then safe to perform the deletion.

The introduction of a dedicated endpoint, as opposed to allowing OTKs to replace each other when performing `/keys/upload`, is to make it an explicit decision for clients to reset OTKs. This removes the risk of hiding client bugs, as the client will only know of the desync when `/keys/upload` returns an HTTP 400.

Finally, the motivation to change `/keys/claim` allows clients to detect and delete in-flight OTKs. They can do this by performing the following:
- Upload OTKs A,B,C,D.
- 2 users claim OTKs for this device. The server MUST return A then B.
- Client receives an encrypted message encrypted with B.
- At this point, the client knows that A is in-flight as A comes before B. It can then wait to see if an encrypted message will be sent using that key, or it can eventually give up (e.g after 30 days) and then delete the key using `/keys/reset`.

### Alternatives
- Allow `/keys/upload` to replace OTKs which have a matching key ID. This risks hiding client and server bugs. It also does nothing to help desync causes due to other issues e.g database issues.
- Do nothing. Clients and servers will continue to desync over time, causing more Olm sessions to be unable to be established, causing unable to decrypt errors.

### Security Considerations

- If an access token is compromised, a malicious attacker can reset OTKs for that device. This would force the fallback key to be used when establishing Olm sessions.

### Unstable prefix

Whilst in development, the path shall be `/_matrix/client/unstable/org.matrix.msc4162/keys/reset`. There is no proposed unstable prefix for the changed semantics to `/keys/claim` due to the change being backwards compatible and valid for servers to do today.

### Appendices

- [Meta-issue](https://github.com/element-hq/element-meta/issues/2406) describing the general problem of OTK desyncing.
