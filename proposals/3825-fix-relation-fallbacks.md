# MSC3825: Obvious relation fallback location

[MSC3440](https://github.com/matrix-org/matrix-spec-proposals/pull/3440) defines
a way to use replies as a fallback for threads. For that it adds an
`is_falling_back` key. Alternatively other relations could be marked as a
fallback in the future if we get multiple relations or other advanced features.
Here are 2 examples, decide which one marks the reply as being a fallback and
which one marks the thread as being a fallback:

```jsonc
"m.relates_to": {
    "rel_type": "m.thread",
    "event_id": "ev1",
    "is_falling_back": true,
    "m.in_reply_to": {
        "event_id": "last_event_id_in_thread",
    }
}
```

```jsonc
"m.relates_to": {
    "rel_type": "m.thread",
    "event_id": "ev1",
    "m.in_reply_to": {
        "event_id": "last_event_id_in_thread",
        "is_falling_back": true,
    }
}
```

You probably have read 3440 so you know that the first option is marking the
reply in the thread relation as being a fallback. It is however not very
logical. The second option is much clearer. It also allows generic handling of
fallbacks in tools processing only the relations of the event like when handling
[pushrules for relations](https://github.com/matrix-org/matrix-spec-proposals/pull/3664).

## Proposal

Move the `is_falling_back` key into the relation it applies to. This means for
replies:

```jsonc
"m.in_reply_to": {
    "event_id": "last_event_id_in_thread",
    "is_falling_back": true,
}
```

And for other relations:


```jsonc
"m.relates_to": {
    "rel_type": "my.custom.relation",
    "event_id": "ev1",
    "is_falling_back": true,
}
```

For the transition period clients might still accept the old location for
threads until the ecosystem has been migrated.

The goal is to merge this change immediately before threads land in the specification.

## Potential issues

This is a breaking change to an already merged feature. This means it will break
events already sent into rooms and make them render incorrectly. This "should be
fine" for several reasons:

- The breakage means old events might show a reply relation when they should
    not. This is annoying and not pretty, but not the end of the world.
- Clients can mitigate by hardcoding a specific `origin_server_ts` to apply the
    old rules to events. While it is strongly recommended to drop this at some
    point for maintainability reasons, it should be fairly low overhead. Once
    relations become editable, we could also fixup those events for other
    clients.
- Thread (as of writing) are not part of a released spec version. They are
    marked as beta and users expect some things to not work optimally. As such
    minor breakage should be acceptable. They will become part of the spec in
    presumably end of Q3 2022. If we want to fix it, now is probably a better
    time than later.

## Alternatives

1. Just accept that threads are weird and never make `is_falling_back` a generic
   field. `is_falling_back` is a nice name and has otherwise clear semantics. I
   would prefer to not take that route.
2. Fix it later. Fixing this issue later is possible by introducing a new field
   and deprecating the old one. The breakage would probably be greater.
3. Special-case threads to have their field in that location. Not a pretty
   solution and prevents multiple relations to ever fall back to threads without
   introducing a different format.

## Security considerations

This introduces some ambiguities, so in theory it could be used to confuse
users. Impact should be fairly limited.

## Unstable prefix

Until this MSC has finished FCP, implementations should use
`im.nheko.msc3825.is_falling_back` as the fieldname instead.

## Dependencies

This MSC depends on threads (MSC3440), which is already merged.

It improves functionality in preparation of
- Pushrules for relations,
    [MSC3664](https://github.com/matrix-org/matrix-spec-proposals/pull/3664)
- Multiple relations or other MSCs building on top of relations that could
    benefit from fallback semantics like
    [MSC3051](https://github.com/matrix-org/matrix-spec-proposals/pull/3051)
