# MSC4042: Disabled Presence State

In current matrix we have no way to tell clients that we simply do not have presence data at all
for a given homeserver or user. This proposal addresses this fact by adding a `disabled` state.

By adding a `disabled` state to presence it allows us to kill two birds with one stone. Its used for
MSC4043 and for this proposal. In this proposal its simply used to indicatea lack of information about 
a given user. This is going to 9 times out of 10 be because of that presence is disabled somewhere in the 
chain and therefore you cant get data. Be that disabled by the other user or their server or your server.
If you are on matrix.org for example all presence will return this value if this proposal is adopted until 
they reenable presence. Since they have presence disabled.


## Proposal

This proposal proposes the `disabled` presence state. This makes it the 4th presence state together
with `online`, `offline`, `unavailable`. 

Due to `unavailable` being taken for another use `disabled` became the best candidate due to its dual use.

`disabled` presence should be used if data is missing. Be that due to presence being disabled or because of other
mechanisms this state was selected. For example due to the user choosing to put this as their state via
MSC4043 or other mechanism like this. 


## Potential issues

The author can not see any significant potential issues arising from this change except that it can cause
clients that are not architected to withstand protocol changes to break. 


## Alternatives

The alternatives for this proposal are well not that many if any? Like a way to indicate we don't have any data
is useful. The only change I can think of is splitting intentional lack of data from we just don't have data yet.
But I fail to find that distinction useful.


## Security considerations

Presence should not be security relevant as far as the author is aware. The only exception is the privacy
discussion. This specific proposal should not have any impact on privacy because of the fact that this proposal
does not it self change anything in practice. Presence being disabled is not a secret its a well known fact.

## Unstable prefix

Unstable implementations will use the state of `support.feline.msc4042.v1.disabled` in place of `disabled`.

## Dependencies

This MSC does not have any direct dependencies but is paired with MSC4043 due to
this MSC being a semi dependency for it. These proposals can be adopted independently.
