# MSC 2002 - Rooms V4

This MSC proposes creating a new room version named v4 to allow servers to switch
event ID grammar to that proposed in MSC1884.

## Proposal

The new room version is called "4". The only difference between v4 and v3 is
that v4 rooms use the grammar for defining event IDs as proposed in MSC1884 -
expressing event IDs as url-safe base64 rather than plain base64 for the
convenience of client implementors.

It is not proposed that servers change the default room version used when
creating new rooms, and it is not proposed that servers recommend upgrading
existing rooms to v4.

## Rationale and Context

We would like to default to creating rooms with a reasonably secure room
algorithm in upcoming Matrix 1.0.  We do not want to default to creating v3
rooms due to the inconvenience the v3 event ID grammar might cause, so instead
we are proposing favouring v4.

Ideally we would also include other room algorithm changes in v4 (e.g.
honouring server signing key validity periods, as per
https://github.com/matrix-org/synapse/issues/4364), but as spec &
implementation work is still ongoing there, we are proposing using v4 as a
room version which can be supported in the wild before Matrix 1.0 and then
used as the initial default for creating rooms.  The expectation is for the
versions of the spec which coincide with 1.0 to also support v5 rooms, but in
practice v5 will not be marked as default until it has sufficient adoption on
the public network.

The expectation is never to recommend upgrading existing
rooms to v4, but instead v5 (once ready), to avoid overburdening room admins
with upgrade notifications.

To conclude, the proposed plan is:
 1. Define room v4 as MSC1884
 2. Introduce servers with v4 support into the public network as rapidly as possible
 3. Wait for enough servers to speak v4.  Meanwhile:
    1. Define an MSC for honouring server signing key validity periods
    2. Implement this MSC
    3. Define room v5 as this MSC
 4. Release Matrix 1.0, defining room v4 as the new default for creating rooms,
    but also shipping support for room v5 for the first time.
 5. Wait for enough servers to speak v5 rooms.
 6. Define room v5 as the new default for creating rooms.
 7. Define room versions prior to v5 as unsafe, thus prompting users to upgrade their
    rooms to v5.

The reason we don't wait for v5 to be widespread before releasing 1.0 is to avoid
delaying the 1.0 yet further.  It is good enough for 1.0 to support v5 without it
also being the default for creating rooms.
