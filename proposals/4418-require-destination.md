# MSC4418: Make `destination` a required server authentication field

Currently the server to server authentication scheme allows `destination` to be optional for
backwards-compatibility, however most homeserver implementations today no longer permit this.
It additionally makes vHosting more difficult to implement and utilize.

## Proposal

Require `destination` for authenticated federation requests.

## Potential issues

Older homeservers may be unable to federate with servers that implement this MSC,
however all major implementations have caught up by now, and any older Synapse
versions that don't send the field are likely riddled with security holes.

## Alternatives

None?

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.
