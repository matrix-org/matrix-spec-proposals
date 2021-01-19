# MSC2874: Single SSSS

[Secure Secret Storage and
Sharing](https://github.com/matrix-org/matrix-doc/pull/1946) (SSSS) was
designed to allow the user to create multiple keys that would be able to
decrypt different subsets of the secrets.  However, the vast majority of users
do not need this feature.

This proposal defines how clients should behave if they only wish to support a
single key, by defining which key clients should use if multiple keys are
present.  It also makes the `name` field in the `m.secret_storage.key.*` events
optional, as this field was mainly added to allow a user to select between
different keys.

## Proposal

If a client wants to present a simplified interface to users by not supporting
multiple SSSS keys, then the client should use the default key (the key listed
in the `m.secret_storage.default_key` account data event.)  If there is no
default key the client may behave as if there is no SSSS key at all.  When such
a client creates an SSSS key, it must mark that key as being the default key.

The `name` field in the `m.secret_storage.key.*` account data events is
optional, rather than required.  If a client wishes to display multiple keys to
a user and a given key does not have a `name` field, the client may use a
default name as the key's name, such as "Unnamed key", or "Default key" if the
key is marked as default.

## Potential issues

If secrets are encrypted using a key that is not marked as default, a client
might not decrypt the secrets, even if it would otherwise be able to.

## Alternatives

Rather than solely relying on the key marked as default, a client could guess
at what key to use.  For example, it could look at the secrets that it needs,
see what keys they are encrypted with, and if there is only one common key,
then it could use that.  (This is what Element currently does.)  Or if there
are multiple keys, it could use some sort of heuristic to pick a key.  However,
this approach can be error-prone, and it is better to rely on an explicit
marking.

## Security considerations

None

## Unstable prefix

An unstable prefix is not needed for a behaviour change in choosing the key to
use as there are no event/endpoint changes.

Some clients already omit the `name` field (notably, matrix-js-sdk
unintentionally does this -- mea culpa), and this does not seem to be causing
issues, so an unstable prefix seems unnecessary for this.
