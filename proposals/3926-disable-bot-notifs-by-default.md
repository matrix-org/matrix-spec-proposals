# MSC3926: Disable server-default notifications for bot users by default

Matrix users are configured [with predefined notification rules](https://spec.matrix.org/v1.4/client-server-api/#predefined-rules)
when they register an account. This applies to both regular Matrix users, but also application service and bot user accounts.

In the case of the latter two, it's not useful to calculate notifications because the majority of
application services and bots do not read notifications.

Notifications are "cleared" when a read receipt is sent into the room, but neither bots or application
services send read receipts in all cases. This can very easily lead to a lot of wasted disk space in some
implementations.

There is also the case that each notitification rule will take some amount of CPU time to process, which
is entirely wasted if the account doesn't check notifications.

Ultimately for these reasons, we should allow bots and appservices to opt-out of server-side notifications
upon registration.

## Proposal

A new body field `enable_predefined_push_rules` will be introduced to [`GET /_matrix/client/v3/register`](https://spec.matrix.org/v1.4/client-server-api/#post_matrixclientv3register),
which will allow users to opt-out of default notifications.

When set, the homeserver MUST disable all rules defined in [predefined-rules](https://spec.matrix.org/v1.4/client-server-api/#predefined-rules),
effectively thereby disabling the calculation of notifications. The user will still be able to enable these notification rules if they so wish.

When the `type` of registration is `m.login.application_service`, the default value of `enable_predefined_push_rules`
will be `false`.

For normal registrations, it will be `true`.

## Potential issues

This doesn't solve the problem for the large number of existing bots and application service users today.

The decision to blanket disable notifications for these users rests with the homeserver and/or
application service implementation, rather than a spec concern.

## Alternatives

### Only enable notifications on first /sync

Instead of adding a flag, the homeserver could instead only start tracking notifications when the user
/syncs. This might help with cases where users are registered but never used. It would also help with 
application services where users never sync. However, this would still cause notifications to be calculated
for traditional `/sync`ing bots. Overall an explicit option at registration time seems more preferable.

### Bots and Appservices could explicitly disable notifications

Bots and integrations could instead explicitly disable all rules on signup, rather than expecting the
homeserver to complete this for them. However, the *defaults* set by the spec are sufficient enough of a
"footgun" that it's easy for developers to forget this setting and allow their homeserver to accumulate
notifications.

Furthermore, severity of running a large application service and filling your database
with unread notifications is higher than potentially missing out on notifications as an appservice user which
is considered more of a niche use case.


## Security considerations

None. The decision to enable or disable notifications is left up to the registering user.

## Unstable prefix

While this MSC is unstable, `enable_predefined_push_rules` should be called `org.matrix.mscXXXX.enable_predefined_push_rules`.

To avoid breaking existing functionality. The *default* setting for both application services and regular users will
be `true`. Developers will be expected to be explicit with their choice until this MSC is merged and the
defaults given in the [proposal](##Proposal) are used.

## Dependencies

None.