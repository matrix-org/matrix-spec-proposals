Matrix Specification
====================

.. Note that this file is specifically unversioned because we don't want to
.. have to add Yet Another version number, and the commentary on what specs we
.. have should hopefully not get complex enough that we need to worry about
.. versioning it.

This specification has been generated from
https://github.com/matrix-org/matrix-doc using
https://github.com/matrix-org/matrix-doc/blob/master/scripts/gendoc.py as of
revision ``{{git_version}}`` -
https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}.

There is an `introduction and overview to the specification here <intro.html>`_.

The following APIs are documented in this specification:

- `Client-Server API <client_server.html>`_ version %CLIENT_RELEASE_LABEL% for writing Matrix clients.
- `Server-Server API <server_server.html>`_ version %SERVER_RELEASE_LABEL% for writing servers which can federate with Matrix.
- `Application Service API <application_service.html>`_ version %CLIENT_RELEASE_LABEL% for writing privileged plugins to servers.
- `Identity Service API <identity_service.html>`_ version unstable for mapping third party identifiers (e.g. email addresses) to Matrix IDs.
- `Push Gateway API <push_gateway.html>`_ version unstable for implementing a server that receives notifications about Matrix events a user is interested in.

There are also some `appendices <appendices.html>`_.

Any developments since the latest release can be found `here`__.

.. __: https://matrix.org/speculator/spec/head/

Old releases of the spec:

- `r0.0.1 <https://matrix.org/docs/spec/r0.0.1>`_
- `r0.0.0 <https://matrix.org/docs/spec/r0.0.0>`_

Before we formally started releasing the specification, the last working copy
we had can be found `here`__.

.. __: https://matrix.org/docs/spec/legacy/

Versioning
----------

The specifications are each versioned in the form ``rX.Y.Z``.

Changes to ``X`` and ``Y`` should not be assumed to be compatible with any other version.

For a fixed ``X`` and ``Y``, any ``Z`` should be assumed to be compatible with any lesser ``Z``.

For example, it is safe to assume that a server which claims to implement ``r0.1.2`` supports ``r0.1.0``, but not vice-versa.
