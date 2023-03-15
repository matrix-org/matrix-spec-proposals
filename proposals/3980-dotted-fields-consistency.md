# MSC3980: Dotted Field Consistency

[MSC3873](https://github.com/matrix-org/matrix-spec-proposals/pull/3873) disambiguated
how event properties are matched for push rules and based the proposal on how
[filters](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3useruseridfilter)
are currently escaped for consistency.

Through the MSC process the escaping was expanded from just escaping `.` characters
with a backslash (`\.`) to also escaping backslashes themselves (`\\`). Unfortunately
that MSC did not propose applying this change *back* to filters for consistency. [^1]

## Proposal

Apply consistent escaping as described in [MSC3873](https://github.com/matrix-org/matrix-spec-proposals/pull/3873)
to the `event_fields` property of filters.
This would allow an unambiguous way to describe property names, as currently
the behavior of backslashes is undefined.

The text given in MSC3873 can apply here (changing `key` to `event_fields`):

> The dot (`.`) character in the [`event_fields`] parameter is changed to be exclusively
reserved for field separators. Any literal dot in field names are to be
escaped using a backslash (`\.`) and any literal backslashes are also escaped with
a backslash (`\\`). A backslash before any other character has no special meaning
and is left as-is, but it is recommended that implementations do not redundantly
escape characters, as they may be used for escape sequences in the future.

In short, this would update the
[description of `event_fields`](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3useruseridfilter)
(bolded part is new):

> List of event fields to include. If this list is absent then all fields are
> included. The entries may include ‘.’ characters to indicate sub-fields. So
> [‘content.body’] will include the ‘body’ field of the ‘content’ object. A
> literal ‘.’ **or '\\'** character in a field name may be escaped using a ‘\’. A server
> may include more fields than were requested.


## Potential issues

This is slightly backwards incompatible if a property name currently contains a
backslash in it.

## Alternatives

Leave things as they are and be inconsistent between different parts of the spec.

## Security considerations

N/A

## Unstable prefix

N/A

## Dependencies

N/A

[^1]: This came up while writing the [spec PR for MSC3873](https://github.com/matrix-org/matrix-spec/pull/1464#discussion_r1135712844).
