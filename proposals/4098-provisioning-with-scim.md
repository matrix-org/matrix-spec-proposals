# MSC4098: User account provisioning using SCIM

This proposal suggests to use the [SCIM protocol](https://en.wikipedia.org/wiki/System_for_Cross-domain_Identity_Management) as a standard way to achieve
user account [provisioning](https://en.wikipedia.org/wiki/Account_provisioning), fix several use cases uncovered
by the specification, and in the end help reduce friction for system administrators managing Matrix servers.

## Provisioning

In short, *provisioning* is a way for different services to exchange information about users and groups.

Organizations often rely on Identity and Access Management (IAM) software to centralize information about their users.
IAM servers often implement protocols to communicate with services, such as OpenID Connect (OIDC) to provide unique
authentication with protocols like OpenID Connect (OIDC).

### Use cases

A common practice is to dynamically create users on services when they first log-in with OIDC,
based on the data provided by the [authentication tokens](https://tools.ietf.org/html/rfc9068)
or a dedicated [endpoint at the IAM](https://openid.net/specs/openid-connect-core-1_0.html#UserInfo) server.
However this usage has limitations.

Several real-world Matrix use cases would benefit having a provisioning protocol implemented,
so IAM software and Matrix servers could communicate together and reduce friction for end users and system
administrators.

#### Centralized user creation

A new employee joins an organization.
The team the employee will join wants to prepare their collaboration tools,
so everything is set up for the employee's first day of work.
The team contacts  the organization system administrators who create a user profile in the IAM software.
- Without a provisioning protocol, the new employee's profile will only be created on the collaboration tools at the
employee first log-in. Until then, the team cannot share files, send welcome emails etc. or in case of a Matrix server,
invite them in a discussion or a space. This is unless system administrators manually perform the user creation on
all the services.
- With a provisioning protocol, when the employee account is created on the IAM server,
 it reaches the different services to push the new employee profile. The team can share
anything they need before the new employee has ever logged in.

#### Centralized user update

An employee wishes to update their display name on their organization IAM server.
- Without a provisioning protocol, they will need to log-out and log-in again so the new display name is read from their
  authentication token.
- With a provisioning protocol, the IAM server instantly communicate the new display name to every services.

#### Centralized user deletion

An employee leaves the organization, the system administrators will remove or de-activate
the user profile from the IAM server, that will immediately prevent the leaving employee to log-in at any service.
The employee may still have data left on all those services (such as files, emails, personal
profile information etc.), that sooner or later will be needed
to remove, either because of disk usage or privacy reasons.
- Without a provisioning protocol, the system administrators
need to manually perform the account removal operation on all the services the employee have been using. This can
be cumbersome depending on the quantity of users and services.
- With a provisioning protocol, the modifications on the user profile
are automacally repercuted on all the services, so the system administrators only need to do the removal once on
the IAM server.

### A provisioning protocol

To paraphrase [MSC1779](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1779-open-governance.md),
*"interoperability is better than fragmentation*".

Synapse implements its own provisioning protocol with its
[Users admin API](https://matrix-org.github.io/synapse/latest/admin_api/user_admin_api.html).
While this is useful from the point of view of the synapse ecosystem, this has limitations from an IAM server - or system
administrator - perspective.

#### A common protocol for the Matrix ecosystem

Without standard protocol, when an IAM software is connected to multiple services,
it implies that it implements a custom provisioning protocol for each one of those services,
multiplicating the maintenance burden and the room for bugs.
Having a common provisioning protocol defined in the Matrix specification would at least reduce the effort for making
IAM servers provisioning Matrix servers, since the protocol would need to be implemented once for all the Matrix
servers.

In addition, this would ensure some interoperability for other user management tools.
For instance, tools of the kind of [synapse-admin](https://github.com/Awesome-Technologies/synapse-admin) could be used
to manage users for any Matrix servers not plugged to an IAM server.

#### A standard protocol for the Matrix ecosystem

Adopting an existing standard provisioning protocol would allow IAM software to not implement dedicated connectors to be able to
manage Matrix server users. Possibly, provisioning would come for free in IAM software already implementing those
protocols.
In the end, that would reduce the friction for system administrators.
Plus, choosing a battle tested standard will save design time and avoid reinventing the wheel.

### The SCIM protocol

System for Cross-domain Identity Management, or SCIM, is a protocol that normalizes users and groups provisioning.
The [SCIM IETF working group](https://datatracker.ietf.org/wg/scim/about/) wrote
[RFC7642](https://www.rfc-editor.org/rfc/rfc7642), [RFC7643](https://www.rfc-editor.org/rfc/rfc7643) and
[RFC7644](https://www.rfc-editor.org/rfc/rfc7644) which details the protocol.
The WG is alive and there are [several drafts currently being worked](https://datatracker.ietf.org/wg/scim/documents/).

A SCIM implementation basically consists in a set of HTTP endpoints used to read or edit objects such as *Users* and
*Groups*, plus a few metadata endpoints. The different standard HTTP methods (GET, POST, PUT, PATCH, DELETE) are used
depending on the intended actions on the objects.

SCIM is to *provisioning* what OpenID Connect (OIDC) is to *authentication*, and is generally implemented in Identity
and Authorization Management (IAM) software.

A lot of scenarios where SCIM is pertinent are available on [RFC7642](https://www.rfc-editor.org/rfc/rfc7642).

#### Real world SCIM implementations

While being almost 10 years old, SCIM suffers from not being very popular yet (at least, not as much as protocols like
OIDC).
It is facing a chicken and egg issue, where services are waiting for IAM servers to implement SCIM before they find useful to
implement it in return, and vice-versa. However, SCIM seems to gain in popularity lately.
Here is a quick state of the art of the current SCIM implementations in famous IAM servers.

- [Auth0](https://auth0.com/docs/authenticate/protocols/scim) ✅
- Authelia ❌
- [Authentik](https://goauthentik.io/docs/providers/scim/) ✅
- [Authentic2](https://dev.entrouvert.org/issues/70751) ❌
- [Canaille](https://canaille.readthedocs.io/en/latest/specifications.html#scim) ❌
- [CAS](https://apereo.github.io/cas/7.0.x/integration/SCIM-Provisioning.html) ✅
- Connect2id ❌
- [Gluu](https://gluu.org/docs/gluu-server/4.0/api-guide/scim-api/) ✅
- [Hydra](https://github.com/ory/hydra/issues/235) ❌
- Keycloak, via plugins [scim-for-keycloak](https://scim-for-keycloak.de/)
  or [keycloak-scim](https://lab.libreho.st/libre.sh/scim/keycloak-scim) ✅
- LemonLDAP ❌
- [Okta](https://developer.okta.com/docs/reference/scim/scim-20/) ✅

## Proposal

### Endpoints

[RFC7644](https://www.rfc-editor.org/rfc/rfc7644) defines different endpoints.
This proposal is to implement the following endpoints:

- [User](https://www.rfc-editor.org/rfc/rfc7643#section-4.1) endpoint, which are used to manage users.
  - creation with [POST](https://www.rfc-editor.org/rfc/rfc7644#section-3.3)
  - retrieval with [GET](https://www.rfc-editor.org/rfc/rfc7644#section-3.4)
  - replacement with [PUT](https://www.rfc-editor.org/rfc/rfc7644#section-3.5.1)
  - deletion with [DELETE](https://www.rfc-editor.org/rfc/rfc7644#section-3.6)
- [Service Provider Configuration endpoints](https://www.rfc-editor.org/rfc/rfc7644#section-4), which display metadata
  about the SCIM implementation.
  - `/ServiceProviderConfig`
  - `/Schemas`
  - `/ResourceTypes`

Other endpoints such as [Bulk operations](https://www.rfc-editor.org/rfc/rfc7644#section-3.7)
or [Search](https://www.rfc-editor.org/rfc/rfc7644#section-3.4.3), or methods like
[PATCH](https://www.rfc-editor.org/rfc/rfc7644#section-3.5.2), are considered optional.

### User attributes matching

The SCIM User attributes are detailed on [RFC7643](https://www.rfc-editor.org/rfc/rfc7643#section-4.1).
Some attributes easily fits between the SCIM and the Matrix specifications:

| SCIM         | Matrix        |
| ------------ | ------------- |
| userName     | username      |
| password     | [password](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3accountpassword) |
| emails       | 3pid email    |
| phoneNumbers | 3pid msisdn   |
| displayName  | display name  |
| photos       | avatar_url    |
| active       | [deactivate](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3accountdeactivate) |

The [Matrix specification on profiles](https://spec.matrix.org/latest/#profiles) indicates that
*Users may publish arbitrary key/value data associated with their account*, and on its own side, SCIM is very feature
complete and leaves room for additional attributes with its [extension
model](https://www.rfc-editor.org/rfc/rfc7643#section-3.3).

In the end, the exact attribute matching implementation should be left to the Matrix server, in a similar fashion
than synapse achieves [mapping from attributes from SSO
providers](https://matrix-org.github.io/synapse/latest/sso_mapping_providers.html).

### Authentication

The SCIM protocol [supports all the common HTTP authentication
methods](https://www.rfc-editor.org/rfc/rfc7644#section-2), so the provisioning endpoints should use the same user
[authentication methods](https://spec.matrix.org/v1.9/client-server-api/#client-authentication) than the rest of the
Matrix server.

As indicated in the [Server Administration](https://spec.matrix.org/v1.9/client-server-api/#server-administration)
paragraph, *Server-local administrator privileges are not specified in this document.* It could rely on a
local *administrator flags*, or a SCIM [entitlements](https://www.rfc-editor.org/rfc/rfc7643#section-4.1) attribute
values for instance.

## Potential issues

The scope of the SCIM User model and the Matrix User model might not perfectly match, however the SCIM [extension
model](https://www.rfc-editor.org/rfc/rfc7643#section-3.3) can be used in the future to standardize more attributes of
the User model in the Matrix specification.

## Alternatives

SCIM appears to be the only existing relevant user account provisioning protocol.

An alternative could be for Matrix to define its own provisioning protocol. This would bring standardization between
Matrix servers, but would not be as useful for IAM servers attached to a large number of services, since they would still need
to implement the Matrix provisioning protocol.

## Security considerations

SCIM security considerations are related in [a dedicated paragraph](https://www.rfc-editor.org/rfc/rfc7644#section-7) in
RFC7644.

## Unstable prefix

The unstable prefix to use for the root SCIM endpoint is `/_matrix/client/unstable/coop.yaal/scim/`.
The stable prefix to use for the root SCIM endpoint is `/_scim/`.
[RFC7644 §3.13](https://www.rfc-editor.org/rfc/rfc7644#section-3.13) indicates that endpoint versioning is optional.

## Dependencies

This MSC has no dependency.

It would solve [matrix-spec#23](https://github.com/matrix-org/matrix-spec/issues/23) and
[matrix-spec#228](https://github.com/matrix-org/matrix-spec/issues/228).

This MSC would play along well with
[MSC3861](https://github.com/matrix-org/matrix-spec-proposals/blob/hughns/delegated-oidc-architecture/proposals/3861-delegated-oidc-architecture.md)
by delegating another aspect of user management to a standard protocol. It might call for a SCIM implementation in
[matrix-authentication-service](https://github.com/matrix-org/matrix-authentication-service).

## Notes

[Indiehosters](https://indiehosters.net/) has [obtained a
grant](https://forum.indiehosters.net/t/candidature-ngi-nlnet-privacy-trust-enhancing-technologies/4715) from the
[NLNet foundation](https://nlnet.nl/) for the realisation of several things around SCIM. My employer
[Yaal Coop](https://yaal.coop/) has been hired to work on the possible Matrix specification and synapse implementation.
