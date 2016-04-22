Matrix Specification
====================

.. Note that this file is specifically unversioned because we don't want to
.. have to add Yet Another version number, and the commentary on what specs we
.. have should hopefully not get complex enough that we need to worry about
.. versioning it.

Matrix is a set of APIs for open-federated Instant Messaging (IM), Voice
over IP (VoIP) and Internet of Things (IoT) communication, designed to create
and support a new global real-time communication ecosystem.

For a more complete introduction to Matrix, see `Introduction <intro.html>`_.

Matrix APIs
-----------

The following APIs are documented in this specification:

- `Client-Server API <client_server.html>`_ (%CLIENT_RELEASE_LABEL%) Interaction between clients and servers
- `Server-Server API <server_server.html>`_ (%SERVER_RELEASE_LABEL%) Federation between servers
- `Application Service API <application_service.html>`_ (%CLIENT_RELEASE_LABEL%) Privileged server plugins
- `Identity Service API <identity_service.html>`_ (unstable) Mapping of third party IDs with Matrix IDs
- `Push Gateway API <push_gateway.html>`_ (unstable) Push notifications for Matrix events

`Appendices <appendices.html>`_ with supplemental information not specific to
of the above APIs is also available.

Specification Version
---------------------

The documents in the specification are generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

The following other versions of the specification are also available,
in reverse chronological order:

- `HEAD <https://matrix.org/speculator/spec/head/>`_: Includes all changes since the latest versioned release.
- `r0.0.1 <https://matrix.org/docs/spec/r0.0.1>`_
- `r0.0.0 <https://matrix.org/docs/spec/r0.0.0>`_
- `Legacy <https://matrix.org/docs/spec/legacy/>`_: The last draft before the spec was formally released in version r0.0.0.

The specification for each API is versioned in the form ``rX.Y.Z``. Changes to
``X`` and ``Y`` should not be assumed to be compatible with any other version.
For a fixed ``X`` and ``Y``, any ``Z`` should be assumed to be compatible with
any lesser ``Z``. For example, it is safe to assume that a server which claims
to implement ``r0.1.2`` supports ``r0.1.0``, but not vice-versa.
