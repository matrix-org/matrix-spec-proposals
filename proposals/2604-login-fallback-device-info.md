# Parameters for Login Fallback

The [login fallback](https://matrix.org/docs/spec/client_server/r0.6.1#login-fallback)
API can be used by clients to support logins that they do not recognize. It is
expected to be loaded in a web view and calls a JavaScript function
(`window.onLogin`) when the login process is complete.

Since the login fallback page does the full login process there is no 
opportunity for the application to provide a device ID (to re-authenticate
an expired session in the [case of soft-logout](https://matrix.org/docs/spec/client_server/r0.6.1#soft-logout))
or an [initial device display name](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-login)
(in the case of an initial login). This causes a few issues:

* It can make it difficult for a user to manage their sessions (as additional
  sessions get created for each soft-logout).
* Cross-signing information gets reset when a new device ID is returned from the
  login process. This results in users needing to re-validate their device. 

## Proposal

The login fallback page will accept query parameters for non-credential related
parameters of the login endpoint. These will be forwarded by the login fallback
API to the login API throughout the login process. Currently the following
parameters should be accepted:

* `device_id`
* `initial_device_display_name`


## Potential issues

There are no backwards compatibility concerns: if a client provides the query
parameters to a homeserver that does not check for them than the current
behavior will occur.


## Security considerations

None.
