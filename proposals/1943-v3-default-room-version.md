# Set v3 to be the default room version

Homeservers support multiple room versions, though one version is the default.
All new rooms created by a server are of the default version.

Room v3 contains support for the new state resolution algorithm and support
for event ids as hashes. Thereby closing a raft of security issues.

This MSC proposes changing the default from v1 to v3.


## Proposal

The default room should be updated to be room v3 from v1.

Until we have greater confidence in the room upgrade UX v1 and v2 will continue
to be marked as 'stable'.

This means that new rooms will be created as v3 rooms, but existing rooms will
not be prompted to upgrade. Separately we intend to deprecate v1 (and v2), but
doing will come as part of a separate MSC

## Tradeoffs

Room v4 will arrive very soon and ideally it will become the default room
version promptly. However in order for a room version to be the default there
must be sufficient take up in the federation so as to avoid locking out old
servers.

That said v3 and v4 are very similar, the significant change being
[server key validity period](https://github.com/matrix-org/synapse/issues/4364)
and there is obvious value to the community to adopt v3 even in the
knowledge that v4 will surpass it shortly.

## Potential issues

If new rooms are to be v3 some old servers will not be able to participate
since they will not support v3. For context, v3 was introduced in Synapse 0.99.0
on 5th Feb 2019.

Ignoring a long tail of of pre 0.30.0 servers (0.30.0 was released in
May 2018) ~2/3 servers support v3, and practically speaking ~90% of users are
on v3 compatible servers.

It does not seem unreasonable to expect Synapse admins to update to > 0.99.0
server as a means to mitigate any difficulties caused by not supporting v3 rooms.


## Security considerations

The primary driver for this MSC is to address known security vulnerabilities.

## Conclusion

Marking v3 as the default room version is a pragmatic means to improve security
in the Matrix federation. Future MSCs will propose further changing the default
to v4 as well marking v1 and v2 as 'unstable' to encourage all rooms to upgrade.
