# MSC3234: Send currently active room event to bots

**This is a first time informal draft, please edit and reformat freely**


Whenever a client is actively checking a room, i.e. the client window is active and a room is
being monitored, send an ephemeral event to compatible bots in the room so they are aware
the user is still actively looking at the room. The client would periodically check if the user
is still monitoring the room and if so, send appropriate events to the other clients.

## Proposal

Consider a bridge implementation that needs to actively check a browser for read-receipts.
It would make sense to only do so for the rooms that are currently open and when the user
is actually waiting to check for such receipts. Without it the bridge would need its own timer
to check for the receipts, and could potentially mark incoming messages as read.

### Potential implementation (Please replace with specifics)

- A user would check if the server has this functionality and send its desired configuration
for this protocol to the currently active clients.
- The server would redirect the request to any compatible clients as soon as available
- The client would configure itself according to the request:
  - **delay time**: A desired time to check and periodically send this event to the listed users
  - **timeout**: If and how the user can pause this check e.g. only check if last message is not the user's
- The client would then set its timer for sending these events while active in the given room.
If the user is not active on the client ignore/pause the timers
- Receiving user would then proceed with their own logic utilizing this event, 
e.g. checking for bridge read-receipts

## Potential issues

## Alternatives

There are some MSCs that would relate to this implementation like MSC3006 and MSC2477.
This could be a specific implementation of those, but still necessary to be standardized as
there are no general systems to install logics to custom ephemiral events proposed in MSC2477.

## Security considerations

This might be abused to monitor unwilling users, so there should be a stage requiring user
verification at least during the bot's registration stage to the clients. For tranperancy sake
the client could also display to which bot the events were sent and when, e.g. `poked bot_A at ...`