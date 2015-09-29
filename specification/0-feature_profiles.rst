Feature Profiles
================

.. sect:feature-profiles:

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
 `End-to-End Encryption`_                                             
 `Instant Messaging`_         YES    YES         YES       YES     YES   YES
 `Presence`_                  YES                YES       YES     YES
 `Push Notifications`_                           YES
 `Receipts`_                  YES                YES       YES     YES
 `Typing Notifications`_      YES                YES       YES     YES
 `VoIP`_                      YES                YES       YES
 `Content Repository`_        YES                YES       YES     YES
 `History Visibility`_        YES                YES       YES     YES
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
.. _History Visibility: `module:history-visibility`_

Clients
-------

Stand-alone web (``Web``)
~~~~~~~~~~~~~~~~~~~~~~~~~

This is a web page which heavily uses Matrix for communication. Single-page web
apps would be classified as a stand-alone web client, as would multi-page web
apps which use Matrix on nearly every page.

Embedded web (``EmbedWeb``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a Matrix client which is embedded in another website, e.g. using
iframes. These embedded clients are typically for a single purpose
related to the website in question, and are not intended to be fully-fledged
communication apps.

Mobile (``Mobile``)
~~~~~~~~~~~~~~~~~~~

This is a Matrix client specifically designed for consumption on mobile devices.
This is typically a mobile app but need not be so provided the feature set can
be reached (e.g. if a mobile site could display push notifications it could be
classified as a mobile client).

Desktop (``Desktop``)
~~~~~~~~~~~~~~~~~~~~~

This is a native GUI application which can run in its own environment outside a
browser.

Command Line Interface (``CLI``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a client which is used via a text-based terminal.

Internet of Things (``IoT``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a client which is typically running on an embedded device such as a
kettle, fridge or car.

