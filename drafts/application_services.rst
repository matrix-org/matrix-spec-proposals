.. TODO
  Sometimes application services need to create rooms (e.g. when lazy loading 
  from room aliases). Created rooms need to have a user that created them, so 
  federation works (as it relies on an entry existing in m.room.member). We should 
  be able to add metadata to m.room.member to state that this user is an application 
  service, a virtual user, etc.

Application Services
====================

Overview
========

Application services provide a way of implementing custom serverside functionality
on top of Matrix without the complexity of implementing the full federation API.
By acting as a trusted service logically located behind an existing homeserver,
Application services are decoupled from:

* Signing or validating federated traffic or conversation history
* Validating authorisation constraints on federated traffic
* Managing routing or retry schemes to the rest of the Matrix federation

As such, developers can focus entirely on implementing application logic rather
than being concerned with the details of managing Matrix federation.

Features available to application services include:

* Privileged subscription to any events available to the homeserver
* Synthesising virtual users
* Synthesising virtual rooms
* Injecting message history for virtual rooms
 
Features not provided by application services include:

* Intercepting and filtering/modifying message or behaviour within a room
  (this is a job for a Policy Server, as it requires a single logical focal
  point for messages in order to consistently apply the custom business logic)
 
Example use cases for application services include:

* Exposing existing communication services in Matrix

  * Gateways to/from standards-based protocols (SIP, XMPP, IRC, RCS (MSRP), SIMPLE, Lync, etc)
  * Gateways to/from closed services (e.g. WhatsApp)
  * Gateways could be architected as:
  
    * Act as a virtual client on the non-Matrix network
      (e.g. connect as multiple virtual clients to an IRC or XMPP server)
    * Act as a server on the non-Matrix network
      (e.g. speak s2s XMPP federation, or IRC link protocol)
    * Act as an application service on the non-Matrix network
      (e.g. link up as IRC services, or an XMPP component)
    * Exposing a non-Matrix client interface listener from the AS
      (e.g. listen on port 6667 for IRC clients, or port 5222 for XMPP clients)


* Bridging existing APIs into Matrix
   * e.g. SMS/MMS aggregator APIs
   * Domain-specific APIs such as SABRE

* Integrating more exotic content into Matrix
   * e.g. MIDI<->Matrix gateway/bridge
   * 3D world <-> Matrix bridge

* Application services:
   * Search engines (e.g. elasticsearch search indices)
   * Notification systems (e.g. send custom pushes for various hooks)
   * VoIP Conference services
   * Text-to-speech and Speech-to-text services
   * Signal processing
   * IVR
   * Server-machine translation
   * Censorship service
   * Multi-User Gaming (Dungeons etc)
   * Other "constrained worlds" (e.g. 3D geometry representations)

     * applying physics to a 3D world on the serverside

       * (applying gravity and friction and air resistance... collision detection)
       * domain-specific merge conflict resolution of events

   * Payment style transactional usecases with transactional guarantees

Architecture Outline
====================

The application service registers with its host homeserver to offer its services.

In the registration process, the AS provides:

* Credentials to identify itself as an approved application service for that HS
* Details of the namespaces of users and rooms the AS is acting on behalf of and
  "subscribing to"
* Namespaces are defined as a list of regexps against which to match room aliases,
  room IDs, and user IDs. Regexps give the flexibility to say, sub-domain MSISDN
  ranges per AS, whereas a blunt prefix string does not. These namespaces are further
  configured by setting whether they are ``exclusive`` or not. An exclusive namespace
  prevents entities other than the aforementioned AS from creating/editing/deleting
  entries within that namespace. This does not affect the visibility/readability of
  entries within that namespace (e.g. it doesn't prevent users joining exclusive
  aliases, or ASes from listening to exclusive aliases, but does prevent both users
  and ASes from creating/editing/deleting aliases within that namespace).
* There is overlap between selecting events via the csv2 Filter API and subscribing
  to events here - perhaps subscription involves passing a filter token into the
  registration API.
* A URL base for receiving requests from the HS (as the AS is a server,
  implementers expect to receive data via inbound requests rather than
  long-poll outbound requests)

On HS handling events to unknown users:

* If the HS receives an event for an unknown user who is in the namespace delegated to 
  the AS, then the HS queries the AS for the profile of that user.  If the AS
  confirms the existence of that user (from its perspective), then the HS
  creates an account to represent the virtual user.
* The namespace of virtual user accounts should conform to a structure like
  ``@.irc.freenode.Arathorn:matrix.org``.  This lets Matrix users communicate with
  foreign users who are not yet mapped into Matrix via 3PID mappings or through
  an existing non-virtual Matrix user by trying to talk to them via a gateway.
* The AS can alternatively preprovision virtual users using the existing CS API
  rather than lazy-loading them in this manner.
* The AS may want to link the matrix ID of the sender through to their 3PID in
  the remote ecosystem.  E.g. a message sent from ``@matthew:matrix.org`` may wish
  to originate from Arathorn on irc.freenode.net in the case of an IRC bridge.
  It's left as an AS implementation detail as to how the user should authorise
  the AS to act on its behalf.

On HS handling events to unknown rooms:

