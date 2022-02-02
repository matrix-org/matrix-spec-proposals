---
toc_hide: true
---

{{% added-in this=true %}} The event ID is the [reference
hash](/server-server-api#calculating-the-reference-hash-for-an-event) of
the event encoded using a variation of [Unpadded
Base64](/appendices#unpadded-base64) which replaces the 62nd and
63rd characters with `-` and `_` instead of using `+` and `/`. This
matches [RFC4648's definition of URL-safe
base64](https://tools.ietf.org/html/rfc4648#section-5).

Event IDs are still prefixed with `$` and might result in looking like
`$Rqnc-F-dvnEYJTyHq_iKxU2bZ1CI92-kuZq3a5lr5Zg`.
