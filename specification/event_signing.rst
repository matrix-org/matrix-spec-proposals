.. Copyright 2016 OpenMarket Ltd
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Signing Events
--------------

Canonical JSON
~~~~~~~~~~~~~~

Matrix events are represented using JSON objects. If we want to sign JSON
events we need to encode the JSON as a binary string. Unfortunately the same
JSON can be encoded in different ways by changing how much white space is used
or by changing the order of keys within objects. Therefore we have to define an
encoding which can be reproduced byte for byte by any JSON library.

We define the canonical JSON encoding for a value to be the shortest UTF-8 JSON
encoding with dictionary keys lexicographically sorted by unicode codepoint.
Numbers in the JSON must be integers in the range [-(2**53)+1, (2**53)-1].

We pick UTF-8 as the encoding as it should be available to all platforms and
JSON received from the network is likely to be already encoded using UTF-8.
We sort the keys to give a consistent ordering. We force integers to be in the
range where they can be accurately represented using IEEE double precision
floating point numbers since a number of JSON libraries represent all numbers
using this representation.

.. code:: python

 import json

 def canonical_json(value):
     return json.dumps(
         value,
         # Encode code-points outside of ASCII as UTF-8 rather than \u escapes
         ensure_ascii=False,
         # Remove unnecessary white space.
         separators=(',',':'),
         # Sort the keys of dictionaries.
         sort_keys=True,
         # Encode the resulting unicode as UTF-8 bytes.
     ).encode("UTF-8")

Grammar
+++++++

Adapted from the grammar in http://tools.ietf.org/html/rfc7159 removing
insignificant whitespace, fractions, exponents and redundant character escapes

.. code::

 value     = false / null / true / object / array / number / string
 false     = %x66.61.6c.73.65
 null      = %x6e.75.6c.6c
 true      = %x74.72.75.65
 object    = %x7B [ member *( %x2C member ) ] %7D
 member    = string %x3A value
 array     = %x5B [ value *( %x2C value ) ] %5B
 number    = [ %x2D ] int
 int       = %x30 / ( %x31-39 *digit )
 digit     = %x30-39
 string    = %x22 *char %x22
 char      = unescaped / %x5C escaped
 unescaped = %x20-21 / %x23-5B / %x5D-10FFFF
 escaped   = %x22 ; "    quotation mark  U+0022
           / %x5C ; \    reverse solidus U+005C
           / %x62 ; b    backspace       U+0008
           / %x66 ; f    form feed       U+000C
           / %x6E ; n    line feed       U+000A
           / %x72 ; r    carriage return U+000D
           / %x74 ; t    tab             U+0009
           / %x75.30.30.30 (%x30-37 / %x62 / %x65-66) ; u000X
           / %x75.30.30.31 (%x30-39 / %x61-66)        ; u001X

Signing JSON
~~~~~~~~~~~~

We can now sign a JSON object by encoding it as a sequence of bytes, computing
the signature for that sequence and then adding the signature to the original
JSON object.

Signing Details
+++++++++++++++

JSON is signed by encoding the JSON object without ``signatures`` or keys grouped
as ``unsigned``, using the canonical encoding described above. The JSON bytes are then signed using the
signature algorithm and the signature is encoded using base64 with the padding
stripped. The resulting base64 signature is added to an object under the
*signing key identifier* which is added to the ``signatures`` object under the
name of the server signing it which is added back to the original JSON object
along with the ``unsigned`` object.

