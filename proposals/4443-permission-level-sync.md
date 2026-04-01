# MSC0000: Permission Level Sync

Managing permissions across many rooms in a Matrix Space is currently a manual and error-prone process. 
If a community or organisation has a Space containing dozens of rooms, and an administrator wants to
promote a user to moderator across all of those rooms, they must visit each room individually and update
that user's power level by hand. This proposal adds a setting to the a room which allows the user to 
define a secondary room to sync permission level's with.

## Proposal

This is the part of the MSC that DidiDidi129 doesn't know how to complete properly. I can give write access to this repo to anyone who would like it...


## Potential issues
Homeserver might not be in both rooms, creating a mismatch between power levels. This can be
solved by allowing another homeserver to update the permissions on the other rooms provided
that there is a user on that server with sufficient permissions.

## Alternatives

Using bots is an option however this is "clunky" as the bot would need to be added to all the rooms,
with spesific permissions


## Security considerations
None that I can think of, though there are certainly going to be some

## Unstable prefix


## Dependencies

Implementation is required on the homeserver, with client support for configuring the settings.
Client support is not required once setup.
