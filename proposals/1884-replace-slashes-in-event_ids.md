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

 * The act of escaping and unescaping slash characters when manually calling
   the API during devops work becomes an constant and annoying chore which
   is entirely avoidable.  Whenever using tools like `curl` and `grep` or
   manipulating SQL, developers will have to constantly keep in mind whether
   they are dealing with escaped or unescaped IDs, and manually convert between
   the two as needed. This will only get worse with further keys-as-IDs
   landing with MSC1228.

 * There exist a number of client (and possibly server) implementations which
   do not currently URL-encode such parameters; these are therefore broken by
   such event IDs and must be updated. Furthermore, all future client
   implementers must remember to do the encoding correctly.

 * Even if client implementations do remember to URL-encode their parameters,
   they may not do it correctly: many URL-encoding implementations may be
   intended to encode parameters in the query-string (which can of course
   contain literal slashes) rather than the path component.

 * Some proxy software may treat `%2F` specially: for instance, Apache, when
   configured as a reverse-proxy, will reject requests for a path containing
   `%2F` unless it is also configured with `nocanon`. Again this means that
   existing setups will be broken by this change, and it is a trap for new
   users of the software.

 * Cosmetically, URL-escaping base64 in otherwise-constant-length IDs results
   in variable length IDs, making it harder to visually scan lists of IDs and
   manipulate them in columnar form when doing devops work.

 * Those developing against the CS API might reasonably expect us to use
   URL-safe identifiers in URLs where available, rather than deliberately
   choosing non-URL-safe IDs, which could be seen as developer-unfriendly.

## Proposal

This MSC proposes that we should introduce a new room version, in which event
IDs are encoded using the [URL-safe Base64
encoding](https://tools.ietf.org/html/rfc4648#section-5) (which uses `-` and
`_` as the 62nd and 63rd characters instead of `+` and `/`).

We will then aim to use URL-safe Base64 encoding across Matrix in future,
such that typical CS API developers should be able to safely assume
that for all common cases (including upcoming MSC1228 identifiers) they should
use URL-safe Base64 when decoding base64 strings.

The exception would be for E2EE data (device keys and signatures etc) which
currently use normal Base64 with no easy mechanism to migrate to a new encoding.
Given E2EE development is rare and requires expert skills, it seems acceptable
to expect E2EE developers to be able to use the right encoding without tripping
up significantly.

Similarly, the S2S API could continue to use standard base64-encoded hashes and
signatures in the places it does today, given they are only exposed to S2S API
developers who are necessarily expert and should be able to correctly pick the
right encoding.

## Counterarguments

1. Inconsistency. Base64 encoding is used heavily elsewhere in the matrix
   protocol and in all cases the standard encoding is used (though with some
   variation as to the inclusion of padding characters). Further, SHA256 hashes
   are used in a number of places and are universally included with standard,
   unpadded Base64.

   Changing event IDs alone would therefore leave us with a confusing mix of
   encodings.

   However, the current uses of standard Base64 encodings are not exposed to
   common CS API developers, and so whilst this might be slightly confusing
   for the minority of expert homeserver developers, the confusion does not
   exist today for client developers (except those implementing E2EE).
   Therefore it seems safe to standardise on URL-safe Base64 for identifiers
   exposed to the client developers, who form by far the majority of the
   Matrix ecosystem today, and expect as simple an API as possible.

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

   The counter-counterargument to this is that it is of course best practice
   for implementations is to URL-escape any IDs used in URLs, and human-selected
   IDs such as Room aliases, Group IDs, Matrix user IDs etc apply an adequate
   forcing function already to remind developers to do this.  However,
   it doesn't follow that we should then also deliberately pick URL-unsafe
   encodings for machine-selected IDs - the argument that it is better for software
   to fail 50% of the time to force a fix is irrelevant when the possibility
   exists for the software to fail 0% of the time in the first place by picking
   an identifier format which cannot fail.

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

There are two main questions here:

 1. Whether it's worth forcing CS API developers to juggle escaping of
    machine-selected IDs during manual use of the API in order to remind them
    to escape all variables in their URIs correctly when writing code.

 2. Whether it's a significant problem for E2EE & SS API developers to have to
    handle strings which are a mix of standard Base64 and URL-safe Base64
    encodings.

Both of these are a subjective judgement call.

Given we wish the CS API particularly to be as easy as possible for manual
use, it feels that we should find another way to encourage developers to
escape variables in their URLs in general - e.g. by recommending that
developers test their clients against a 'torture room' full of exotic IDs and
data, or by improving warnings in the spec... rather than (ab)using
machine-selected IDs as a reminder.

Meanwhile, given we have many more people manually invoking the CS API than
developing on the SS or E2EE APIs, and we wish to make the CS API particularly
easy for developers to manually invoke, it feels we should not prioritise
consistency of encodings for SS/E2EE developers over the usability of the CS
API.

Therefore, on balance, it seems plausible that changing the format of event IDs
does solve sufficient problems to make it desirable.
