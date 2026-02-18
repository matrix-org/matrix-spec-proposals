# MSC4043: Presence Override API

In current matrix there exists no mechanism that is reliable to override the supposed to exist totem pole
for presence. Where more important states overrule less important ones. This proposal fixes that.

This proposal proposes a new API that you can call to set a authoritative presence state for your account. This
state is always used negating all other ways to set presence. So if you set your state to `disabled` from
[MSC4042](https://github.com/matrix-org/matrix-spec-proposals/pull/4042) then well then your state would always be `disabled`.

Using a new API for this instead of recycling some old method does come at the benefit of that this just works.

No existing code can mess up and use this wrong to effectively ruin the whole point of this system because its new.

Being able to set your authoritative presence state is seen as beneficial due to that it allows users to have full
control over their presence status instead of having to rely on all clients on their account collaborating to not
ruin the intention of the user.

## Proposal

To set a new presence override you call the new `/_matrix/client/v1/presence/{userId}/override` endpoint
using a PUT request. Using a payload that can look like the example below.

```json
{
  "presence_override": "online"
}
```

The `presence_override` key used is whatever you want to force your presence to be.

If you want to ask for what your current override is you simply make a GET request to the same endpoint.

And you will get back a response that is like the example below if your override is `offline`.

```json
{
  "presence_override": "offline"
}
```

And to disable override you send a payload with a empty `presence_override` key like the example below.

```json
{
  "presence_override": ""
}
```

As for error codes this is currently WIP but it follows a similar pattern to the current `/_matrix/client/v3/presence/{userId}/status`
endpoint. With minor reasonable adaptations like how presence is replaced with presence override where sensible.

## Potential issues

Other than this functionality being duplicate the author does not foresee any potential issues other than
that clients that don't support this feature will not be able to set the override status for the user.

## Alternatives

There are talks about that certain existing presence mechanisms might have this as their intended functionality but
as is addressed at the top of this proposal they have a viability problem in the fact that they are all existing
mechanisms. Existing mechanisms being reused can lead to clients with bad implementations misusing them
causing the mechanism to be rendered useless.

A completely new API comes with the benefit that no legacy implementations can ruin everyone's experience.

## Security considerations

This proposal should not as far as the author is aware have security implications that are negative. The primary
positive effect is privacy related not strictly security in that users can cloak their presence state reliably.

## Unstable prefix

While this proposal is unstable instead of using `/_matrix/client/v1/presence/{userId}/override` you use
`/_matrix/client/unstable/support.feline.msc4043.v1/presence/{userId}/override`

And unstable feature flag used is `support.feline.msc4043.v1`

## Dependencies

This MSC has MSC4042 as a soft dependency as its a very useful state to override to.
This MSC has no hard dependencies and can be used on its own and merged on its own.
