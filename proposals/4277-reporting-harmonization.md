# MSC4277: Harmonizing the reporting endpoints

Matrix currently has three reporting endpoints:

- [`/_matrix/client/v3/rooms/{roomId}/report/{eventId}`] ([added] in Matrix
  0.4.0, no MSC known)
- [`/_matrix/client/v3/rooms/{roomId}/report`] ([added][1] in Matrix 1.13 as per
  [MSC4151])
- `/_matrix/client/v3/users/{userId}/report` (to be [added][2] to Matrix as per
  [MSC4260])

The spec contains a number of subtle differences for these endpoints:

1.  The `reason` parameter on the event reporting endpoint was made optional by
    [MSC2414]. The other two reporting endpoints didn't pick up on this,
    however, and still require `reason` to be present while allowing it to be
    blank.
2.  The user reporting endpoint [allows] servers to respond with 200 even if the
    user doesn't exist to deny enumerating users. This option is not allowed in
    the event and room reporting endpoints.
3.  The user and event reporting endpoints allow servers to add a random delay
    when generating responses. This is a more sophisticated measure against
    enumeration attacks. While the spec doesn't explicit forbid this technique
    on the room reporting endpoint it doesn't explicitly mention or recommend
    it either.

These differences seem unnecessary and were likely introduced by accident only.
The present proposal, therefore, seeks to align the three endpoints.

## Proposal

On all three endpoints:

1.  The `reason` parameter is made optional.

2.  Servers MAY respond with 200 and no content regardless of whether the
    reported subject exists or not to combat enumeration attacks.

3.  Servers MAY add a random delay or use constant time functions when
    processing responses to combat enumeration attacks.

All of these changes appear applicable regardless of the reported subject and it
is not clear why the spec should differentiate the endpoints here.

## Potential issues

The `reason` field on the room and user reporting endpoints is currently
required. Making it optional, therefore, is a breaking change. Clients should
either act on the servers supported version or blanketly include an empty string
if the user doesn't provide a reason

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
  [1]: https://github.com/matrix-org/matrix-spec/pull/1938
  [MSC4151]: https://github.com/matrix-org/matrix-spec-proposals/pull/4151
  [2]: https://github.com/matrix-org/matrix-spec/pull/2093
  [MSC4260]: https://github.com/matrix-org/matrix-spec-proposals/pull/4260
  [MSC2414]: https://github.com/matrix-org/matrix-spec-proposals/pull/2414
  [allows]: https://github.com/matrix-org/matrix-spec-proposals/pull/4260/files#diff-cbb17920e2617e7a20ab0838879675f7aa70e828f0263a3cfa5f4c53913ce5f7R34-R35
