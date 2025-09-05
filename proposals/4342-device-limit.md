## MSC4342: Limiting the number of devices per user ID

Matrix currently does not specify any limit to the number of devices a user can have. This has
negative impacts on homeservers:
 - They need to persist an unbounded set of devices. If those devices use E2EE, they also need to persist one-time keys (OTKs).
 - The way device lists are synced over federation (`prev_id` and `stream_id` in `m.device_list_update` EDUs) is complex and error-prone, primarily to support this unbounded workload.
 - Any wildcard queries (`/sendToDevice` with a device ID of `*`) causes massive traffic amplification.

..and on clients:
 - Sending encrypted messages encrypts for all devices in the room. A single user with thousands of devices
   can significantly impact performance when sending encrypted messages.
 - Size limits on HTTP requests means a user with thousands of devices risks causing unable to decrypt errors as the response
   to `/keys/claim` exceeds the size permitted by reverse proxies. As `/keys/claim` is server-scoped, this can impact the ability
   to claim OTKs for innocent users.

What's worse, often users with many devices are unaware that they have so many e.g because they have logged in via their browser repeatedly.
This ultimately reduces security of E2EE as messages are encrypted for an unnecessarily large number of sessions, any one of which could be
compromised to then decrypt the messages.

Because the number of devices affects not just the user with those devices but everyone they communicate with,
the limit needs to be enforced in the specification, hence this proposal.

In comparison to other encrypted apps:
- WhatsApp restricts to [5 devices](https://faq.whatsapp.com/378279804439436/?cms_platform=android) (one primary, 4 linked).
- Signal restricts to [6 devices](https://support.signal.org/hc/en-us/articles/360007320551-Linked-Devices) (one primary, 5 linked).

### Proposal

The maximum number of devices a user can have at any one time is reduced to 10.

>[!NOTE]
> 10 was chosen based on a statistical analysis of the matrix.org database:
> - 99.312% of users have <= 5 devices. A limit of 5 will affect 1 in every 145 users.
> - 99.839% of users have <= 10 devices. A limit of 10 will affect 1 in every 621 users.
> - 99.931% of users have <= 15 devices. A limit of 15 will affect 1 in every 1449 users.

Attempts to login and exceed this limit returns the error code `M_TOO_MANY_DEVICES`. A client receiving this
error code should instruct the user to logout an existing device and try again.

>[!NOTE]
> There's two main options here: prevent the limit being exceed or logout the longest inactive device.
> Logging out devices causes data loss because it drops to-device events which contain encryption keys.
> Therefore, this proposal instead prevents the limit being exceeded by returning an error code.

Application service users will be unaffected by this restriction.

>[!NOTE]
> Application services may have workflows outside expected use cases. To reduce the risk of this proposal
> having unintended consequences, application service users (and their exclusive namespaced users) are exempt
> from this limit.

### Potential Issues

Clients which do not log out cleanly by failing to talk to the server when logging out will still be tracked
as a device. Certain workflows which repeatedly destroy clients in this way (e.g the client runs on a VM
which is destroyed at the end of every day) will be impacted by this change as they will slowly accumulate
more and more devices. Clients which behave in this manner need to manage the existing sessions for the user
or else they will eventually be unable to login.

### Alternatives

The number can be higher or lower than 10. 10 was chosen to limit the impact on existing users using matrix.org
as their homeserver.

We could continue to have no limit. However, this will eventually become untenable due to the unbounded
growth of devices. 

### Security Considerations

An attacker who has the password for a user may login many devices to stop the real user from logging in
new devices. However, if an attacker has your password they can do worse and logout your devices causing
data loss. The additional denial of service risk seems small in comparison.

### Unstable prefix

The error code is `ORG_MATRIX_MSC4342_M_TOO_MANY_DEVICES` whilst in development.

### Dependencies

None.