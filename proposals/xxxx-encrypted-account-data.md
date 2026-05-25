# MSCXXXX: Encrypted Account Data

Many features, such as [MSC4441][], store information within [`account_data`][] that may contain sensitive information
that the server doesn't require access to, and hence can be encrypted to improve privacy. This MSC introduces encrypted
account data, which may be used to optionally encrypt sensitive values.

## Proposal

### Account Data Key (ADK)

Clients MAY choose to store a new secret, `m.account_data.key` within [secret storage][]. The value of the key, the
"ADK secret," is 256 bits of cryptographic random data used as the secret in the HKDF when encrypting account data.

`m.account_data.key`:

```json
{
    "encrypted": {
        "key_id_1": {
            "ciphertext": "base64+encoded+encrypted+data",
            "mac": "base64+encoded+mac",
            // ... other properties according to algorithm property in
            // m.secret_storage.key.key_id_1
        }
    }
}
```

### Encrypted Account Data

Using the ADK secret introduced above, specified "encryptable" account data MAY be encrypted using the
[`m.secret_storage.v1.aes-hmac-sha2`][] algorithm. Clients MUST NOT encrypt specified account data that has not been
listed as encryptable. Clients MAY, however, encrypt their own unspecified account data, given that those events are
named using a [Common Namespaced Identifier].

`com.example.some_encryptable_account_data_key`:

```json
{
    "encrypted": {
        "iv": "...",
        "ciphertext": "...",
        "mac": "..."
    }
}
```

## Potential issues

This MSC explicitly limits account data encryption to a limited set of events to prevent clients from encrypting account
data the server may rely upon, such as `m.push_rules`.

Clients which do not understand Encrypted Account Data may overwrite encrypted values with their own data, or improperly
handle these values.

If a user loses access to SSSS and resets their identity, all encrypted account data is lost.

## Alternatives

* Account data as a whole could be encrypted natively.  
  This breaks backwards-compatibility with older clients, and servers may rely on information stored within account data
  to function properly.
* Eliminate the ADK and simply use the SSSS master.  
  Using the SSSS master would require re-encrypting account data whenever recovery keys change. Usage of a separate ADK
  is extensible for further `account_data` events, alongside providing the ability to rotate the ADK independently of
  SSSS.

## Security considerations

Alongside all other forms of cryptography used within present Matrix, AES-CTR-256 (the algorithm that backs
`m.secret_storage.v1.aes-hmac-sha2`) is vulnerable to Grover's algorithm. However, symmetric algorithms are not
vulnerable in the same manner, with their security bit-strength being effectively halved. PQC is still being actively
investigated in the Matrix ecosystem, and if it is determined that these algorithms are ineffective, a future MSC may
introduce additional algorithms.

## Dependencies

None.

## Unstable prefix

Before this MSC is accepted, implementations should use the following unstable key names:

| Stable identifier    | Purpose         | Unstable identifier                  |
| -------------------- | --------------- | ------------------------------------ |
| `m.account_data.key` | ADK secret name | `dev.zirco.MSCXXXX.account_data.key` |

[MSC4441]: https://github.com/matrix-org/matrix-spec-proposals/pull/4441
[`account_data`]: https://spec.matrix.org/v1.18/client-server-api/#client-config
[secret-storage]: https://spec.matrix.org/v1.18/client-server-api/#secret-storage
[`m.secret_storage.v1.aes-hmac-sha2`]: https://spec.matrix.org/v1.18/client-server-api/#msecret_storagev1aes-hmac-sha2-1
[Common Namespaced Identifier]: https://spec.matrix.org/v1.18/appendices/#common-namespaced-identifier-grammar

