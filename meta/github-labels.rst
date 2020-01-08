The following labels are used to help categorize issues:

`spec-omission <https://github.com/matrix-org/matrix-doc/labels/spec-omission>`_
--------------------------------------------------------------------------------

Things which have been implemented but not currently specified. These may range
from entire API endpoints, to particular options or return parameters.

Issues with this label will have been implemented in `Synapse
<https://github.com/matrix-org/synapse>`_. Normally there will be a design
document in Google Docs or similar which describes the feature.

Examples:

* `Spec PUT /directory/list <https://github.com/matrix-org/matrix-doc/issues/417>`_
* `Unspec'd server_name request param for /join/{roomIdOrAlias}
  <https://github.com/matrix-org/matrix-doc/issues/904>`_

`clarification <https://github.com/matrix-org/matrix-doc/labels/clarification>`_
--------------------------------------------------------------------------------

An area where the spec could do with being more explicit.

Examples:

* `Spec the implicit limit on /syncs
  <https://github.com/matrix-org/matrix-doc/issues/708>`_

* `Clarify the meaning of the currently_active flags in presence events
  <https://github.com/matrix-org/matrix-doc/issues/686>`_

`spec-bug <https://github.com/matrix-org/matrix-doc/labels/spec-bug>`_
----------------------------------------------------------------------

Something which is in the spec, but is wrong.

Note: this is *not* for things that are badly designed or don't work well
(for which see 'improvement' or 'feature') - it is for places where the
spec doesn't match reality.

Examples:

* `swagger is wrong for directory PUT
  <https://github.com/matrix-org/matrix-doc/issues/933>`_

* `receipts section still refers to initialSync
  <https://github.com/matrix-org/matrix-doc/issues/695>`_

`improvement <https://github.com/matrix-org/matrix-doc/labels/improvement>`_
----------------------------------------------------------------------------

A suggestion for a relatively simple improvement to the protocol.

Examples:

* `We need a 'remove 3PID' API so that users can remove mappings
  <https://github.com/matrix-org/matrix-doc/issues/620>`_
* `We should mandate that /publicRooms requires an access_token
  <https://github.com/matrix-org/matrix-doc/issues/612>`_

`feature <https://github.com/matrix-org/matrix-doc/labels/feature>`_
--------------------------------------------------------------------

A suggestion for a significant extension to the matrix protocol which
needs considerable consideration before implementation.

Examples:

* `Peer-to-peer Matrix <https://github.com/matrix-org/matrix-doc/issues/710>`_
* `Specify a means for clients to "edit" previous messages
  <https://github.com/matrix-org/matrix-doc/issues/682>`_


`wart <https://github.com/matrix-org/matrix-doc/labels/wart>`_
--------------------------------------------------------------

A point where the protocol is inconsistent or inelegant, but which isn't really
causing anybody any problems right now. Might be nice to consider fixing one
day.


`question <https://github.com/matrix-org/matrix-doc/labels/question>`_
----------------------------------------------------------------------

A thought or idea about the protocol which we aren't really sure whether to
pursue or not.

Examples:

* `Should we prepend anti-eval code to our json responses?
  <https://github.com/matrix-org/matrix-doc/issues/908>`_
