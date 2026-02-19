# MSC3837: Cascading profile tags for push rules

The push rule system includes support for per-device rule sets via
profile tags. Rules are stored either within the default `global` scope
or a dedicated `device/<profile_tag>` scope. When registering a pusher,
a specific profile tag can be assigned which will make this pusher only
execute rules within the associated scope.

This system works great in situations where two devices require
completely unrelated push rules. It is, however, cumbersome to use when
there is a common rule set with only minor differences per device
because clients have to keep the common parts in sync across scopes.

An exemplary use case is wanting to customize notification settings for
a specific room on your mobile phone without having to copy and maintain
your entire desktop push rule set in a separate scope.

The proposal at hand attempts to resolve this situation by introducing a
list of profile tags per pusher which are evaluated in cascade, stopping
at the first matching tag.

## Proposal

The existing `profile_tag` request parameter on
`POST /_matrix/client/v3/pushers/set` is deprecated and a new
`profile_tags` parameter is introduced.

-   Name: `profile_tags`
-   Type: `[string]`
-   Description: These strings determine which sets of device specific
    rules this pusher executes. The tags are evaluated in cascading
    order, stopping at the first tag that has a matching rule. If
    omitted or empty, defaults to `["global"]`.

The response of `GET /_matrix/client/v3/pushers` is changed accordingly
by deprecating `Puhser.profile_tag` and introducing
`Pusher.profile_tags`.

Servers should ignore duplicate profile tags in the array and only
retain the first occurrence of each tag. In other words,
`["tag1", "tag2", "tag1"]` is equivalent to `["tag1", "tag2"]`.

When evaluating an event against push rules, servers should follow the
following steps:

1.  Determine the highest priority matching rule (if any) in each
    existing scope
2.  For each pusher, walk through its `profile_tags` in order
    1.  If the current tag has a matching rule, execute it and stop
    2.  If the current tag doesn’t have a matching rule, continue to the
        next tag or stop if this is the last tag

To illustrate how this proposal can be used for the two use cases
mentioned in the introduction:

-   A device that wants to extend the `global` rule set without copying
    it can register a pusher with
    `"profile_tags": [<profile_tag>, "global"]`.
-   Two devices that want to maintain disjoint rule sets can register
    pushers with `"profile_tags": [<profile_tag1>]` and
    `"profile_tags": [<profile_tag2>]`, respectively.

## Potential issues

Even though profile tags are part of the spec, not all servers support
them today because an efficient implementation is complex. At the time
of writing, Synapse, for instance, only supports the `global` scope. The
current proposal further complicates the logic of profile tags which
likely makes a performant implementation even more involved.

## Alternatives

Instead of defining a new parameter, a delimiter-joined string such as
`"<profile_tag1>,<profile_tag2>"` could be provided in the existing
`profile_tag` parameter. However, this raises compatibility problems
because the spec doesn’t define an allowed character set for profile
tags. As a result, it’s not possible to determine a safe delimiter that
is guaranteed to not be part of an existing profile tag. Changing the
grammar for profile tags brings compatibility problems of its own
because some clients (such as Element Android) already apply profile
tags today.

As mentioned in the introduction, the common subsets of two or more push
rule scopes could be kept in sync by the client. This is inferior to the
current proposal because it bloats the total set of push rules,
discourages reuse and would require more invasive changes to the push
rule API to allow simultaneous manipulation of rules across scopes.

## Security considerations

None that wouldn’t also apply to the current single-profile-tag system.

## Unstable prefix

While this MSC is not considered stable, `profile_tags` should be
referred to as `org.matrix.msc3837.profile_tags`.

## Dependencies

This MSC doesn’t depend on but concerts with [MSC3767][] and [MSC3768][]
for fine-grained per-device push rule configurations.

  [MSC3767]: https://github.com/matrix-org/matrix-spec-proposals/pull/3767
  [MSC3768]: https://github.com/matrix-org/matrix-spec-proposals/pull/3768
