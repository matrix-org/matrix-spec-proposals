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

Central Authentication Service (CAS) is a web-based single sign-on protocol.

Client behaviour
----------------

An overview of the process, as used in Matrix, is as follows:

1. The Matrix client instructs the user's browser to navigate to the
   |/login/cas/redirect|_ endpoint on the user's homeserver.

2. The homeserver responds with an HTTP redirect to the CAS user interface,
   which the browser follows.

3. The CAS system authenticates the user.

4. The CAS server responds to the user's browser with a redirect back to the
   |/login/cas/ticket|_ endpoint on the homeserver, which the browser
   follows. A 'ticket' identifier is passed as a query-parameter in the
   redirect.

5. The homeserver receives the ticket ID from the user's browser, and makes a
   request to the CAS server to validate the ticket.

6. Having validated the ticket, the homeserver responds to the browser with a
   third HTTP redirect, back to the Matrix client application. A login token
   is passed as a query-parameter in the redirect.

7. The Matrix client receives the login token and passes it to the |/login|_
   API.

If successful, the user is redirected back to the client via the redirectUrl given to the
homeserver on the initial redirect request. In the url will be a loginToken query parameter
which contains a Matrix login token which the client should then use to complete the login
via the Token-based process described above.


{{cas_login_redirect_cs_http_api}}
{{cas_login_ticket_cs_http_api}}


.. |/login| replace:: ``/login``
.. _/login: #post-matrix-client-%CLIENT_MAJOR_VERSION%-login
.. |/login/cas/redirect| replace:: ``/login/cas/redirect``
.. _/login/cas/redirect: #get-matrix-client-%CLIENT_MAJOR_VERSION%-login-cas-redirect
.. |/login/cas/ticket| replace:: ``/login/cas/ticket``
.. _/login/cas/ticket: #get-matrix-client-%CLIENT_MAJOR_VERSION%-login-cas-ticket
