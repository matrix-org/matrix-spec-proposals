# MSC3442: move the `prev_content` key to `unsigned`

Background: the Client-Server API specification
[documents](https://matrix.org/docs/spec/client_server/r0.6.1#state-event-fields)
a `prev_content` property to be included on state events. It gives the
`content` of the previous state event with the same `type` and `state_key`.

This property does not form part of the "raw" event as sent to federating
homeservers via the Server-Server API; it is added to events served over the
Client-Server API as a service to those clients.

Adding properties at the top level of the event in this way is confusing: it
makes it difficult to understand which properties are part of the raw event,
and which added retrospectively.

It is also inconsistent with other properties which are added by the local
homeserver such as `age`, `redacted_because` and `transaction_id`, which are
returned under `unsigned`: see https://matrix.org/docs/spec/client_server/r0.6.1#room-event-fields.

## Further background information

1. The specification for the [`GET
   /_matrix/client/r0/notifications`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-notifications)
   API is unusual in that it requires `prev_content` to be returned under
   `unsigned`.

2. In general, in addition to returning `prev_content` at the top level as
   specified, Synapse *also* returns it under `unsigned`, as proposed here.

   The exceptions to this are `GET /notifications` and `GET /sync`, where
   Synapse returns `prev_content` *only* under `unsigned`. As noted above, this
   is compliant with the spec for `/notifications`, but appears to be a spec
   violation for `/sync`.

3. Dendrite returns `prev_content` *only* under `unsigned` (and is therefore
   theoretically in violation of the spec).

## Proposal

It is proposed that the specification be updated to move the `prev_content`
property to the `unsigned` object, bringing it in line with `age`,
`redacted_because` and `transaction_id`.

This will affect:
 * Events returned by the Client-Server API.
 * Events sent to Application Services by the Application Services API.

## Potential issues

The proposed change may break compatibility with existing clients and
Application Services.

In practice, any client supporting Dendrite or `/sync` requests via Synapse
must already support the new location, so this is not a breaking change for
such clients. There may be Application Services which rely on `prev_content` at
the top level; however these can be safely updated to use the new location,
since Synapse populates both locations.

The problem can be further mitigated by homeservers populating the key at
*both* locations for as long as they support older versions of the
specification, as Synapse does today.

## Alternatives

1. We could double-down on the existing situation and require that
   `prev_content` always be populated at the top level (possibly including
   `/notifications`).  That is unattractive for the reasons set out in the
   introduction to this proposal. Furthermore, in practice it will introduce
   *more* compatibility problems, due to the implementations which currently do
   not comply with the spec.

2. We could require that homeservers populate the property at *both*
   locations. However, setting aside the added complexity for homeserver
   implementations, it also increases the chances of a situation as follows:

    * Some clients use one property, some use another.
    * A homeserver developer tests against a subset of clients, all of which use
      one property.
    * In consequence, some clients are incompatible with some homeservers.

## Security considerations

When an event is sent over federation, the sending homeserver can freely add
properties to the `unsigned` object, without them being covered by the
hashes or signatures. Some homeserver implementations (including Synapse)
will then pass any such properties on to clients and application services.

In principle then, a malicious or buggy homeserver implementation could add an
incorrect `prev_content` property under `unsigned`, and send it over
federation. A receiving homeserver, implementing the *current* specification,
might pass that property straight through to a client, and the receiving client
would be unable to tell that it was actually incorrectly populated by the
remote homeserver.

This is a more general problem that exists today, and which requires a more
general solution to `unsigned` objects - see
https://github.com/matrix-org/synapse/issues/11080.  This proposal does not
materially affect the problem.

## Unstable prefix

No unstable prefix is required, since the behaviour proposed is already
implemented by both Synapse and Dendrite.
