# MSC3873: event_match dotted keys

The current specification of [`event_match`] describes the parameter
`key` as

> `key`: The dot-separated path of the property of the event to match,
> e.g. `content.body`.

It does, however, not clarify how to handle collisions such as in

    {
      "m": { "foo": "bar" },
      "m.foo": "baz"
    }

where it is unclear which field the dot-separated path `m.foo` should
match ([#648]).

While collisions are often not a practical problem, the ambiguity in the
specification leads to incomptible implementations as evidenced by
[matrix-org/matrix-js-sdk#1454]. The current proposal resolves the
ambiguity by leveraging the existing solution for the same problem in
the [filter API].

## Proposal

The . character in the `key` parameter is changed to be exclusively
reserved for field separators. Any literal key in field names is to be
escaped using a \\.

Revisiting the example from above

    {
      "m": { "foo": "bar" },
      "m.foo": "baz"
    }

this means that `"key": "m.foo"` unambigously matches the nested `foo`
field. The top-level `m.foo` field in turn can be matched through
`"key": "m\.foo"`.

As mentioned above, this exact solution is already employed in the
[filter API]. Reusing it here, therefore, increases the
specification’s coherence.

## Backwards compatibility

In order to provide partial backwards compatibility, implementations
should continue supporting unescaped dot-separated paths in situations
where they are collision-free. In other words, `"key": "m.foo"` should
continue matching both

    {
      "m": { "foo": "bar" },
    }

and

    {
      "m.foo": "baz"
    }

but not

    {
      "m": { "foo": "bar" },
      "m.foo": "baz"
    }

It is recommend that implementations maintain this fallback for a
certain transition period, e.g. one year, to give clients a chance to
update any affected push rules.

## Potential issues

The proposed solution is only partially backwards compatible and will
break any push rule that relies on implicit implementation behavior
caused by the ambiguity. This is, unfortunately, unavoidable because the
very purpose of this proposal is to resolve said ambiguity.

## Alternatives

An alternative to the current proposal are [JSON pointers]. While
being more versatile than the simplistic escaping proposed here, JSON
pointers introduce a wholy new DSL for the `key` parameter which breaks
backwards compatibility for *all* existing `event_match` conditions.

## Security considerations

None.

  [`event_match`]: https://spec.matrix.org/v1.3/client-server-api/#conditions-1
  [#648]: https://github.com/matrix-org/matrix-spec/issues/648
  [matrix-org/matrix-js-sdk#1454]: https://github.com/matrix-org/matrix-js-sdk/issues/1454
  [filter API]: https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3useruseridfilter
  [JSON pointers]: https://www.rfc-editor.org/rfc/rfc6901
