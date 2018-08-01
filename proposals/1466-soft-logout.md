# Soft Remote Logout Proposal

## Motivation

Currently when a user logs out of riot, the app will destroy things like 
encryption keys. If the logout was done by the user in local app then it will 
have first prompted the user to export the encryption keys. However, when the
app is logged out remotely (i.e. it received a 401 from the server) there is no
oppurtunity to ask the user to backup the keys, resulting in those keys being
lost.

While this behaviour is useful in many circumstances, e.g. remote logging out a 
stolen/lost device, it also means that the server shouldn't automatically
logging out devices, to avoid users losing encryption keys.


## Proposal

A new parameter is added to the JSON body of 401 responses, called 
`soft_logout`. This is a boolean flag (defaulting to `false`) that signals to 
the client whether it should keep local data and simply propmpt to reauth (when
`true`) or to destroy the current data like it does today (when `false`).

The major disadvantage with this approach is that once the client is logged 
out, the user can no longer remotely cause the client to destroy the local
data. However, this is not substantially different from today where the app has
to be opened to receive remote logout requests (via 401), as it allows
attackers to get at encryption keys even after remote logout if they simply
avoid opening the app.


## Alternatives

One alternative is to force the user to enter a password for backing up keys 
when they enter the app, and then have the app keep secure backups of they
keys. This then means its safer to not delete the secure backups when the app
is logged out remotely.

