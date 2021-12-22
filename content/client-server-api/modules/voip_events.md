---
type: module
weight: 20
---

### Voice over IP

This module outlines how two users in a room can set up a Voice over IP
(VoIP) call to each other. Voice and video calls are built upon the
WebRTC 1.0 standard. Call signalling is achieved by sending [message
events](#events) to the room; these events are defined in the
[events spec](/events/#voice-over-ip).

#### Server behaviour

The homeserver MAY provide a TURN server which clients can use to
contact the remote party. The following HTTP API endpoints will be used
by clients in order to get information about the TURN server.

{{% http-api spec="client-server" api="voip" %}}
