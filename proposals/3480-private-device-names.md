# MSCxxxx: Make device names private

Matrix allows users to use their account with multiple devices simultaneously.
These devices may be given a human-readable name (`device_display_name` or
`display_name`) to help users identify different devices.  For example, a
client can display a list of the user's devices so that they can log out stale
devices or check if there are any malicious or unexpected devices logged in to
their account.

In the past, prior to
[cross-signing](https://github.com/matrix-org/matrix-doc/pull/1756), this was
also used when verifying users' device keys, as users would need to select
which device you were verifying.  However, with cross-signing, we no longer
need to select individual devices to verify, and so we do not need to expose a
user's device display name to other users for verification.

In addition, the device display name may contain information that a user may
not wish to be broadcast publicly.  For example, some clients automatically
name devices based on the client name and device type, and if a device's
display name is "Foo client on ExpensiveBrandName® FancyPhone 10™", this
indicates that the user has a ExpensiveBrandName® FancyPhone 10™.  A user could
rename the devices to remove any information that they do not wish to be
public.  However, the user then needs to determine the tradeoff between
including enough information that they can distinguish their devices, and
removing enough information to satisfy their privacy preferences.

Given that device names are no longer needed for verification, which was the
main reason that the device names were public, we propose that device names
should only be published to the user who owns the devices.  Other users will
not receive the devices' display names.

Links:

* Element-web issue: [we should consider not publishing device names in a
  cross-signing world](https://github.com/vector-im/element-web/issues/10153)
* Element-web issue: [Rather than infer device names we should prompt users
  explicitly to name their devices when they log
  in](https://github.com/vector-im/element-web/issues/2295)


## Proposal

Device display names will only be visible to the user who owns the device.
Endpoints that report a device's display name will omit the display name when
querying a device that does not belong to the user calling the endpoint.  Also,
the `device_display_name` field from the `m.device_list_update` EDU will be
dropped; servers will no longer send this field, and will ignore it if it is
received.

As a transitional measure, servers that currently have devices with display
names should send updates to other servers indicating that the device display
names have been removed.  This should be done in the same way as if the users
had actually removed the device display names, with the exception that the
updates can be spread out over a period of time.


## Potential issues

Device display names can also be useful in debugging.  However, people who are
doing debugging are likely to be reasonably comfortable using device IDs, so on
balance, it is better to avoid the privacy impact of public device display
names.


## Alternatives

Rather than making the device display name private, a device could have a
public display name and a private display name, as suggested in
https://github.com/matrix-org/matrix-doc/issues/1826.  However, having to
manage public and private names could be confusing for a user.  In addition,
this would require API changes, whereas making device names private does not
require API changes.  (Note that #1826 also suggests making other information
about the device available privately.  This can be done independently of this
MSC.)


## Security considerations

Aside from addressing the privacy issue of public device display names, this
MSC does not try to fix any other security issues related to device display
names.  For example, server administrators are able to change a user's device
display names.

## Unstable prefix

Since no new names are being introduced, no unstable prefix is needed.
