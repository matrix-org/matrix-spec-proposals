# MSC4158: MatrixRTC focus information in .well-known

MatrixRTC can use different infrastructures.
Until now backend infrastructure is provided by the homeserver. To also conform to this pattern
for MatrixRTC the most reasonable to place for the MatrixRTC focus information is the homeserver.
This puts the homeserver admin in control what infrastructure their users use for calls.
(The same as the homeserver now does for Matrix events)

> [!NOTE]
> A **infrastructure** in this context can be anything that can serve as the backend for a
> MatrixRTC session. In most cases this is a SFU. But also a full mesh implementation could
> be an infrastructure. Not all kind of infrastructure require a way of sourcing a backend resource
> (e.g. full-mesh). In this MSC we only refer to infrastructure where it is necessary to have access to additional
> data to participate in the MatrixRTC session.

With this proposal homeservers are invited to host and expose their infrastrucuture via the `.well-known` similar to how
they historically were invited to provide a turn server.

> [!NOTE]
> To get a better understanding of the parts and their responsibilities for a working
> MatrixRTC setup see:
>
> https://github.com/matrix-org/matrix-spec-proposals/pull/4143
>
> The MSC is phrased with the expectation that the reader knows about MSC4143 to minimize redundencies.

## Proposal

The proposal is to reserve a key in the homeserver client `.well-known` which can expose a sorted list
of infrastructure description objects. These objects are called `FocusInfo`.

```json
"m.rtc_foci": [
{
  "type":"any-focus-type",
  "additional-type-specific-field":"https://my_livekit_focus.domain",
  "another-additional-type-specific-field":["with", "Array", "type"]
},
{
  "type":"livekit",
  "livekit_service_url":"https://my_livekit_focus.domain"
}
]
```

## Potential issues

The `.well-known` is publicly readable, hence everyone can read and know about the infrastructure which could
lead to resource "stealing".
Each infrastructure however has their own authentication mechanism defined in the infrastructure specification.
Those mechanisms for instance can use a service to interact with the homeserver and based on that decide to allow users
to use the infrastructure.

This is defined in the respective infrastructure MSC.

## Alternatives

This MSC proposes to combine the MatrixRTC backend infrastructure with the homeserver.
Other sources where the backend could be sourced from are:

- A separate system not associated with Matrix accounts.
  (you would need a Matrix account + a "Livekit provider" account for example)
- The client could bring its own backend link.
- A centralized solution.

The centralized solution would not fit to Matrix. A separate system would match the distributed
nature of Matrix but would not match the user experience goals for MatrixRTC calls.

The client defining the SFU that is used, is the current solution. This causes the issue, that clients
in general are less distributed than homeservers. There is only a limited set of clients that a large
percentage of users use.
Using this as the source for the infrastructure would result in just a handful of very large infrastructure
hosts.
This is harder to scale and it is harder to justify who is covering the costs. (For Matrix homeservers, this
is an already solved problem where there are individuals, communities and institutions that have their own individual
solutions and answers for how and why they provide the infrastructure.)

## Security considerations

With the addition of the `.well-known` key no issues are idetified yet. There are lots of considerations
to be made with the actual exposure/authentication of the infrastructure.
Those are made in the respective infrastrucuture MSC's.

## Unstable prefix

While this MSC is not considered stable, use `org.matrix.msc4158.` instead of `m.`.

## Dependencies/Relations

This MSC relates with [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143). It does not
depend on it since exposing the Foci list also works without using MatrixRTC but it also only makes sense when there
is a specification in how to use it. It makes sense to discuss merging this before MSC4143 however so that
homeservers can already prepare infrastructure and a larger adoption of MatrixRTC calls is possible to be
distributed on multiple backends before things break down on the client provided backends.
