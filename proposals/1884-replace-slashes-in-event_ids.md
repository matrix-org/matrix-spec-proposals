# MSC1884: Proposal to replace slashes in event IDs

[MSC1659](https://github.com/matrix-org/matrix-doc/pull/1659) mandated that,
starting in version 3 rooms, event IDs must be calculated as a base64-encoding
of a hash. This implies that event IDs may contain any character in the
standard Base64 alphabet, which notably includes the slash character, `/`.

Event IDs are often embedded in URI paths, and since the slash character is
used as a separator in URI paths, this presents a problem. The immediate
solution is to ensure that event IDs are URL-encoded, so that `/` is instead
represented as `%2F`. However, this is not entirely satisfactory for a number
of reasons:

 * There exist a number of client (and possibly server) implementations which
   do not currently URL-encode such parameters; these are therefore broken by
   such event IDs and must be updated. Furthermore, all future client
   implementers must remember to do the encoding correctly.

 * Even if client implementations do rembember to URL-encode their parameters,
   they may not do it correctly: many URL-encoding implementations may be
   intended to encode parameters in the query-string (which can of course
   contain literal slashes) rather tha the path component.

 * Some proxy software may treat `%2F` specially: for instance, Apache, when
   configured as a reverse-proxy, will reject requests for a path containing
   `%2F` unless it is also configured with `nocanon`. Again this means that
   existing setups will be broken by this change, and it is a trap for new
   users of the software.

## Proposal

This MSC proposes that we should introduce a new room version, in which event
IDs are encoded using the [URL-safe Base64
encoding](https://tools.ietf.org/html/rfc4648#section-5) (which uses `-` and
`_` as the 62nd and 63rd characters instead of `+` and `/`).

## Counterarguments

1. Inconsistency. Base64 encoding is used heavily elsewhere in the matrix
   protocol and in all cases the standard encoding is used (though with some
   variation as to the inclusion of padding characters). Further, SHA256 hashes
   are used in a number of places and are universally included with standard,
   unpadded Base64.

   Changing event IDs alone would therefore leave us with a confusing mix of
   encodings.

   A potential extension would be to change *all* Base64 encodings to be
   URL-safe. This would address the inconsistency. However, it feels like a
   large job which would span the entire matrix ecosystem (far larger than
   updating clients to URL-encode their URL prarameters), and again the
   situation would be confusing while the transition was in progress.

2. Incompleteness. Event IDs are certainly not the only identifier which can
   contain slashes - Room aliases, Room IDs, Group IDs, User IDs [1], and state
   keys can all contain slashes, as well as a number of identifiers whose
   grammars are currently underspecified (eg transaction ids, event types,
   device IDs). (Indeed, there was nothing preventing Event IDs from containing
   slashes before room v3 - it just happened that Synapse used an algorithm
   which didn't generate them).

   All of these other identifiers can appear in URLs in either or both the
   client-server or server-server APIs, and all have the potential to cause
   misbehaviour if software does not correctly URL-encode them.

   It can be argued that it is better for software to fail 50% of the time [2]
   so that it can be fixed than it is to fail only on edge-cases or, worse,
   when deliberately provoked by a malicious or "curious" actor.

   Of course, an alternative is to modify the grammars of all of these
   identifiers to forbid slashes.

[1] Discussion remains open as to whether allowing slashes in User IDs was a
good idea.

[2] 48% of random 32-byte sequences will contain a slash when Base64-encoded.

## Alternatives

An alternative would be to modify all REST endpoints to use query or body
parameters instead of path parameters.  This would of course be a significant
and incompatible change, but it would also bring the benefit of solving a
common problem where forgetting to use `nocanon` in a reverse-proxy
configuration [breaks
federation](https://github.com/matrix-org/synapse/issues/3294) (though other
solutions to that are also possible).

## Conclusion

It's unclear to me that changing the format of event IDs alone solves any
problems.
