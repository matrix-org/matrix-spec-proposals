# MSC2663: Errors for dealing with inexistent push rules

This MSC proposes that homeservers respond with a HTTP 404 ('Not Found') status
code and an `errcode` of `M_NOT_FOUND` when a client attempts to read or write
the `enabled` status or `actions` of a non-existent push rule.

## Background

The current revision of the Client-Server specification does not make clear what
a homeserver implementation is meant to do when getting or setting the `enabled`
or `actions` properties of a supposed push rule that does not exist.

## Motivation

This change is considered minor and the proposed error code is deemed
unsurprising as it matches the remainder of the specification.

## Proposal

The following endpoints of the Client-Server specification are affected:

- `GET /_matrix/client/r0/pushrules/{scope}/{kind}/{ruleId}`
- `DELETE /_matrix/client/r0/pushrules/{scope}/{kind}/{ruleId}`
- `PUT /_matrix/client/r0/pushrules/{scope}/{kind}/{ruleId}`
- `GET /_matrix/client/r0/pushrules/{scope}/{kind}/{ruleId}/enabled`
- `PUT /_matrix/client/r0/pushrules/{scope}/{kind}/{ruleId}/enabled`
- `GET /_matrix/client/r0/pushrules/{scope}/{kind}/{ruleId}/actions`
- `PUT /_matrix/client/r0/pushrules/{scope}/{kind}/{ruleId}/actions`

The affected endpoints will have the following response status code added:

**Status code 404:**

The push rule does not exist.

**Example**
```json
{
  "errcode": "M_NOT_FOUND"
}
```

This error response is to be returned when the push rule represented by
`{scope}/{kind}/{ruleId}` does not exist.
