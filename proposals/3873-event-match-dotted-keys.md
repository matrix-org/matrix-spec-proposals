# MSC3873: event_match dotted keys

The current specification of [`event_match`] describes the parameter
`key` as

> `key`: The dot-separated path of the property of the event to match,
> e.g. `content.body`.

It does not, however, clarify how to handle collisions such as in

    {
      "m": { "foo": "bar" },
      "m.foo": "baz"
    }

where it is unclear which field the dot-separated path `m.foo` should
match ([#648]).

Previously collisions were not often a practical problem, but as dotted-field names
have become more common in Matrix, e.g. `m.relates_to` or [MSC1767]-style
extensible events, this ambiguity is no longer satisfactory.

The ambiguity in the specification leads to incompatible implementations as
evidenced by [matrix-org/matrix-js-sdk#1454]. The current proposal resolves the
ambiguity by leveraging the existing solution for the same problem used by the
`event_fields` of [filters]:

> List of event fields to include. If this list is absent then all fields are included.
> The entries may include ‘.’ characters to indicate sub-fields. So [‘content.body’]
> will include the ‘body’ field of the ‘content’ object. A literal ‘.’ character
> in a field name may be escaped using a ‘\’.

This ambiguity is blocking other MSCs which all attempt to create rules on fields
with dots in them, such as:

* [MSC3952] Intentional Mentions
* [MSC3958] Suppress notifications from message edits

And likely any push rule for keywords using extensible events.

## Proposal

The dot (`.`) character in the `key` parameter is changed to be exclusively
reserved for field separators. Any literal dot in field names are to be
escaped using a backslash (`\.`) and any literal backslashes are also escaped with
a backslash (`\\`). A backslash before any other character has no special meaning
and is left as-is, but it is recommended that implementations do not redundantly
escape characters, as they may be used for escape sequences in the future.

Revisiting the example from above

    {
      "m": { "foo": "bar" },
      "m.foo": "baz"
    }

this means that `"key": "m.foo"` unambiguously matches the nested `foo`
field. The top-level `m.foo` field in turn can be matched through
`"key": "m\.foo"`.

As mentioned above, this exact solution is already employed by
[filters]. Reusing it here, therefore, increases the
specification’s coherence.

## Potential issues

This MSC provides no mechanism for backwards compatibility. [^1] This should not
impact the vast majority of users since none of the default push rules (nor common
custom push rules, e.g. for keywords) are dependent on dotted field names.

Implementations could attempt to disambiguate the `key` by checking all possible
ambiguous version this is fragile: what do you do if both ambiguous fields exist?
This gets worse as additional nested objects exist:

```json
{
  "m": { 
    "foo": { "bar":  "abc" },
    "foo.bar": "def"
  },
  "m.foo": { "bar": "ghi" },
  "m.foo.bar": "jkl"
}
```

This may break custom push rules that users have configured, but it is asserted
that those are broken anyway, as mentioned above (see [matrix-org/matrix-js-sdk#1454]).

## Alternatives

Alternatives to the current proposal are to use [JSON pointers] or [JSONPath]. While
being more versatile than the simplistic escaping proposed here, these are
unnecessary and break backwards compatibility for *all* existing `event_match`
conditions.

## Security considerations

None.

[^1]: See [a previous version].

  [`event_match`]: https://spec.matrix.org/v1.3/client-server-api/#conditions-1
  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
  [#648]: https://github.com/matrix-org/matrix-spec/issues/648
  [matrix-org/matrix-js-sdk#1454]: https://github.com/matrix-org/matrix-js-sdk/issues/1454
  [MSC3952]: https://github.com/matrix-org/matrix-spec-proposals/pull/3952
  [MSC3958]: https://github.com/matrix-org/matrix-spec-proposals/pull/3958
  [filters]: https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3useruseridfilter
  [JSON pointers]: https://www.rfc-editor.org/rfc/rfc6901
  [JSONPath]: https://goessner.net/articles/JsonPath/
  [a previous version]: https://github.com/matrix-org/matrix-spec-proposals/blob/cd906fcb263f667a7b8e5a626cc5b55fba3b9262/proposals/3873-event-match-dotted-keys.md?rgh-link-date=2022-08-21T18%3A02%3A02Z#backwards-compatibility
