# MSC4052: Hiding read receipts UI in certain rooms

Displaying read receipts is not relevant or useful in all kinds of rooms. This MSC proposes a hint for clients that they shouldn't display read receipts in the UI for certain rooms.

## Proposal

A new room state event `m.hide_ui` with state key `read_receipts` determines whether read receipts should be hidden in the UI. To opt-in to hiding read receipts, the event should contain `{"hidden": true}`. Other properties are ignored. If `hidden` is not `true` then read receipts are not hidden.

An example use-case is when rooms are bridged to other platforms but those platforms don't support all of Matrix's features. As a practical example, read receipts are not a feature on IRC. Any IRC rooms bridged with Matrix will show each user as only having read messages that they themselves sent. Implementing this proposal would make the behaviour consistent between Matrix users and bridged users.

Another example use-case is for announcement rooms which may be read by thousands of users. Users probably don't care whether other users have read the latest update, so the read receipt UI is noise in these rooms. Hiding it would provide a better experience.

The `m.hide_ui` event is designed to be sent by a compatible appservice bridge when it manages a bridged room. It can also be sent manually for any reason.

In the future, this concept could be extended to hide other parts of the UI using other state keys. Sticking with IRC as an example, the bridge bot may ask clients to hide "add reaction" buttons, "create rich reply" buttons, "upload file" buttons and so on, if it knows that it cannot handle those events in a satisfactory way. The exact details are out of scope for MSC4052. MSC4052 only specifies hiding read receipts in the UI.

## Potential issues

Since this flag applies to the entire room, users on the Matrix side of the bridge will not be able to see read receipts from other Matrix users, even when those read receipts are correct. See below.

## Alternatives

Rather than hiding all read receipts, it may be desirable to only hide read receipts of bridged users. However, this comes with its own issues: without a visible read receipt a particular user might not be perceived by others to be part of the room.

## Security considerations

The default power level required to send state events, including `m.hide_ui`, is PL 50. This should be fine for most rooms. PL 100 might be a better fit.

Not all clients will follow this spec, so read receipts might still be displayed. We may want clients to also send private read receipts (see MSC2285 which is merged) for rooms in this mode. Otherwise, users might not realise they are leaking what messages they've viewed.

## Unstable prefix

When unstable, the event type `chat.schildi.hide_ui` should be used instead. (The state key is still `read_receipts` and the content is still `{"hidden": true}`.)

## Implementations

* [SchildiChat (client)](https://github.com/SchildiChat/matrix-react-sdk/pull/18)
* [Out Of Your Element (bridge)](https://gitdab.com/cadence/out-of-your-element/commit/5e6bb0cd2edaa8c340b5f27d5ccfce622c22fc8e#diff-1712f73f1ef677367997f55e69a76b0cc2a2b425)


