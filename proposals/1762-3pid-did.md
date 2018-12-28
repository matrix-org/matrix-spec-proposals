# Proposal to support user-owned identifiers as 3rd party identifiers (3PID)

Email and phone numbers are well-established third party identifiers (3PID). The verification that a user owns such an identifiers is usually done by sending an email or SMS. This requires interaction from the user and is not immediate. With the advances in blockchain technologies, so-called user-owned or "distributed identifiers" (DID) have been established that are created, owned and controlled by the person herself. The ownership of DIDs are verifiable by third-parties immediately, usually using cryptographic calculations and public/private key pairs. Shared secrets (passwords) are not required. Therefore, DIDs are good candidates to authenticate a user when logging in to a matrix home server.

For the matrix protocol, this means that DIDs can be associated to a user account immediately, and that autentication can be done with the username and 3PID only, without using the user's password. 

While DIDs are not human-friendly identifiers by definition there are some DID methods that associate a human-friendly id to DIDs. These ids/names can be used to find matrix users through the identity servers. The details for such a search by DID names should be defined in a new MSC.

## Proposal

During the last year decentralized identifiers have been standardized by the [W3C Credentials Community Group](https://w3c-ccg.github.io) (CCG). There exists several methods to create DIDs. A list of these methods is maintained by the [CCG Method Registry](https://w3c-ccg.github.io/did-method-registry). The group also defines standards to describe properties of identifiers, in particular how to verify ownership of DIDs.

Supporting DIDs as a new 3PID type opens the matrix network to users that are using DIDs, enables applications with control over DIDs to communicate across the borders of DID methods, e.g. connect users with a blockstack.org account (did:stacks:..) to users with sovrin.org accounts (did:sov:..) and to users that do not have any DID but a matrix account. 

DIDs should be defined as a new 3PID type. The medium should be defined as ``did``. The address should contains the DID in normalized form as [defined by the W3C CCG](https://w3c-ccg.github.io/did-spec/#normalization).

Example:

```
{ 
    medium: "did",
    address: "did:stack:v0:15gxXgJyT5tM5A4Cbx99nwccynHYsBouzr-0"
}
```
The user should be able to add this 3PID to her account.

Furthermore, the new type of login ``m.login.signature`` should be defined for login calls and user-interactive authentication API calls as follows:

Authentication is supported by a challenge-response requests where the
session id is signed with the private key associated to the identifier. The home server
should only accept this stage as completed if all of the following holds:
* the identifier is valid for an active user account
* a public key could be deduced from the identifer
* the signature could be verified with the public key

To use this authentication type in login calls, clients should submit the following:
.. code:: json

  {
    "type": "m.login.signature",
    "identifier": {
      ...
    },
    "signature": "<signature>",
  }
where the signature is the signed challenge that the user has received before from challenge/response endpoint of the home server.

To use this authentication type in user-interactive authentication API calls, clients should submit an auth dict as follows:

.. code:: json

  {
    "type": "m.login.signature",
    "identifier": {
      ...
    },
    "signature": "<signature>",
    "session": "<session ID>"
  }

If no public key could be deduced from the identifier the error ``M_UNRECOGNIZED`` should
be returned. If the signature could not be verified the error ``M_UNAUTHORIZED`` should be returned and the session should be invalidated.

Currently, identifiers of type ``m.id.thirdparty`` and medium ``did`` could be accepted by using a universal DID resolver to get the public key of the DID. Home servers can choose between a hosted version like [Universal Resolver](https://uniresolver.io) or implement their own resolver e.g. based on the [universal-resolver on github](https://github.com/decentralized-identity/universal-resolver/). If the cryptographic method of the public key is not supported then the error ``M_UNRECOGNIZED`` should be returned.



## Tradeoffs

Instead of adding a new type of 3PID DID could be defined as a new identifier type like 
``m.id.did`` as the user has created the DID herself and is in control of it. However, DIDs define their own namespace that matches the concept of 3PID very well.

Instead of adding a new login type, the type ``m.login.password`` could be used. The password could contain the signature of the challenge and during password verification the home server could verify the signature. However, it is not the password of matrix user and therefore, the password login type should not be used.

The verification of the signature and the creation of the challenge for the login call could be handled by the identity server. The user would then just submit the 3PID verificaion credentials of the identity server session for login calls similar to ``m.login.email.identity``. However, this would transfer the responsibility of authentication to the identity server.

## Potential issues

The universal resolution of DIDs could add extra code that is not at the core of the matrix project. Here, delegating to a hosted version could help.

The verification of signatures could add more cryptographic code that is not at the core of the matrix project. Here, the existing code for signature verification could be used.


## Security considerations

* Universal resolution of DIDs depends on public nodes of the associated distributed ledger/blockchain network. If the chosen node turns into a bad node there should be a possibility for the user to switch nodes.

* The challenge could be guessed by someone else or reused for a login. It needs to be ensured that the session id of the authentication flow is random enough and that it is not reused in the future.


## Conclusion

Adding support for decentralized identifiers is inline with the vision of matrix.org to build an open, decentralized communication network. The proposed new 3PID type helps users to include their DID as they are used to it with email and phone numbers. The cryptographic properties of DIDs require a new login type that defines a challenge/response request and signature validation.

