# MSC3585: Allow the base event to be omitted from `/federation/v1/event_auth` response

The [specification for `GET
/_matrix/federation/v1/event_auth/{roomId}/{eventId}`](https://spec.matrix.org/unstable/server-server-api/#get_matrixfederationv1event_authroomideventid)
does not explicitly say whether the event with the specified `eventId` should
be included in the response.

In cases of such ambiguity, we look to historical precedent, where we see that
Synapse does return that event (see `include_given=True` in
[`FederationHandler.on_event_auth`](https://github.com/matrix-org/synapse/blob/v1.49.2/synapse/handlers/federation.py#L423)). It
has been that wasy since at least
[synapse#2247](https://github.com/matrix-org/synapse/pull/2247), predating the
inclusion of this endpoint in the spec.

The de-facto spec is therefore that `eventId` *should* be returned. However,
there is no good reason to return it: the only reason why a remote server would
call this endpoint is if it already has a copy of the event but is missing some
of its auth events. Indeed, Synapse includes code to ignore that event where it
is returned: https://github.com/matrix-org/synapse/blob/v1.49.2/synapse/handlers/federation_event.py#L1710-L1711.

## Proposal

The specification for `GET
/_matrix/federation/v1/event_auth/{roomId}/{eventId}` should be clarified to
say that `eventId` itself should not be returned.

## Potential issues

In theory this is a breaking change; although Synapse does not depend on
`eventId` being returned, it is possible that this will cause problems on other
implementations for some reason. However, as above, there is no reason for a
homeserver implementation to call `/event_auth` unless it already has a copy of
the event, so this is judged to be a minor risk.

In addition, Conduit is known to elide the requested event already (see
[server_server.rs](https://gitlab.com/famedly/conduit/-/blob/9b57c89df6861eef97b8615ff22433f26c43a377/src/server_server.rs#L2432))
so the potential for incompatibility already exists.

## Alternatives

Alternatives include:

 * double-down on requiring `eventId` to be returned. This seems like a
   retrograde step.
 * introduce a way in which implementations can opt-in to the omission of
   `eventId` (for example, via a query parameter, or with a new version of the
   `/event_auth` endpoint). This seems overengineered.

## Security considerations

None foreseen.

## Unstable prefix

No unstable prefix is proposed.

## Dependencies

None.
