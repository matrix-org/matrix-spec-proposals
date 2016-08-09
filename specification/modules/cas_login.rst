.. Copyright 2016 OpenMarket Ltd
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

CAS-based client login
======================

.. _module:cas_login:

`Central Authentication Service
<https://github.com/apereo/cas/blob/master/cas-server-documentation/protocol/CAS-Protocol-Specification.md>`_
(CAS) is a web-based single sign-on protocol.

An overview of the process, as used in Matrix, is as follows:

1. The Matrix client instructs the user's browser to navigate to the
   |/login/cas/redirect|_ endpoint on the user's homeserver.

2. The homeserver responds with an HTTP redirect to the CAS user interface,
   which the browser follows.

3. The CAS system authenticates the user.

4. The CAS server responds to the user's browser with a redirect back to the
   |/login/cas/ticket|_ endpoint on the homeserver, which the browser
   follows. A 'ticket' identifier is passed as a query parameter in the
   redirect.

5. The homeserver receives the ticket ID from the user's browser, and makes a
   request to the CAS server to validate the ticket.

6. Having validated the ticket, the homeserver responds to the browser with a
   third HTTP redirect, back to the Matrix client application. A login token
   is passed as a query parameter in the redirect.

7. The Matrix client receives the login token and passes it to the |/login|_
   API.

Client behaviour
----------------

The client starts the process by instructing the browser to navigate to
|/login/cas/redirect|_ with an appropriate ``redirectUrl``. Once authentication
is successful, the browser will be redirected to that ``redirectUrl``.

.. TODO-spec

   Should we recommend some sort of CSRF protection here (specifically, we
   should guard against people accidentally logging in by sending them a link
   to ``/login/cas/redirect``.

   Maybe we should recommend that the ``redirectUrl`` should contain a CSRF
   token which the client should then check before sending the login token to
   ``/login``?

{{cas_login_redirect_cs_http_api}}
{{cas_login_ticket_cs_http_api}}

Server behaviour
----------------

The URI for the CAS system to be used should be configured on the server by the
server administrator.

Handling the redirect endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When responding to the ``/login/cas/redirect`` endpoint, the server must
generate a URI for the CAS login page. The server should take the base CAS URI
described above, and add a ``service`` query parameter. This parameter MUST be
the URI of the ``/login/cas/ticket`` endpoint, including the ``redirectUrl``
query parameter. Because the homeserver may not know its base URI, this may
also require manual configuration.

.. TODO-spec:

   It might be nice if the server did some validation of the ``redirectUrl``
   parameter, so that we could check that aren't going to redirect to a non-TLS
   endpoint, and to give more meaningful errors in the case of
   faulty/poorly-configured clients.

Handling the authentication endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When responding to the ``/login/cas/ticket`` endpoint, the server MUST make a
request to the CAS server to validate the provided ticket. The server MAY also
check for certain user attributes in the response. Any required attributes
should be configured by the server administrator.

Once the ticket has been validated, the server MUST map the CAS ``user_id``
to a valid `Matrix user identifier <../intro.html#user-identifiers>`_. The
guidance in `Mapping from other character sets
<../intro.html#mapping-from-other-character-sets>`_ may be useful.

If the generated user identifier represents a new user, it should be registered
as a new user.

Finally, the server should generate a short-term login token. The generated
token should be a macaroon, suitable for use with the ``m.login.token`` type of
the |/login|_ API, and `token-based interactive login <#token-based>`_. The
lifetime of this token SHOULD be limited to around five seconds.


.. |/login| replace:: ``/login``
.. _/login: #post-matrix-client-%CLIENT_MAJOR_VERSION%-login
.. |/login/cas/redirect| replace:: ``/login/cas/redirect``
.. _/login/cas/redirect: #get-matrix-client-%CLIENT_MAJOR_VERSION%-login-cas-redirect
.. |/login/cas/ticket| replace:: ``/login/cas/ticket``
.. _/login/cas/ticket: #get-matrix-client-%CLIENT_MAJOR_VERSION%-login-cas-ticket
