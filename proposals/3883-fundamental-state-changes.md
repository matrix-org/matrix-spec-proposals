# MSC3883: Fundamental state changes (Draft)

## Problems

1. Room Joins:
    Joining rooms takes very long. Over 10 minutes are required to join Matrix HQ.
    A room has a lot of state associated with it. Most of it needs to be
    transferred, validated and persisted.

2. State resolution:
    It can be very expensive. Split brained rooms are tolerated, so similar
    state resolutions have to be done over and over again.

3. State events:
    Setting your avatar will send state events with that picture into all
    joined rooms. If you picked a wrong picture on accident, you can't undo it.


## Proposal

- Only users with power level > 50 can send state events.

- Memberships updates are coordinated using EDUs.
    Each server is responsible for tracking kicks, bans etc. of its own users.
    If a server abuses this, the server should be banned as a whole.

- Displayname/Avatar updates should be EDUs that trigger a /profile query. While servers still fetch the picture, at least it is not in the timeline.
