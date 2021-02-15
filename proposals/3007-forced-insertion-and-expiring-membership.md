# MSC3007: Forced member insertion, expiring memberships and room blocking by self-banning

This proposal is going to change the auth rules to allow for users to forcibly add other users into
public or knockable rooms if they have a newly proposed power to `insert_member`. In addition,
it adds a new field `exipres` to invite requests which, when used, sets an expiration on invite and
membership. Those two in combination can be used to implement an ban reversal, a ban-subject-to-probation,
or a temporary room membership.

## Proposal

### Forced member insertion, self-banning and inviting from ban

The current auth rules do not allow `ban` to `join` or `ban` to `invite` transistion in the member
state machine in any case. This proposal seeks to add well-defined rules on who can reverse a ban to
membership without going through not-member `leave` state.

Add `insert_member` field to `m.room.power_levels`, whose value is going to be interpreted as
the minimum power level that a member has to have to be able to forcibly add users to a room.
Unless greater than or equal to the power level required to invite, this operation is completely
disallowed in said room.

Change the auth rules for the member state transistions as follows:
* from anything to `ban`: allowed only if the banning user has the power to perform `ban` or banning
and banned users are the same (the latter case is termed a self-ban, and is irreversible)
* from `ban` to `invite`: allowed only if the inviter has power to perform both `ban` and `invite`,
ill-formed if the user attempts to invite oneself, or user has self-banned
* from `ban` to `join`: allowed only if the member attempting to insert has power to perform
both `ban` and `insert_member`, unless user has self-banned
* from `ban` to `leave`: allowed only if the member attempting to unban has power to perform `ban`,
and the ban on the user is not a self-ban
* from `leave` to `join`: allowed only if join rule is `public` or the member attempting to insert
has power to perform `insert_member`

The endpoint for a member to forcibly add a member is virtually identical to the endpoint for invites
(see below for "expiring invites", in which section I define an `expires` field), except for the path
and an optional field `power_level`, which determines post-insertion power level for
the newly inserted member:

```
POST /_matrix/client/r0/rooms/room_address/insert  HTTP/1.1
Content-Type: application/json

{
  "user_id": "@user:example.com",
  "power_level": 0 
}
```
The insertion is ill-formed if the specified power level is greater than user's own power level or
user attempts to insert itself using this method. Field `roles` is reserved for a future role-based
power implementation and currently inoperative.

### Expiring invites and memberships

There is currently no way to temporarily insert a member. This seeks to solve the problem by adding
an `expires` field at invites, which is a timestamp determining the expiration time of both
the invite and the resulting membership. Membership expiration shall be treated as equivalent to
membership status transtioning to `leave` at the time specified at `expires` field.

## Potential issues

* Repeated ban-invite or ban-insert cycles by room moderators, causing an event spam on clients.
* Users accidentally blocking rooms by self-banning.

## Alternatives

Not considered yet.

## Security considerations

No security risks foreseen.

## Unstable prefix

Not implemented yet.
