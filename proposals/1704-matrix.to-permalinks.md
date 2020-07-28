# matrix.to permalink navigation

Currently Matrix uses matrix.to URIs to reference rooms and other entities in a
permanent manner. With just a room ID, users can't get into rooms if their server
is not already aware of the room. This makes permalinks to rooms or events difficult
as the user won't actually be able to join. A matrix.to link generated using a
room's alias is not a permanent link due to aliases being transferable.

In lieu of an improved way to reference entities permanently in Matrix, a new parameter
is to be added to matrix.to URIs to assist clients and servers receiving permanent links
in joining the room.

For reference, existing permalinks look like this:

```
https://matrix.to/#/!somewhere:example.org
https://matrix.to/#/!somewhere:example.org/$something:example.org
```

By adding a new parameter to the end, receivers can more easily join the room:

```
https://matrix.to/#/!somewhere:example.org?via=example-1.org&via=example-2.org
https://matrix.to/#/!somewhere:example.org/$something:example.org?via=example-1.org&via=example-2.org
```

Clients can pass the servers directly to `/join` in the form of `server_name`
parameters.

When generating the permalinks, clients should pick servers that have a reasonably
high chance of being in the room in the distant future. The current recommendation
is to pick up to 3 unique servers where the first one is that of the user with the
highest power level in the room, provided that power level is 50 or higher. The other
2 servers should be the most popular servers in the room based on the number of joined
users. This same heuristic should apply to the first server if no user meets the power
level requirements. Servers blocked by server ACLs should not be picked because they
are unlikely to continue being residents of the room. Similarly, IP addresses should
not be picked because they cannot be redirected to another location like domain names
can, making them a higher risk option.
