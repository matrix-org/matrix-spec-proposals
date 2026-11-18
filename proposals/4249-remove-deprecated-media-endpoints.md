# MSC4249: Removal of legacy media endpoints

[MSC3916 (merged)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3916-authentication-for-media.md)
deprecated several `/_matrix/media/*` endpoints in favour of authenticated versions
in proper namespaces, and was released in Matrix 1.11 back in June 2024. The spec's
[deprecation policy](https://spec.matrix.org/v1.13/#deprecation-policy) allows
endpoints in this state to be removed as early as 1 version later.

A majority of the endpoints simply moved to a namespace, however the more-used
endpoints are subject to security concerns ([1](https://github.com/element-hq/synapse/security/advisories/GHSA-gjgr-7834-rhxr),
[2](https://github.com/element-hq/synapse/security/advisories/GHSA-4mhg-xv73-xq2x)).
These security concerns make the endpoints undesirable on most servers, and
implementations have added features to "freeze" the media served over them, as
recommended by MSC3916. The freeze functionality is slowly being [turned on by default](https://github.com/element-hq/synapse/pull/17889)
in some server implementations, and [up for consideration](https://github.com/element-hq/synapse/issues/17950)
to make it a built-in, non-optional, feature.

The diminishing usefulness of the endpoints makes them added noise in the specification,
potentially confusing developers into thinking they can still use the endpoints
when in practice the vast majority of media the user wants to see is only available
over the new, authenticated, endpoints.

This proposal removes the suite of legacy endpoints from the specification, though
does not expect that implementations will follow suite in the near term due to
the endpoints still being used by some users/clients in the wild. The removal is
primarily meant to improve developer experience.

## Proposal

The following deprecated endpoints are removed from the specification:

* [`GET /_matrix/media/v3/preview_url`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixmediav3preview_url)
* [`GET /_matrix/media/v3/config`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixmediav3config)
* [`GET /_matrix/media/v3/download/{serverName}/{mediaId}`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixmediav3downloadservernamemediaid)
* [`GET /_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixmediav3downloadservernamemediaidfilename)
* [`GET /_matrix/media/v3/thumbnail/{serverName}/{mediaId}`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)

Servers which support old specification versions should note the [deprecation policy](https://spec.matrix.org/v1.13/#deprecation-policy),
which requires that servers support later-removed endpoints if the endpoint isn't
removed in those old specification versions. This is primarily expected to affect
implementations like Synapse which maintain backwards compatibility to the very
first specification versions, where possible.

Servers which support old specification versions but still don't want to support
the `/download` and `/thumbnail` endpoints specifically should note that the
specification [allows](https://spec.matrix.org/v1.13/client-server-api/#content-repo-client-behaviour)
them to return `404 M_NOT_FOUND` for those endpoints. This could be extended to
be a hardcoded `return 404 M_NOT_FOUND;` on the deprecated endpoints.

## Potential issues

No such servers are known to exist, however servers which only implement the latest
version of the specification may cause breakage to clients if they remove the
older endpoints too quickly. However, such servers are likely breaking clients
in other ways by doing this.

Servers which support old specification versions will not be able to outright
remove the endpoints, though as noted in the MSC, they can just return 404 for
everything to avoid the problem.

## Alternatives

Instead of recommending that servers return 404 for everything, we could add a
carve-out in the deprecation policy to allow servers to drop the endpoints,
however this would lead to 405 errors instead, which clients might not handle
particularly well (the 405 error for unimplemented endpoints was only introduced
in Matrix 1.6 (2023) while the media download endpoints were introduced in ~2014/2015).

## Security considerations

None relevant. Security considerations were already made with the deprecation of
the endpoints.

## Unstable prefix

No unstable prefix is possible or required for this proposal.

## Dependencies

None relevant.
