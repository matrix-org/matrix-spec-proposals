Macaroon Caveats
================

`Macaroons`_ are issued by Matrix servers as authorization tokens. Macaroons may be restricted by adding caveats to them.

.. _Macaroons: http://theory.stanford.edu/~ataly/Papers/macaroons.pdf

Caveats can only be used for reducing the scope of a token, never for increasing it. Servers are required to reject any macroon with a caveat that they do not understand.

Some caveats are specified in this specification, and must be understood by all servers. The use of non-standard caveats is allowed.

All caveats must take the form::

  key operator value

where:
 - ``key`` is a non-empty string drawn from the character set [A-Za-z0-9_]
 - ``operator`` is a non-empty string which does not contain whitespace
 - ``value`` is a non-empty string
 
And these are joined by single space characters.

Specified caveats:

+-------------+--------------------------------------------------+------------------------------------------------------------------------------------------------+
| Caveat name | Description                                      | Legal Values                                                                                   |
+=============+==================================================+================================================================================================+
| gen         | Generation of the macaroon caveat spec.          | 1                                                                                              |
+-------------+--------------------------------------------------+------------------------------------------------------------------------------------------------+
| user_id     | ID of the user for which this macaroon is valid. | Pure equality check. Operator must be =.                                                       |
+-------------+--------------------------------------------------+------------------------------------------------------------------------------------------------+
| type        | The purpose of this macaroon.                    | - ``access``: used to authorize any action except token refresh                                |
|             |                                                  | -  ``refresh``: only used to authorize a token refresh                                         |
|             |                                                  | - ``login``: issued as a very short-lived token by third party login flows; proves that        |
|             |                                                  |   authentication has happened but doesn't grant any privileges other than being able to be     |
|             |                                                  |   exchanged for other tokens.                                                                  |
+-------------+--------------------------------------------------+------------------------------------------------------------------------------------------------+
| time        | Time before/after which this macaroon is valid.  | A POSIX timestamp in milliseconds (in UTC).                                                    |
|             |                                                  | Operator < means the macaroon is valid before the timestamp, as interpreted by the server.     |
|             |                                                  | Operator > means the macaroon is valid after the timestamp, as interpreted by the server.      |
|             |                                                  | Operator == means the macaroon is valid at exactly the timestamp, as interpreted by the server.|
|             |                                                  | Note that exact equality of time is largely meaningless.                                       |
+-------------+--------------------------------------------------+------------------------------------------------------------------------------------------------+
