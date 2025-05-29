# MSC0666: Ignore and mass ignore invites


## Proposal


### Introduction 

Invite spam is getting more problematic and clients have no good way to handle massive invite spamming without server support.

**Ignoring** users seem to help this but it has two serious problems:

- completely igoring users make them completely disappear for the user, and if the user is also a moderator/adminstrator it makes impossible to detect and handle further abuse
- servers are not _required_ to clean up [invites] after ignored users (by the spec).

**Rejecting ignores** also creates problem for clients:

- Invite rejections are _room based_, so when a user is invited to massive amount of rooms by `spammer` then rejections require numerous `leave` API calls
- API calls are rate limited so massive rejections may be impossible without seriously disturbing user communication
- There are no mass invite rejection feature based on `sender`

This proposal suggests a separate ignore for invites, and proposes compulsory server cleanup of invites, giving one solution for all of the listed problems.

### Proposed solution

Ignores are currently handled by `m.ignored_user_list` (`account_data` [APIs](https://spec.matrix.org/v1.14/client-server-api/#put_matrixclientv3useruseridaccount_datatype)).

Current spec only handles `ignored_users` list.

I propose to have it extended by `ignored_inviters` list the following way:

- the type is `m.ignored_inviters_list`
- it is a mapping of userId to empty object, similar to `ignored_users`
- the limit of the amount of the entries shall follow the same guidelines as `ignored_users`

#### Server behaviour

- Following an update of the `m.ignored_user_list`, the sync API for all clients should immediately start ignoring (or un-ignoring) all invites from all the listed users.
- Servers are **required** to reject all pending invites from all the ignored users.
- Servers could choose to provide a boilerplate `reason` for rejection (but see security considerations below)

## Potential issues

When the server doesn't support this feature it should give appropriate error to the client, and the client have to handle that.

Clients should be aware of the success of the ignore somehow since they need a method to clear pending invited from the user UI. The method should be the same as for `ignored_users`.

This proposal does not handle rejection of all future invites.

This proposal does not handle rejection of future invites of various logical classification, like "invites from actors not sharing a room with the user", "invites from actors matching a pattern or regex", "invites from actors on a given server". These are often requested features but would make this proposal much more complex, which would slow down its acceptance. These could be covered in a later proposal.

## Alternatives

Manual rejection, hitting rate limits, losing connection, spam invites piling up. Sadness.

## Security considerations

This function is fuctionally similar to `ignore_users`, any security consideration there may apply here.

When a server autorejects invites on the user behalf it may choose to include a boilerplate `reason` for the rejection. However this would cause an unnecessary information leak towards the abuser (informing whether the server provides mass ignore or not), so choosing to have an absent `reason` may be prudent, this way it is indistinguishable from manual rejections. This proposal provides no way for the user to provide a `reason` field, which may or may not cause discomfort.

## Unstable prefix

This proposal use the already established `m.ignored_user_list` feature, extending its functionality.
