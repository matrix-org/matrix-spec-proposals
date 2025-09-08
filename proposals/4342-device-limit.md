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

Unlike these apps however, Matrix is a decentralised protocol with many different types of clients/apps available. This biases towards
users running multiple apps for the same account.

### Proposal

The maximum number of devices a user can have at any one time is reduced to 30.
Servers MAY have an even lower limit than this. Servers MUST NOT have a higher limit than this.

>[!NOTE]
> This proposal has to balance the needs and desires of users with the needs and desires of server admins
> who cannot allow unbounded amounts of data. This proposal aims to balance this by affecting <1% of "power users"
> where "power users" is defined as having >= 2 devices logged into matrix.org as of Sept 2025.
>
> 30 was chosen based on a statistical analysis of the matrix.org database:
> - 99.312% of users have <= 5 devices. A limit of 5 will affect 1 in every 145 users.
> - 99.839% of users have <= 10 devices. A limit of 10 will affect 1 in every 621 users.
> - 99.931% of users have <= 15 devices. A limit of 15 will affect 1 in every 1449 users.
> - 99.978% of users have <= 30 devices. A limit of 30 will affect 1 in every 4545 users.
>
> Excluding users with only 1 device (e.g throwaway accounts or users who try Matrix once and never again):
> - 79.809% of users with >1 device have <= 5 devices. A limit of 5 will affect 1 in every 5 users with >1 device.
> - 95.277% of users with >1 device have <= 10 devices. A limit of 10 will affect 1 in every 21 users with >1 device.
> - 98.818% of users with >1 device have <= 20 devices. A limit of 20 will affect 1 in every 85 users with >1 device.
> - 99.367% of users with >1 device have <= 30 devices. A limit of 30 will affect 1 in every 158 users with >1 device.
> - 99.558% of users with >1 device have <= 40 devices. A limit of 40 will affect 1 in every 226 users with >1 device.
> - 99.654% of users with >1 device have <= 50 devices. A limit of 50 will affect 1 in every 289 users with >1 device.
> - 99.712% of users with >1 device have <= 60 devices. A limit of 60 will affect 1 in every 347 users with >1 device.

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

Servers which retrospectively apply this MSC MAY arbitrarily logout the oldest devices to reclaim resources from those users.
Users SHOULD be informed of this beforehand e.g via a Server Notices room.

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