The *signing key identifier* is the concatenation of the *signing algorithm*
and a *key version*. The *signing algorithm* identifies the algorithm used to
sign the JSON. The currently support value for *signing algorithm* is
``ed25519`` as implemented by NACL (http://nacl.cr.yp.to/). The *key version*
is used to distinguish between different signing keys used by the same entity.

The ``unsigned`` object and the ``signatures`` object are not covered by the
signature. Therefore intermediate servers can add unsigned data such as timestamps
and additional signatures.


.. code:: json

  {
     "name": "example.org",
     "signing_keys": {
       "ed25519:1": "XSl0kuyvrXNj6A+7/tkrB9sxSbRi08Of5uRhxOqZtEQ"
     },
     "unsigned": {
        "age_ts": 922834800000
     },
     "signatures": {
        "example.org": {
           "ed25519:1": "s76RUgajp8w172am0zQb/iPTHsRnb4SkrzGoeCOSFfcBY2V/1c8QfrmdXHpvnc2jK5BD1WiJIxiMW95fMjK7Bw"
        }
     }
  }

.. code:: python

  def sign_json(json_object, signing_key, signing_name):
      signatures = json_object.pop("signatures", {})
      unsigned = json_object.pop("unsigned", None)

      signed = signing_key.sign(encode_canonical_json(json_object))
      signature_base64 = encode_base64(signed.signature)

      key_id = "%s:%s" % (signing_key.alg, signing_key.version)
      signatures.setdefault(signing_name, {})[key_id] = signature_base64

      json_object["signatures"] = signatures
      if unsigned is not None:
          json_object["unsigned"] = unsigned

      return json_object

Checking for a Signature
++++++++++++++++++++++++

To check if an entity has signed a JSON object a server does the following

1. Checks if the ``signatures`` object contains an entry with the name of the
   entity. If the entry is missing then the check fails.
2. Removes any *signing key identifiers* from the entry with algorithms it
   doesn't understand. If there are no *signing key identifiers* left then the
   check fails.
3. Looks up *verification keys* for the remaining *signing key identifiers*
   either from a local cache or by consulting a trusted key server. If it
   cannot find a *verification key* then the check fails.
4. Decodes the base64 encoded signature bytes. If base64 decoding fails then
   the check fails.
5. Checks the signature bytes using the *verification key*. If this fails then
   the check fails. Otherwise the check succeeds.

Signing Events
~~~~~~~~~~~~~~

Signing events is a more complicated process since servers can choose to redact
non-essential parts of an event. Before signing the event it is encoded as
Canonical JSON and hashed using SHA-256. The resulting hash is then stored
in the event JSON in a ``hash`` object under a ``sha256`` key.

.. code:: python

    def hash_event(event_json_object):
    
        # Keys under "unsigned" can be modified by other servers.
        # They are useful for conveying information like the age of an
        # event that will change in transit.
        # Since they can be modifed we need to exclude them from the hash.
        unsigned = event_json_object.pop("unsigned", None)
        
        # Signatures will depend on the current value of the "hashes" key.
        # We cannot add new hashes without invalidating existing signatures.
        signatures = event_json_object.pop("signatures", None)
        
        # The "hashes" key might contain multiple algorithms if we decide to
        # migrate away from SHA-2. We don't want to include an existing hash
        # output in our hash so we exclude the "hashes" dict from the hash.
        hashes = event_json_object.pop("hashes", {})
        
        # Encode the JSON using a canonical encoding so that we get the same
        # bytes on every server for the same JSON object.
        event_json_bytes = encode_canonical_json(event_json_bytes)
        
        # Add the base64 encoded bytes of the hash to the "hashes" dict.
        hashes["sha256"] = encode_base64(sha256(event_json_bytes).digest())
        
        # Add the "hashes" dict back the event JSON under a "hashes" key.
        event_json_object["hashes"] = hashes
        if unsigned is not None:
            event_json_object["unsigned"] = unsigned
        return event_json_object

The event is then stripped of all non-essential keys both at the top level and
within the ``content`` object. Any top-level keys not in the following list
MUST be removed:

.. code::

    auth_events
    depth
    event_id
    hashes
    membership
    origin
    origin_server_ts
    prev_events
    prev_state
    room_id
    sender
    signatures
    state_key
    type

A new ``content`` object is constructed for the resulting event that contains
only the essential keys of the original ``content`` object. If the original
event lacked a ``content`` object at all, a new empty JSON object is created
for it.

The keys that are considered essential for the ``content`` object depend on the
the ``type`` of the event. These are:

.. code::

    type is "m.room.aliases":
      aliases

    type is "m.room.create":
      creator

    type is "m.room.history_visibility":
      history_visibility

    type is "m.room.join_rules":
      join_rule

    type is "m.room.member":
      membership

    type is "m.room.power_levels":
      ban
      events
      events_default
      kick
      redact
      state_default
      users
      users_default

The resulting stripped object with the new ``content`` object and the original
``hashes`` key is then signed using the JSON signing algorithm outlined below:

.. code:: python

    def sign_event(event_json_object, name, key):
    
        # Make sure the event has a "hashes" key.
        if "hashes" not in event_json_object:
            event_json_object = hash_event(event_json_object)
            
        # Strip all the keys that would be removed if the event was redacted.
        # The hashes are not stripped and cover all the keys in the event.
        # This means that we can tell if any of the non-essential keys are
        # modified or removed.
        stripped_json_object = strip_non_essential_keys(event_json_object)
        
        # Sign the stripped JSON object. The signature only covers the
        # essential keys and the hashes. This means that we can check the
        # signature even if the event is redacted.
        signed_json_object = sign_json(stripped_json_object)
        
        # Copy the signatures from the stripped event to the original event.
        event_json_object["signatures"] = signed_json_oject["signatures"]
        return event_json_object

Servers can then transmit the entire event or the event with the non-essential
keys removed. If the entire event is present, receiving servers can then check
the event by computing the SHA-256 of the event, excluding the ``hash`` object. 
If the keys have been redacted, then the ``hash`` object is included when
calculating the SHA-256 instead.

New hash functions can be introduced by adding additional keys to the ``hash``
object. Since the ``hash`` object cannot be redacted a server shouldn't allow
too many hashes to be listed, otherwise a server might embed illict data within
the ``hash`` object. For similar reasons a server shouldn't allow hash values
that are too long.

.. TODO
  [[TODO(markjh): We might want to specify a maximum number of keys for the
  ``hash`` and we might want to specify the maximum output size of a hash]]
  [[TODO(markjh) We might want to allow the server to omit the output of well
  known hash functions like SHA-256 when none of the keys have been redacted]]

