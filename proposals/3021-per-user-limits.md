# MSC3021: Limits API — Part 1: per-User Fanout Limits

Not all servers are as lucky as matrix.org to have variable scaling,
hence some of them will need to place fanout limits on users and rooms,
such as how many rooms a user is allowed to be member of, how many members can
a room simultaneously have, how may child rooms a space room is allowed
to have, or how many sessions a user is allowed to have simultaneously open.
This MSC deals with the easiest part, per-user fanout limits.

## The basics

To modify the limit of a particular user:
```
PUT /_matrix/client/r0/admin/limits/{user_id} HTTP/1.1
{
   "type": "m.limits.fanout.user_rooms",
   "value": infinity
}
```

To modify the limits of all users:
```
PUT /_matrix/client/r0/admin/limits/ HTTP/1.1
{
   "type": "m.limits.fanout.user_rooms",
   "value": infinity
}
```

The query will be made to the same paths, using the GET method instead.
And to delete the limit for the particular user, use the DELETE method
for the same path. A user is allowed to query users from own homeserver only.
If, a server-wide limit is defined but a user specific limit is not,
the user specific limit shall be returned as if it were the same. In case
both limits exist, the smaller limit for a given user shall apply.

## The per-user room limit semantics

A user shall not be allowed to join more rooms once it joins as many rooms as 
specified by the per-user room limit. The join requests will be rejected,
invites overturned and knocks ignored by the server. As soon as the number of
rooms user has joined drops below the limit, joins will be processed as usual.

If a user has more room than it is allowed to be joined when the limit is put
in place, it is to be auto-kicked from the excess rooms by the server
starting from the last joined one. If such a kick cannot be implemented
due to end-to-end encryption, then the server will ignore the room membership
FOR THAT USER ONLY, i.e. shall not deliver the events from that room to
the said user.
