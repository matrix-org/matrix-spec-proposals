Add cross-signing:

- Add properties to the response of ``GET /user/keys`` and ``GET
  /user/devices/{userId}``.
- The ``m.device_list_update`` EDU is sent when a device gets a new signature.
- A new ``m.signing_key_update`` EDU is sent when a user's cross-signing keys
  are changed.

per [MSC1756](https://github.com/matrix-org/matrix-doc/pull/1756).
