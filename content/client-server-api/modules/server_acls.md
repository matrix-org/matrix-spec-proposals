---
type: module
---

### Server Access Control Lists (ACLs) for rooms

In some scenarios room operators may wish to prevent a malicious or
untrusted server from participating in their room. Sending an
[m.room.server\_acl](#mroomserver_acl) state event into a room is an effective way to
prevent the server from participating in the room at the federation
level.

Server ACLs can also be used to make rooms only federate with a limited
set of servers, or retroactively make the room no longer federate with
any other server, similar to setting the `m.federate` value on the
[m.room.create](#mroomcreate) event.

{{% event event="m.room.server_acl" %}}

{{% boxes/note %}}
Port numbers are not supported because it is unclear to parsers whether
a port number should be matched or an IP address literal. Additionally,
it is unlikely that one would trust a server running on a particular
domain's port but not a different port, especially considering the
server host can easily change ports.
{{% /boxes/note %}}

{{% boxes/note %}}
CIDR notation is not supported for IP addresses because Matrix does not
encourage the use of IPs for identifying servers. Instead, a blanket
`allow_ip_literals` is provided to cover banning them.
{{% /boxes/note %}}

#### Client behaviour

Clients are not expected to perform any additional duties beyond sending
the event. Clients should describe changes to the server ACLs to the
user in the user interface, such as in the timeline.

Clients may wish to kick affected users from the room prior to denying a
server access to the room to help prevent those servers from
participating and to provide feedback to the users that they have been
excluded from the room.

#### Server behaviour

Servers MUST prevent blacklisted servers from sending events or
participating in the room when an [m.room.server\_acl](#mroomserver_acl) event is
present in the room state. Which APIs are specifically affected are
described in the Server-Server API specification.

Servers should still send events to denied servers if they are still
residents of the room.

#### Security considerations

Server ACLs are only effective if every server in the room honours them.
Servers that do not honour the ACLs may still permit events sent by
denied servers into the room, leaking them to other servers in the room.
To effectively enforce an ACL in a room, the servers that do not honour
the ACLs should be denied in the room as well.
