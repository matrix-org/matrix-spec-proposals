# MSC1956: Integrations API

"Integration managers" are applications that help clients bring integrations (bridges, bots, widgets, etc)
to users. This can be for things like setting up an IRC bridge or adding a Giphy bot to the room. Integration
managers have been popularized by Riot, however other clients also have support for concept as well although
to a lesser extent.

Integration managers are important to the Matrix ecosystem as they help abstract away the underlying integration
and allow providers of the integratiosn to manage access to them. For example, there are multiple XMPP bridges
available in the Matrix ecosystem and an integration manager is in the best position to handle the different APIs
each exposes, generalizing the API exposed to clients. Similarly, the integration manager could charge for access
to specific integrations such as sticker packs or per-user access to a bridge.

This proposal introduces a new Matrix API: the "Integrations API" (or "Integrations Specification") which covers
how integration managers and integrations themselves cooperate with clients. Typically these kinds of extensions
to Matrix would be put into the Client-Server API, however the integration manager is not typically the same as
the user's homeserver and is therefore ideal to be specified indepdently.


## Glossary

Due to the introduction of a new API, some common terminology is to be established:

An **Integration Manager** (or *Integrations Manager*, or simply *Manager*) is an application which assists users
and/or clients in setting up *Integrations*.

**Integrations** are something the *Integration Manager* exposes, such as *Bots*, *Bridges*, and *Widgets*.

A **Bot** is typically a Matrix user which provides a utility service, such as Github Notifications or reaction
GIFs.

A **Bridge** is typically an Application Service which proxies events between Matrix and a 3rd party platform,
such as IRC. Bridges may also operate in a single direction and have other features like *Puppeting*, which are
not covered here. For information on the various types of bridging, please see the
[reference guide](https://matrix.org/docs/guides/types-of-bridging.html).

**Widgets** are embedded web applications in a Matrix client. These are split into two types: **Account Widgets**
and **Room Widgets**. *Account Widgets* are specific to a particular Matrix user and not shared with other users
whereas *Room Widgets* are shared with the members of the room they reside in.

A **Trusted Integration Manager** is an *Integration Manager* which the client has deemed trustworthy by its own
criteria. For example, this may be defined as being known as an account widget, discovered by .well-known, or
being set in the client's configuration. By proxy, an **Untrusted Integration Manager** is the opposite.

The **Integration Manager API** is the set of HTTP endpoints which clients can use to interact with a given
*Integration Manager*.

The **Widget API** is the set of `postMessage` APIs which are used for clients and *Widgets* to communicate with
each other when embedded.

The **Integrations API** is the set of both the *Integration Manager API* and *Widget API* as well as any other
details which affect *Widgets* or *Integration Managers* and their interactions with clients.


## Proposal

A new Integrations API be introduced into Matrix which consists of the components listed in this proposal.

**Components**:

* API Standards (see later section of this proposal)
* Discovery - [MSC1957](https://github.com/matrix-org/matrix-doc/pull/1957)
* Widgets
  * Includes [MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236)
  * Includes [MSC1958](https://github.com/matrix-org/matrix-doc/pull/1958)
  * Includes [MSC1960](https://github.com/matrix-org/matrix-doc/pull/1960)
  * MSC for extensions and alterations not yet defined
    * ***TODO: MSC for each or group them by subject?***
  * The first version of the Widget API is to be `0.1.0`, with the existing `0.0.x` versions being flagged as
    development versions which are otherwise unspecified.
* Sticker picker and custom emoji
  * Includes [MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951)
  * Includes [MSC1959](https://github.com/matrix-org/matrix-doc/pull/1959)
* Authentication in integration managers - [MSC1961](https://github.com/matrix-org/matrix-doc/pull/1961)
* Terms of service / policies - [MSC2140](https://github.com/matrix-org/matrix-doc/pull/2140)
* Integration manager specific APIs
  * MSC and scope not yet defined

***TODO: Define where paid integrations, OAuth, etc all fit if at all.***
***TODO: Finalize what goes into this spec.***


## Proposed API standards

All HTTP APIs in this specification must consume and produce JSON unless otherwise indicated. Errors emitted by
these APIs should follow the standard error responses defined by other APIs in Matrix. Some common error responses
implementations may encounter are:
* `403` `{"errcode":"M_UNKNOWN_TOKEN","error":"Invalid token"}`
* `400` `{"errcode":"M_MISSING_PARAM","error":"Missing 'matrix_server_name'"}`
* `400` `{"errcode":"M_INVALID_PARAM","error":"'matrix_server_name' must be a string"}`
* `400` `{"errcode":"M_NOT_FOUND","error":"The sharable URL did not resolve to a pack"}`


## Tradeoffs

Specifying a whole new set of APIs means introducing another complex system into Matrix, potentially causing
confusion or concerns about the architecture of Matrix or its implementations. It is believed by the author that
having a dedicated set of APIs for this system within Matrix is important to reduce the burden on homeserver
authors and to support client authors in their ambitions to grow Matrix through bridges, bots, etc.

It is also questionable if integration managers should be a concept within Matrix as the APIs which clients would
be interacting with can be generically exposed by the integrations themselves without the need for a manager. The
manager's role in this specification is to provide clients with the opportunity to quickly get themselves connected
with the larger Matrix ecossytem without adding the burden of designing their own interface. The majority of the
APIs are defined such that a client is able to put their own UI on top of the manager instead of embedding that
manager if desired by the client.


## Potential issues

Clients which support today's ecosystem of integration managers have a lot of work to do to support this proposal
in all its parts. In addition, integration managers themselves have a decent amount of work in order to become
compliant. The exercise of this proposal is not to make development harder for the projects in the ecosystem, but
to standardize on a set of APIs which bridge the gap between managers while also patching inadequacies in the current
systems.


## Security considerations

Each proposal which branches off this proposal has its own set of security considerations. As a whole, clients are
expected to make decisions on which integration managers are trusted, and integration managers are encouraged to do
the same with clients and integrations.


## Conclusion / TLDR

Add a new API specification for interactions between integrations and clients. APIs for interactions between the
integrations and managers is undefined and left as an implementation detail.
