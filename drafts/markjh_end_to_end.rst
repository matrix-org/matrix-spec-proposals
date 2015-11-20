Goals of Key-Distribution in Matrix
===================================

* No Central Authority: Users should not need to trust a central authority
  when determining the authenticity of keys.

* Easy to Add New Devices: It should be easy for a user to start using a
  new device.

* Possible to discover MITM: It should be possible for a user to determine if
  they are being MITM.

* Lost Devices: It should be possible for a user to recover if they lose all
  their devices.

* No Copying Keys: Keys should be per device and shouldn't leave the device
  they were created on.

A Possible Mechanism for Key Distribution
=========================================

Basic API for setting up keys on a server:

https://github.com/matrix-org/matrix-doc/pull/24

Client shouldn't trust the keys unless they have been verified, e.g by
comparing fingerprints.

If a user adds a new device it should some yet to be specified protocol
communicate with an old device and obtain a cross-signature from the old
device for its public key.

The new device can then present the cross-signed key to all the devices
that the user is in conversations with. Those devices should then include
the new device into those conversations.

If the user cannot cross-sign the new key, e.g. because their old device
is lost or stolen. Then they will need to reauthenticate their conversations
out of band, e.g by comparing fingerprints.


Goals of End-to-end encryption in Matrix
========================================

* Access to Chat History: Users should be able to see the history of a
  conversation on a new device. User should be able to control who can
  see their chat history and how much of the chat history they can see.

* Forward Secrecy of Discarded Chat History: Users should be able to discard
  history from their device, once they have discarded the history it should be
  impossible for an adversary to recover that history.

* Forward Secrecy of Future Messages: Users should be able to recover from
  disclosure of the chat history on their device.

* Deniablity of Chat History: It should not be possible to prove to a third
  party that a given user sent a message.

* Authenticity of Chat History: It should be possible to prove amoungst
  the members of a chat that a message sent by a user was authored by that
  user.


Bonus Goals:

* Traffic Analysis: It would be nice if the protocol was resilient to traffic
  or metadata analysis. However it's not something we want to persue if it
  harms the usability of the protocol. It might be cool if there was a
  way for the user to could specify the trade off between performance and
  resilience to traffic analysis that they wanted.


A Possible Design for Group Chat using Olm
==========================================

Protecting the secrecy of history
---------------------------------

Each message sent by a client has a 32-bit counter. This counter increments
by one for each message sent by the client. This counter is used to advance a
ratchet. The ratchet is split into a vector four 256-bit values,
:math:`R_{n,j}` for :math:`j \in {0,1,2,3}`. The ratchet can be advanced as
follows:

.. math::
    \begin{align}
    R_{2^24n,0} &= H_1\left(R_{2^24(i-1),0}\right) \\
    R_{2^24n,1} &= H_2\left(R_{2^24(i-1),0}\right) \\
    R_{2^16n,1} &= H_1\left(R_{2^16(i-1),1}\right) \\
    R_{2^16n,2} &= H_2\left(R_{2^16(i-1),1}\right) \\
    R_{2^8i,2}  &= H_1\left(R_{2^8(i-1),2}\right) \\
    R_{2^8i,3}  &= H_2\left(R_{2^8(i-1),2}\right) \\
    R_{i,3}     &= H_1\left(R_{(i-1),3}\right)
    \end{align}

Where :math:`H_1` and :math:`H_2` are different hash functions. For example
:math:`H_1` could be :math:`HMAC\left(X,\text{"\textbackslash x01"}\right)` and
:math:`H_2` could be :math:`HMAC\left(X,\text{"\textbackslash x02"}\right)`.

So every :math:`2^24` iterations :math:`R_{n,1}` is reseeded from :math:`R_{n,0}`.
Every :math:`2^16` iterations :math:`R_{n,2}` is reseeded from :math:`R_{n,1}`.
Every :math:`2^8` iterations :math:`R_{n,3}` is reseeded from :math:`R_{n,2}`.

This scheme allows the ratchet to be advanced an arbitrary amount forwards
while needing only 1024 hash computations.

This the value of the ratchet is hashed to generate the keys used to encrypt
each mesage.

A client can decrypt chat history onwards from the earliest value of the
ratchet it is aware of. But cannot decrypt history from before that point
without reversing the hash function.

This allows a client to share its ability to decrypt chat history with another
from a point in the conversation onwards by giving a copy of the ratchet at
that point in the conversation.

A client can discard history by advancing a ratchet to beyond the last message
they want to discard and then forgetting all previous values of the ratchet.

Proving and denying the authenticity of history
-----------------------------------------------

Client sign the messages they send using a Ed25519 key generated per
conversation. That key, along with the ratchet key, is distributed
to other clients using 1:1 olm ratchets. Those 1:1 ratchets are started using
Triple Diffie-Hellman which provides authenticity of the messages to the
participants and deniability of the messages to third parties. Therefore
any keys shared over those keys inherit the same levels of deniability and
authenticity.

Protecting the secrecy of future messages
-----------------------------------------

A client would need to generate new keys if it wanted to prevent access to
messages beyond a given point in the conversation. It must generate new keys
whenever someone leaves the room. It should generate new keys periodically
anyway.

The frequency of key generation in a large room may need to be restricted to
keep the frequency of messages broadcast over the individual 1:1 channels
low.
