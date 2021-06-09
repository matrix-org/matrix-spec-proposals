# \[WIP]MSCXXXX: aPAKE authentication

Like most password authentication, matrix's [login](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-login) requires sending the password in plain text (though usually encrypted in transit with https). This requirement has as (obvious) downside that a man in the middle attack would allow reading the password, but also requires that the server has temporary access to the plaintext password (which will subsequently be hashed before storage).

A Password Authenticated Key Exchange (PAKE) can prevent the need for sending the password in plaintext for login, and an aPAKE (asymmetric or augmented) allows for safe authentication without the server ever needing access to the plaintext password. OPAQUE is a modern implementation of an aPAKE that is [currently an ietf draft](https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-opaque-05).

## Proposal



## Potential issues

Adding this authentication method requires client developers to implement this in all matrix clients.

OPAQUE is still a draft at ietf, and doesn't have very many implementations, potentially making the lives of client developers harder. *perhaps srp is better? I'd be fine with deciding to go with SRP, as it has more implementations available.*

## Alternatives

Secure Remote Password (SRP) is the most commonly used alternate aPAKE, which has a longer track record, and is used by apple and 1password, and is [rfc2945](https://datatracker.ietf.org/doc/html/rfc2945).

*Bitwardens scheme can be mentioned here as well, since it does allow auth without the server learning the plaintext password, but it isn't a PAKE, but rather something along the lines of a hash of the password before sending the has to the server for auth, practically making the hash the new password, and as such it doesn't protect against a mitm.*


## Security considerations

Probably loads, though SRP and OPAQUE have had lots of eyes, I would assume.

## Unstable prefix


