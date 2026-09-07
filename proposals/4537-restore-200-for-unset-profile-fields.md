# MSC4537: Restore `200 {}` for unset profile fields

[MSC4133] extended the profile API beyond `displayname` and `avatar_url`, merging the per-field endpoints into a single
[`GET /_matrix/client/v3/profile/{userId}/{keyName}`] that works for any profile field. In doing so, it also made an
unintended breaking change: since Matrix 1.16, fetching an **unset** `displayname` or `avatar_url` must return a `404`
error, where a `200` response with the field omitted had also been valid since the first version of the specification.

This MSC proposes to go back to the behaviour specified before Matrix 1.16, returning the client `v3` API to a state
where it carries no breaking change: both `200` with the field omitted and the `404` are valid representations of an
**unset** field, and clients treat them identically.

## Proposal

For requests to [`GET /_matrix/client/v3/profile/{userId}/{keyName}`] where the user exists and the requested field is
not set, servers MAY respond with either:

- `200` with an empty JSON object (`{}`), i.e. omitting the requested key from the response body; or
- `404` with an `M_NOT_FOUND` error code, as currently specified.

For `displayname` and `avatar_url`, servers MUST NOT respond with `200` and the requested key set to `null`: these two
fields are specified to hold string values, and `null` is not a valid value for them. This does not apply to fields
that may legitimately hold a `null` value: for those, a `200` response carrying an explicit `null` means the field is
set to `null`, not unset.

Clients MUST treat the two permitted responses identically, as the field not being set.

This proposal changes nothing about returning `404` for a user that does not exist, returning the `403` introduced by
[MSC4170], the server-server API, or the endpoint's authentication, rate-limiting and guest access requirements.

## Potential issues

### Another breaking change in v3

This MSC is technically a new breaking change to the `v3` API, following the one introduced by [MSC4133].
In practice this is not a problem:

- clients have started treating both responses equally, since some homeservers began returning the `404` when
  implementing [MSC4133]
- homeservers already return either one or the other

### Ecosystem divergence

The ecosystem has diverged and will continue to diverge between servers returning `200 {}` and servers returning the
`404`.

Such a divergence has been possible since the first version of the specification, which already allowed both
representations without saying which one a server should pick.

In practice it only materialised after Matrix 1.16, when the first implementation of the `404` appeared. The requirement
that clients treat both responses identically makes the divergence harmless, and a future version of the client/server
API could mandate a single representation.

## Alternatives

