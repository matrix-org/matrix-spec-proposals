# MSC4002: Walkie-Talkie 

Implementing a Walkie-Talkie-like feature to enhance its communication capabilities.
The proposed feature would allow users to send and receive E2EE voice messages
in real-time, similar to how a Walkie-Talkie operates.
This functionality will require protocol changes as broadcast need to be locked server
side for everyone when one person is talking and it needs permission management. 
Real-time Voice Communication is often needed at a workplace or can be usefull in a group
of friends or even families when parents could want to maintain easy
communication with a child 24/7.

## Proposal

	Real-time Voice Communication:
Voice messages are sent and received in real-time, allowing for instant 
communication without the need for typing or waiting for messages to be fully dictated/recorded.

	Walkie-Talkie instantiation:
Works on top of a room for everyone that allowed receiving Real-time Voice
Communication in that specific room.
For all participating in receiving Real-time Voice Communication, typical record and send
voice communication turns into live broadcast VoIP on demand.
There only can be one user speaking at the time so protocol must lock it for everyone else.

	Bridges and Other Users:
Walkie-Talkie broadcast recording will display as regular voice message for everyone to replay.
	
	Permissions:
Only users that are willing to receive Walkie-Talkie broadcast can broadcast themselves
Walkie-Talkie receiving and sending permit can be time limited or permanent
depending on user preference.
Permission is device based and every device that accepted it will receive it.

## Potential issues

Walkie-Talkie broadcast recordings are usefull for everyone but could litter chat history.

User can be in multiple Walkie-Talkie groups in the same time, client need to cache unplayed
messages while user is recording or playing other broadcasts.

50% of this project is client side dependent.

What if slight delay between home servers results in allowing 2 users speak at the same time?
Homeserver could go and ask every other homeserver if anyone is talking and lock audio for a while
but some Homeservers have like 1s ping.

VoIP really needs to be on demand so it wont use battery and internet while in sleep state.
Socket like system could turn it on and off.

## Alternatives

Regular VoIP still exist however it isn't perfect in work environment.

## Security considerations

Recordings of broadcasts for future replay need to be client side dependent to preserve E2EE.

## Unstable prefix

No unstable prefix is currently proposed.

## Dependencies

No dependencies are currently needed.