* If the HS receives an invite to an unknown room which is in the namespace
  delegated to the AS, then the HS queries the AS for the existence of that room.
  If the AS confirms its existence (from its perspective), then the HS creates
  the room.
* The initial state of the room may be populated by the AS by querying an
  initialSync API (probably a subset of the CS initialSync API, to reuse the
  same pattern for the equivalent function).  As messages have to be signed
  from the point of ``m.room.create``, we will not be able to back-populate
  arbitrary history for rooms which are lazy-created in this manner, and instead
  have to chose the amount of history to be synchronised into the AS as a one-off.
* If exposing arbitrary history is required, then:
   
  * either: the room history must be preemptively provisioned in the HS by the AS via
    the CS API (TODO: meaning the CS API needs to support massaged
    timestamps), resulting in conversation history being replicated between
    the HS and the source store.
  * or: the HS must delegate conversation storage entirely to the
    AS using a Storage API (not defined here) which allows the existing
    conversation store to back the HS, complete with all necessary Matrix
    metadata (e.g. hashes, signatures, federation DAG, etc).  This obviously
    increases the burden of implementing an AS considerably, but is the only
    option if the implementer wants to avoid duplicating conversation history
    between the external data source and the HS.

On HS handling events to existing users and rooms:

* If the HS receives an event for a user or room that already exists (either
  provisioned by the AS or by normal client interactions), then the message
  is handled as normal.
* Events in the namespaces of rooms and users that the AS has subscribed to
  are pushed to the AS using the same pattern as the federation API (without
  any of the encryption or federation metadata).  This serves precisely the
  same purpose as the CS event stream and has the same data flow semantics
  (and indeed an AS implementer could chose to use the CS event stream instead)
  
  * Events are linearised to avoid the AS having to handle the complexity of
    linearisation, and because if linearisation is good enough for CS, it
    should be good enough for AS. Should the AS require non-linearised events
    from Matrix, it should implement the federation API rather than the AS API
    instead.
  * HS->AS event pushes are retried for reliability with sequence numbers
    (or logical timestamping?) to preserve the linearisation order and ensure
    a reliable event stream.
  * Clustered HSes must linearise just as they do for the CS API.  Clustered
    ASes must loadbalance the inbound stream across the cluster as required.

On AS relaying events from unknown-to-HS users:

* AS injects the event to the HS using the CS API, irrespective of whether the
  target user or room is known to the HS or not.  If the HS doesn't recognise
  the target it goes through the same lazy-load provisioning as per above.
* The reason for not using a subset of the federation API here is because it
  allows AS developers to reuse existing CS SDKs and benefit from the more
  meaningful error handling of the CS API.  The sending user ID must be
  explicitly specified, as it cannot be inferred from the access_token, which
  will be the same for all AS requests.

  * TODO: or do we maintain a separate ``access_token`` mapping?  It seems like
    unnecessary overhead for the AS developer; easier to just use a single
    privileged ``access_token`` and just track which ``user_id`` is emitting events?
  * If the AS is spoofing the identity of a real (not virtual) matrix user,
    we should actually let them log themselves in via OAuth2 to give permission
    to the AS to act on their behalf.
  * We can't auth gatewayed virtual users from 3rd party systems who are being
    relayed into Matrix, as the relaying is happening whether the user likes it
    or not.  Therefore we do need to be able to spoof sender ID for virtual users.
 
On AS relaying events in unknown-to-HS rooms:

* See above.

On AS publishing aliases for virtual rooms:

* AS uses the normal alias management API to preemptively create/delete public
  directory entries for aliases for virtual rooms provided by the AS.
* In order to create these aliases, the underlying room ID must also exist, so
  at least the ``m.room.create`` of that room must also be prepopulated.  It seems
  sensible to prepopulate the required initial state and history of the room to
  avoid a two-phase prepopulation process.
   
On unregistering the AS from the HS:

* An AS must tell the HS when it is going offline in order to stop receiving
  requests from the HS.  It does this by hitting an API on the HS.

AS Visibility:

* If an AS needs to sniff events in a room in order to operate on them (e.g.
  to act as a search engine) but not inject traffic into the room, it should
  do so by subscribing to the relevant events without actually joining the room.
* If the AS needs to participate in the room as a virtual user (e.g. an IVR
  service, or a bot, or a gatewayed virtual user), it should join the room
  normally.
* There are rare instances where an AS may wish to participate in a room
  (including inserting messages), but be hidden from the room list - e.g. a
  conferencing server focus bot may wish to join many rooms as the focus and
  both listen to VoIP setups and inject its own VoIP answers, without ever
  being physically seen in the room.  In this scenario, the user should set
  its presence to 'invisible', a state that HSes should only allow AS-authed
  users to set.
   
E2E Encryption

* The AS obviously has no visibility to E2E encrypted messages, unless it is
  explicitly added to an encrypted room and participates in the group chat
  itself.

Extensions to CS API
====================

* Ability to assert the identity of the virtual user for all methods.
* Ability to massage timestamps when prepopulating historical state and
  messages of virtual rooms (either by overriding ``origin_server_ts`` (preferred) or
  adding an ``as_ts`` which we expect clients to honour)
* Ability to delete aliases (including from the directory) as well as create them.
