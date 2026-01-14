# MSC4277: Harmonizing the reporting endpoints

Matrix currently has three reporting endpoints:

- [`/_matrix/client/v3/rooms/{roomId}/report/{eventId}`] ([added] in Matrix
  0.4.0, no MSC known)
- [`/_matrix/client/v3/rooms/{roomId}/report`] ([added][1] in Matrix 1.13 as per
  [MSC4151])
- [`/_matrix/client/v3/users/{userId}/report`] ([added][2] in Matrix 1.14 as per
  [MSC4260])

The spec contains a number of subtle differences for these endpoints:

1.  The user reporting endpoint allows servers to respond with 200 even if the
    user doesn't exist to deny enumerating users. This option is not allowed in
    the event and room reporting endpoints.
2.  The user and event reporting endpoints allow servers to add a random delay
    when generating responses. This is a more sophisticated measure against
    enumeration attacks. While the spec doesn't explicit forbid this technique
    on the room reporting endpoint it doesn't explicitly mention or recommend it
    either.
3.  The event reporting endpoint contains a `score` property in the request body
    that was made optional by [MSC2414] in 2020. The other two endpoints, when
    introduced much later, didn't include this property. Evidently, this is
    because `score` hasn't proved useful on event reports.

These differences seem unnecessary and at least some of them were likely
introduced by accident only. The present proposal, therefore, seeks to align the
three endpoints.

Note that in addition to the list above, the endpoints also differ in their
handling of the `reason` property in the request body. [MSC2414] made `reason`
optional on the event reporting endpoint. The other two endpoints, however, went
the opposite direction and made `reason` required (while allowing it to be
blank) to limit spam. Resolving this inconsistency is not covered by this
proposal.

## Proposal

On all three endpoints:

1.  Servers MAY respond with 200 and no content regardless of whether the
    reported subject exists or not to combat enumeration attacks.
2.  Servers MAY add a random delay or use constant time functions when
    processing responses to combat enumeration attacks.
3.  The `score` property is removed.

All of these changes appear applicable regardless of the reported subject and it
is not clear why the spec should differentiate the endpoints here.

## Potential issues

Some clients may send `score` on event reports today. These clients are not
broken by this proposal because servers that implement it will simply ignore any
`score` property.

## Alternatives

None.

## Security considerations

Enumeration attacks are likely more severe for users than for rooms or events.
There are still not irrelevant, however.

## Unstable prefix

None.

## Dependencies

None.

  [`/_matrix/client/v3/rooms/{roomId}/report/{eventId}`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3roomsroomidreporteventid
  [added]: https://github.com/matrix-org/matrix-spec-proposals/pull/1264
  [`/_matrix/client/v3/rooms/{roomId}/report`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3roomsroomidreport
  [`/_matrix/client/v3/users/{userId}/report`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3usersuseridreport
  [1]: https://github.com/matrix-org/matrix-spec/pull/1938
  [MSC4151]: https://github.com/matrix-org/matrix-spec-proposals/pull/4151
  [2]: https://github.com/matrix-org/matrix-spec/pull/2093
  [MSC4260]: https://github.com/matrix-org/matrix-spec-proposals/pull/4260
  [MSC2414]: https://github.com/matrix-org/matrix-spec-proposals/pull/2414
