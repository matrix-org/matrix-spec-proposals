Feature Profiles
================

Matrix supports many different kinds of clients: from embedded IoT devices to
desktop clients. Not all clients can provide the same feature sets as other
clients e.g. due to lack of physical hardware such as not having a screen.
Clients can fall into one of several profiles and each profile contains a set
of features that the client MUST support. This section details a set of
"feature profiles". Clients are expected to implement a profile in its entirety
in order for it to be classified as that profile.

Summary
-------

============================ ===== =========== ======== ========= ===== =====
  Module / Profile            Web   Embed-Web   Mobile   Desktop   CLI   IoT
============================ ===== =========== ======== ========= ===== =====
 `End-to-End Encryption`_     YES                YES       YES     YES
 `Instant Messaging`_         YES    YES         YES       YES     YES   YES
 `Presence`_                  YES                YES       YES     YES
 `Push Notifications`_                           YES
 `Receipts`_                  YES                YES       YES     YES
 `Typing Notifications`_      YES                YES       YES     YES
 `VoIP`_                      YES                YES       YES
 `Content Repository`_        YES                YES       YES     YES
============================ ===== =========== ======== ========= ===== =====

*Please see each module for more details on what clients need to implement.*

.. _End-to-End Encryption: `module:e2e`_
.. _Instant Messaging: `module:im`_
.. _Presence: `module:presence`_
.. _Push Notifications: `module:push`_
.. _Receipts: `module:receipts`_
.. _Typing Notifications: `module:typing`_
.. _VoIP: `module:voip`_
.. _Content Repository: `module:content`_

