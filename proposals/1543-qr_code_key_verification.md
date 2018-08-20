Key verification using QR codes
===============================

Problem/Background
------------------

Key verification is essential in ensuring that end-to-end encrypted messages
cannot be read by unauthorized parties.  Traditionally, key verification is
done by comparing long strings.  To save users from the tedium of reading out
long strings, some systems allow one party to verify the other party by
scanning a QR code; by doing this twice, both parties can verify each other.
In this proposal, we present a method for both parties to verify each other by
only scanning one QR code.

Other methods exist for making it easier to verify keys.  In Matrix,
[MSC1267](https://github.com/matrix-org/matrix-doc/issues/1267) proposes
another method, which is useful when neither party is able to scan a QR code.

Proposal
--------

Example flow:

1. Alice and Bob meet in person, and want to verify each other's keys.
2. Bob tells his device to display a QR code.  Bob's device displays a
   byte-encoded QR code using UTF-8 of the string `/verify <user-id>
   <device-id> <device-signing-public-key>`.  (This format matches the
   `/verify` command in Riot.)
3. Alice scans the QR code.
4. Alice's device ensures that the user ID in the QR code is the same as the
   expected user ID.  This can be done by prompting Alice with the user ID, or
   can be done automatically if the device already knows what user ID to
   expect.  At this point, Alice's device has now verified Bob's key.
5. Alice's device sends a `m.key.verification.reciprocate` message (see below)
   as a to-device message to Bob's device (using the user ID and device ID from
   the QR code.)
6. Bob's device fetches Alice's public key, signs it, and sends it to Alice's
   device in a `m.key.verification.check_own_key` to-device message (see
   below).  Bob's device displays a message saying that Alice wants him to
   verify her key, and presents a button for him to press /after/ Alice's
   device says that things match.
7. Alice's device receives the `m.key.verification.check_own_key` message,
   checks Bob's signature, and checks that the key is the same as her device
   key.  Alice's device displays the result of the checks.
8. Bob sees Alice's device confirm that the key matches, and presses the button
   on his device to indicate that Alice's key is verified.

### Message types

#### `m.key.verification.reciprocate`

Tells Bob's device that Alice has verified his key, and requests that he verify
Alice's key in turn.

message contents:

- `device_id`: the ID of the device that Alice is using
- `transaction_id`: a unique identifier for the transaction (is this needed?)

#### `m.key.verification.check_own_key`

Tells Alice's device what Bob's device thinks her key is.

message contents:

- `key`: The key that Bob's device has for Alice's device
- `transaction_id`: the transaction ID from the
  `m.key.verification.reciprocate` message
- `signatures`: signature of the key and transaction ID, signed using Bob's key

Tradeoffs/Alternatives
----------------------

The exact format for the QR code is not nailed down.  Another possibility is
that it could be a URL, so that a user can scan the code in any QR code
scanner, and have it automatically open the user's Matrix client to begin the
verification.

Security Considerations
-----------------------

Step 4 is to ensure that Bob does not present a QR code claiming to be Carol's
key.  Without this check, Bob will be able to trick Alice into verifying a key
under his control, and evesdropping on Alice's communications with Carol.

Other Issues
------------

Conclusion
----------
