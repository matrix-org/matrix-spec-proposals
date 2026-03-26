# MSC4426: Handling incoming JSON in the server-server API

The structure of Matrix rooms, and the security of the server-server API,
relies on the calculation and checking of signatures and hashes of data
structures. Examples include:

 * Server-server API requests are
   [authenticated](https://spec.matrix.org/v1.17/server-server-api/#request-authentication)
   by a signature on a data structure containing the details of the request.

 * Room events must be
   [signed](https://spec.matrix.org/v1.17/server-server-api/#signing-events) by
   the homeserver that created them (and, in the case of invite events, by the
   target of the invite), to guard against impersonation.

 * [Event IDs](https://spec.matrix.org/v1.17/rooms/v12/#event-ids) are hashes of
   events, to guard against equivocation (i.e. an attacker sending different
   event contents to different recipients, claiming that they fit in the same
   place in room history).

 * Room events also include a [content
   hash](https://spec.matrix.org/v1.17/server-server-api/#calculating-the-content-hash-for-an-event),
   to guard against tampering of the `contents` (which are not directly
   protected by the signature or Event ID).

All of these processes rely on encoding the data structure in question as
[Canonical JSON](https://spec.matrix.org/v1.17/appendices/#canonical-json), and
feeding the bytes thus obtained into the relevant hashing or signing algorithm.

However, the specification today is not sufficiently clear on how exactly
Canonical JSON should be used. This MSC seeks to provide the necessary
clarifications.

## Proposal

1. When receiving JSON over the server-server API (either in a request or
   response body), server implementations MUST first deserialize the incoming
   JSON into internal data structures. These data structures must be able to
   fully represent the data types permissible in Canonical JSON:
     * strings
     * numbers (or at least, integers in the range `[-(2**53)+1, (2**53)-1]`)
     * objects
     * arrays
     * `true`, `false`, `null`.

   The original JSON MUST then be discarded, and all future operations must be
   based on the deserialized structures. This includes hashing and signature
   checking, which must be done be encoding the deserialized structures as
   Canonical JSON.

   In particular: it is **not** sufficient to construct the Canonical JSON by
   modifying the unparsed JSON data, since this brings the risk of inconsistent
   parsing when the JSON is later parsed. Further discussion of the potential
   problems can be found in the [Appendix](#appendix) below.

2. Implementations MUST guard against duplicate keys in the incoming JSON, and
   ensure that duplicates are dropped before encoding to Canonical JSON. (In
   JSON, a "duplicate key" refers to a JSON object which contains two or more
   entries using the same key; for example: `{"a": 1, "a": 2}`.)

   Implementations are free to implement this requirement by dropping one or
   other duplicate, or by rejecting the JSON as a whole.

   Assuming that the internal data structures mentioned above only allow one
   value per key, no action will be needed by homeservers to comply with this
   requirement, as duplicate keys will be dropped automatically.

   To be explicit: Canonical JSON encodings MUST NOT contain duplicate keys.

3. A clarification to the handling of the [UTF-16
   surrogates](https://www.unicode.org/faq/utf_bom#utf16-2) `U+D800`-`U+DFFF`.
   It is possible that implementations will encounter these codepoints in
   incoming JSON (possibly, though not necessarily, represented with a `\uXXXX`
   escape). For example, the JSON `{"emoji": "\ud83d\ude00"}` contains one possible
   representation of the smiley face, 😀.

   There is no way to legally express the UTF-16 surrogates in Canonical JSON,
   since Canonical JSON forbids the use of `\uXXXX` escapes other than for
   some of the C0 control characters, and Canonical JSON is defined to use
   the UTF-8 encoding (which
   [forbids](https://www.unicode.org/faq/utf_bom#utf8-4) encoding of the
   surrogates).

   To be explicit, then: Canonical JSON MUST NOT encode the UTF-16
   surrogates.

   Valid surrogate pairs SHOULD be decoded to their Unicode code point on
   parsing, and then encoded as a 4-byte UTF-8 sequence when encoding as
   Canonical JSON. JSON containing unpaired surrogates MUST be rejected
   (either on parsing, or when attempting to encode as Canonical JSON).

## Potential issues

TODO

## Alternatives

A number of alternative approaches have been proposed, and are discussed below.

### Require servers to transmit Canonical JSON on the wire

One approach would be to mandate that federation request bodies be serialized
as Canonical JSON. Doing so could bring performance benefits: the signature on
an incoming federation request could be checked much more efficiently than
today.

The benefit is less clear for *response* bodies, since they are not signed in
their own right, though some responses, such as
[`/backfill`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1backfillroomid),
contain event bodies, which are signed, so requiring them to be transmitted as
Canonical JSON could be beneficial.

In any case, the main difficulty is that such a rule has no benefit unless it
can be enforced. Receiving servers would have to verify that incoming JSON is
actually compliant with Canonical JSON, to prevent attacks from malicious
servers. This is not a trivial operation.

Ideally a JSON parser might check that incoming JSON is Canonical during
parsing, but we are not aware of any JSON parsers capable of doing this, and it
is worth noting that any implementation must be absolutely watertight to avoid
the danger of inconsistent parsing between different implementations.

A completely separate pass over the incoming JSON is feasible but not obviously
much more efficient than reserializing the received data as Canonical JSON.

A secondary problem is that this is not the way the Matrix ecosystem works
today. To maintain compatibility with today's servers, we would need to spec a
way to indicate that sending servers are opting in to the requirements (New API
endpoints? Alternative `Content-Encoding` headers?) and implementation would be
a significant amount of work for server maintainers, leading to an opportunity
cost in development in other areas of Matrix.

### Sign/hash the transmitted JSON rather than a canonical representation

Another suggestion is that when receiving JSON, either in request bodies or
room events, servers must validate signatures and hashes against the received
JSON (including any whitespace and unordered object keys) rather than
converting it to a canonical form. Checking signatures and hashes *before*
parsing JSON could bring security and performance benefits.

There are three significant problems with this approach:

- There is a danger of implementations parsing the same event object
  inconsistently; in particular, different JSON deserializers can interpret
  JSON in different ways. One example is with duplicate keys on JSON objects;
  others include floating-point numbers (which may be rounded differently or
  have different range), or acceptance of non-standard JSON such as `NaN` or
  `Infinity`, or even comments or trailing commas.

  Such inconsistency can be used by a malicious server to create a split-brain
  in a room, where different servers accept different subsets of events.

  These effects could in theory be guarded against by forbidding all ambiguous
  JSON constructs, but that's essentially equivalent to requiring Canonical
  JSON on the wire, which is discussed above.

- Such an approach would require servers to keep a copy of the original JSON
  for each event, so that it can be sent on to other servers which will
  themselves need to check the signatures and hashes.

- The [hashing and
  signing](https://spec.matrix.org/v1.17/server-server-api/#signing-events)
  process on room events involves manipulating the event in question (the
  content must be
  [redacted](https://spec.matrix.org/v1.17/rooms/v12/#redactions) to calculate
  the reference hash/event ID, and the `signatures` and `unsigned` properties
  must be removed to calculate the signature). If the incoming JSON is not
  Canonical, there are questions about how to perform this process: in
  particular, how should whitespace before and after removed properties be
  handled?

  Further, manipulating the raw JSON in this way is very unnatural in some
  languages: it is much easer to parse the incoming JSON, manipulate the data,
  and re-serialize.

### Allow servers to canonicalise incoming JSON separately to parsing

Some implementations (for example, Dendrite) operate on incoming JSON at the
byte level to transform it to Canonical JSON, before checking
signatures/hashes. They then retain the *original* JSON, deserializing it where
necessary for later operation. Should we allow such an approach?

The short answer is: if this approach can *provably* give the same result as
that suggested in the proposal, then yes it should be tolerated.

However, the practicalties make it dangerous. It is possible for the
canonicalisation process to remove ambiguities (such as duplicate keys),
allowing a malicious server to construct JSON which passes a signature or hash
check but is then interpreted differently later on.

This is therefore not a recommended approach.

### Allow servers to canonicalise incoming JSON *before* parsing

A variation on the previous approach is to canonicalise the JSON at the byte
level, check the signatures/hashes, and only then deserialize the JSON for
later operations.

This is safer than retaining the original JSON, However, the canonicalisation
process must be absolutely fail-safe to ensure that any possible ambiguities
are removed, to avoid security vulnerablities.

For example: consider a bug where the canonicaliser failed to realise that the
following object contains duplicate keys:

```json
{
   "apple": "foo",
   "appl\u0065": "bar"
}
```

This could obviously lead to a security vulnerability.

It should be *possible* to write a byte-level canonicaliser that is not subject
to such bugs (particularly if we provide a good set of Canonical JSON test
vectors); however implementations which round-trip the JSON via deserialised
objects appear to be more robust.

In short: we're not recommending this approach, for robustness.

### Use an alternative Canonical JSON format

Rather than using a Canonical JSON format specific to Matrix, could we use a
standardised format such as "JSON Canonicalization Scheme" (JCS, specified by
[RFC8785](https://www.rfc-editor.org/rfc/rfc8785.html))?

This is a somewhat orthogonal question, but worth discussing while we're in the
area. Adopting a standardized canonical JSON format might mean that we could
benefit from existing implementations.

For reference, the differences between Matrix's Canonical JSON and JCS are as
follows:

 * JCS forbids the Unicode non-characters, whereas Canonical JSON allows
   them. The non-characters are defined by [Unicode section
   3.4](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G21465)
   to be the codepoints U+nFFFE and U+nFFFF (where n is from 0 to 0x10) and the
   codepoints U+FDD0..U+FDEF".

 * JCS allows floating point numbers, in the full range supported by IEEE 754
   doubles (i.e., up to 1.8e+308), with associated complicated formatting
   rules drawn from the ECMAScript specification.

   CanonicalJSON allows only integers in the range `[-(2**53)+1, (2**53)-1]`,
   forbidding exponential notation and decimal points.

 * The sort order for object keys is subtly different: JCS encodes the keys
   using UTF-16 and sorts the resulting code units, whilst Canonical JSON sorts
   the UTF-32 code points.

   In other words, JCS sorts the smiley face 😀 (U+1F600) before the Hebrew
   letter דּ (U+FB33), whilst Canonical JSON uses the opposite sorting.

It's not obvious that the benefits of switching to an alternative Canonical
JSON format are worthwhile at this time.

### Use an alternative serialization format

We could go further than switching JSON format, and use a completely different
format. A different serialisation format might be more amenable to consistent
parsing, and signature checking.

One candidate for such a format is [DRISL](https://dasl.ing/drisl.html) (a
proposed format based on CBOR which aims specifically for consistent
representation of data).

Such an change remains under consideration, but is left for a future MSC.

## Security considerations

Consistent JSON canonicalisation is central to the security of the Matrix
protocol. It is therefore critical that the specification be clear about
expected behaviour, and that implementations match those expectations.

## Unstable prefix

N/A

## Dependencies

None

## Appendix

- we assume that rejecting questionable JSON is much, much safer than accepting
  it
- there are no safe CanonicalJSON decoders
- examples of attacks
- examples of suitable implementations:
  - Go: unmarshal into `interface{}`
  - Python: json.load
  - Rust: deserialize to serde_json::Value