**Keep the specification as is, with the `404` as the only valid response.** This keeps the specification clean, with a
single representation of an unset field. However, most clients still expect `200 {}` and would need to change their
implementation to handle the `404`, as demonstrated when the one server that adopted it broke deployed clients
([mautrix/go#563]). It also leaves nearly every server non-compliant until they migrate.

**Mandate `200 {}` as the only valid response.** This would also keep the specification clean, and match what most
servers already do. However, it would put the implementations that followed the Matrix 1.16 text out of compliance,
swapping which part of the ecosystem is in violation rather than resolving the situation.

**Restrict the allowance to `displayname` and `avatar_url`.** Only these two fields carry the pre-1.16 legacy that
motivates this proposal, so the allowance could be scoped to them, keeping the `404` as the only representation of an
absent field for `m.tz` and custom fields. However, this would make the unset behaviour of the unified endpoint depend
on which key is being requested, and a single rule for all `keyName`s is simpler to implement and to specify.

## Security considerations

This proposal does not change what information is disclosed. Whether a user's existence and profile may be disclosed
to a requester is already governed by the `403` introduced by [MSC4170]: a server that is unwilling to disclose this
information answers `403` before the question of representing an unset field arises. The two permitted responses only
apply where profile look-up is allowed.

## History

- **2015-12** — the first stable release of the client-server API ([r0.0.0])
  - only the `200` response is documented: "The user's display name if they have set one."
  - no `404` appears in the published endpoint documentation
- **2016-02-03** — the unset case is clarified, twice in one day
  - first as "otherwise null" ([`542b17e9`][spec-null])
  - then as "otherwise not present" ([`53a4a563`][spec-not-present], "Actually we think they should not be present
    (which means synapse is buggy)")
  - the next day, Synapse stops returning `null` and omits the field instead ([`24277fbb`][synapse-2016], merged
    2016-02-04)
- **2016-05-09** — [r0.1.0] is released
  - it now also documents the `404` ("There is no display name for this user or this user does not exist"), inherited
    from the draft OpenAPI definitions
  - this is the first published version with both representations, and no guidance on which one to pick
- **2017-07-10** — Dendrite implements the profile API ([`1efbad81`][dendrite-2017])
  - its current implementation answers `200 {}` when the field is unset ([source][dendrite])
- **2020-04-09** — Conduit implements the profile endpoints ([`062c5521`][conduit-2020])
  - it answers `200 {}` when the field is unset
- **2022-06-30** — the deviation from the `404` reading is reported as [synapse#13137]
- **2024-09-13** — the duality is noticed during the [review][msc4133-review] of [MSC4133]
  - it is not resolved as a compatibility question
  - the accepted proposal restates only the `404`, describing it as "unchanged, just expanded to apply to arbitrary
    keys"
- **2024-09-14** — Conduwuit implements [MSC4133] ([`d75aebc3`][conduwuit-impl])
  - the new generic key route returns `404` for missing custom keys
  - `displayname` and `avatar_url` keep their dedicated routes answering `200 {}`
- **2025-01-21** — Synapse implements [MSC4133] ([synapse#17488], released in Synapse 1.123.0)
  - it accidentally replaces its long-standing `200 {}` with `200 {"displayname": null}`
    - this shape is valid under no version of the specification
    - it reintroduces the exact behaviour Synapse had [removed in 2016][synapse-2016]
- **2025-02-20** — the PR transcribing [MSC4133] into the specification is reviewed ([matrix-spec#2071])
  - the review settles the adjacent question of these fields' legacy `null` storage
    ([they can never be returned as `null`][null-thread])
  - the removal of the `200`-omission form goes undiscussed
- **2025-06-26** — [Matrix v1.15] is released
  - the wording of both representations is still unchanged since [r0.1.0]
- **2025-08-13** — Ruma implements the [MSC4133] endpoint ([`9ede1ac9`][ruma-2025])
  - its server-side implementation answers `200 {}` when the field is unset ([source][ruma-server])
- **2025-09-17** — [Matrix 1.16][v1.16-keyname] is released
  - the `404` is now the only valid representation of an unset field
- **2026-02-10** — Synapse's `null` breaks Element X
  - reported as [ruma#2360], worked around in [matrix-rust-sdk#6148]
  - the inconsistencies are reported as [synapse#19466]
- **2026-04-28** — Continuwuity unifies its legacy fields onto the [MSC4133] code path
  ([`1bf6d2a1`][continuwuity-impl])
  - it chooses `200 {}` for all fields
- **2026-06-29** — Tuwunel performs the same unification ([`fb5a4ea9`][tuwunel-impl])
  - it chooses the `404` for all fields
  - it becomes the first homeserver to return `404` for an unset legacy field
- **2026-08-31** — Tuwunel's `404` breaks Mautrix bridges ([mautrix/go#563])
  - their avatar update flow treats the `404` as a fatal error
- **2026-09-01** — Tuwunel reverts to `200 {}` for unset `displayname` and `avatar_url` ([`130f63da`][tuwunel-revert])
  - it keeps the `404` for other fields, matching Conduwuit
  - the Mautrix fix is closed unmerged, its maintainer expecting the specification to change instead
  - no homeserver returns `404` for an unset legacy field any more

<details>
<summary>The Conduit family tree summarises the divergence</summary>

```
Conduit ····························· 200 {}
└── Conduwuit (2024-09-14) ············ 200 {} for displayname/avatar_url, 404 for other fields
    ├── Continuwuity (2026-04-28) ····· 200 {} for all fields
    └── Tuwunel (2026-06-29) ·········· 404 for all fields
        └── (2026-09-01) ·············· 200 {} for displayname/avatar_url, 404 for other fields
```

</details>

## Unstable prefix

None: this proposal only affects HTTP status codes and response bodies of an existing endpoint.

## Dependencies

None.

[MSC4133]: https://github.com/matrix-org/matrix-spec-proposals/pull/4133
[MSC4170]: https://github.com/matrix-org/matrix-spec-proposals/pull/4170
[`GET /_matrix/client/v3/profile/{userId}/{keyName}`]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3profileuseridkeyname
[mautrix/go#563]: https://github.com/mautrix/go/pull/563
[Matrix v1.15]: https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3profileuseriddisplayname
[matrix-spec#2071]: https://github.com/matrix-org/matrix-spec/pull/2071
[synapse#17488]: https://github.com/element-hq/synapse/pull/17488
[ruma#2360]: https://github.com/ruma/ruma/issues/2360
[r0.0.0]: https://spec.matrix.org/historical/client_server/r0.0.0.html
[r0.1.0]: https://spec.matrix.org/historical/client_server/r0.1.0.html
[spec-null]: https://github.com/matrix-org/matrix-spec/commit/542b17e9
[spec-not-present]: https://github.com/matrix-org/matrix-spec/commit/53a4a563
[synapse-2016]: https://github.com/element-hq/synapse/commit/24277fbb97
[dendrite-2017]: https://github.com/element-hq/dendrite/commit/1efbad81
[conduit-2020]: https://github.com/continuwuity/continuwuity/commit/062c5521f
[ruma-2025]: https://github.com/ruma/ruma/commit/9ede1ac95
[dendrite]: https://github.com/element-hq/dendrite/blob/08cac1ccf0/internal/eventutil/types.go#L48-L49
[ruma-server]: https://github.com/ruma/ruma/blob/2f4413428217221e3fdae4f2069dc052dddb8e76/crates/ruma-client-api/src/profile/get_profile_field.rs#L212-L216
[synapse#13137]: https://github.com/matrix-org/synapse/issues/13137
[msc4133-review]: https://github.com/matrix-org/matrix-spec-proposals/pull/4133#discussion_r1759291605
[conduwuit-impl]: https://github.com/continuwuity/continuwuity/commit/d75aebc3
[null-thread]: https://github.com/matrix-org/matrix-spec/pull/2071#discussion_r1965190460
[v1.16-keyname]: https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3profileuseridkeyname
[synapse#19466]: https://github.com/element-hq/synapse/issues/19466
[continuwuity-impl]: https://github.com/continuwuity/continuwuity/commit/1bf6d2a1
[tuwunel-impl]: https://github.com/matrix-construct/tuwunel/commit/fb5a4ea96
[tuwunel-revert]: https://github.com/matrix-construct/tuwunel/commit/130f63da5b
[matrix-rust-sdk#6148]: https://github.com/matrix-org/matrix-rust-sdk/pull/6148
