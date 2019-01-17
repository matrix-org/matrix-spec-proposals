.. Copyright 2019 New Vector Ltd
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

SSO client login
================

.. _module:sso_login:

Single Sign-On (SSO) is a generic term which refers to protocols which allow
users to log into applications via a single web-based authentication portal.
Examples include "Central Authentication Service" (CAS) and SAML.

An overview of the process, as used in Matrix, is as follows:

1. The Matrix client instructs the user's browser to navigate to the
   |/login/sso/redirect|_ endpoint on the user's homeserver.

2. The homeserver responds with an HTTP redirect to the SSO user interface,
   which the browser follows.

3. The SSO system authenticates the user.

4. The SSO server and the homeserver interact to verify the user's identity
   and other authentication information, potentially using a number of redirects.

5. The browser is directed to the ``redirectUrl`` provided by the client with
   a ``loginToken`` query parameter for the client to log in with.

.. Note::
   In the older `r0.4.0 version <https://matrix.org/docs/spec/client_server/r0.4.0.html#cas-based-client-login>`_
   of this specification it was possible to authenticate via CAS when the server
   provides a ``m.login.cas`` login flow. This specification deprecates the use
   of ``m.login.cas`` to instead prefer ``m.login.sso``, which is the same process
   with the only change being which redirect endpoint to use: for ``m.login.cas``, use
   ``/cas/redirect`` and for ``m.login.sso`` use ``/sso/redirect`` (described below).
   The endpoints are otherwise the same.

Client behaviour
----------------

The client starts the process by instructing the browser to navigate to
|/login/sso/redirect|_ with an appropriate ``redirectUrl``. Once authentication
is successful, the browser will be redirected to that ``redirectUrl``.

.. TODO-spec

   Should we recommend some sort of CSRF protection here (specifically, we
   should guard against people accidentally logging in by sending them a link
   to ``/login/sso/redirect``.

   Maybe we should recommend that the ``redirectUrl`` should contain a CSRF
   token which the client should then check before sending the login token to
   ``/login``?

{{sso_login_redirect_cs_http_api}}

Server behaviour
----------------

The URI for the SSO system to be used should be configured on the server by the
server administrator. The server is expected to set up any endpoints required to
interact with that SSO system. For example, for CAS authentication the homeserver
should provide a means for the administrator to configure where the CAS server is
and the REST endpoints which consume the ticket. A good reference for how CAS could
be implemented is available in the older `r0.4.0 version <https://matrix.org/docs/spec/client_server/r0.4.0.html#cas-based-client-login>`_
of this specification.

Handling the redirect endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When responding to the ``/login/sso/redirect`` endpoint, the server must
generate a URI for the SSO login page with any appropriate parameters.

.. TODO-spec:

   It might be nice if the server did some validation of the ``redirectUrl``
   parameter, so that we could check that aren't going to redirect to a non-TLS
   endpoint, and to give more meaningful errors in the case of
   faulty/poorly-configured clients.

Handling the authentication endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the homeserver has verified the user's identity with the SSO system, it
MUST map the user ID to a valid `Matrix user identifier <../index.html#user-identifiers>`_.
The guidance in `Mapping from other character sets
<../index.html#mapping-from-other-character-sets>`_ may be useful.

If the generated user identifier represents a new user, it should be registered
as a new user.

Finally, the server should generate a short-term login token. The generated
token should be a macaroon, suitable for use with the ``m.login.token`` type of
the |/login|_ API, and `token-based interactive login <#token-based>`_. The
lifetime of this token SHOULD be limited to around five seconds. This token is
given to the client via the ``loginToken`` query parameter previously mentioned.


.. |/login| replace:: ``/login``
.. _/login: #post-matrix-client-%CLIENT_MAJOR_VERSION%-login
.. |/login/sso/redirect| replace:: ``/login/sso/redirect``
.. _/login/sso/redirect: #get-matrix-client-%CLIENT_MAJOR_VERSION%-login-sso-redirect
