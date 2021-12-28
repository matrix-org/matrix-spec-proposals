# Proposal for mandating case folding when processing e-mail addresses

[RFC822](https://tools.ietf.org/html/rfc822#section-3.4.7) mandates that
localparts in e-mail addresses must be processed with the original case
preserved. [The Matrix spec](https://matrix.org/docs/spec/appendices#pid-types)
doesn't mandate anything about processing e-mail addresses, other than the fact
that the domain part must be converted to lowercase, as domain names are case
insensitive.

On the other hand, most major e-mail providers nowadays process the localparts
of e-mail addresses as case insensitive. Therefore, most users expect localparts
to be treated case insensitively, and get confused when it's not. Some users,
for example, get confused over the fact that registering a 3PID association for
`john.doe@example.com` doesn't mean that the association is valid for
`John.Doe@example.com`, and don't expect to have to remember the exact
case they used to initially register the association (and sometimes get locked
out of their account because of that). So far we've seen that confusion occur
and lead to troubles of various degrees over several deployments of Synapse and
Sydent.

## Proposal

This proposal suggests changing the specification of the e-mail 3PID type in
[the Matrix spec appendices](https://matrix.org/docs/spec/appendices#pid-types)
to mandate that, before any processing, e-mail addresses must go through a full
case folding as described under "Caseless Matching" in
[chapter 5 of the unicode standard](https://www.unicode.org/versions/Unicode13.0.0/ch05.pdf#G21790), on top of
having their domain lowercased.

This means that `Strauß@Example.com` must be considered as being the same e-mail
address as `strauss@example.com`.

## Other considered solutions

A first look at this issue concluded that there was no need to add such a
mention to the spec, and that it can be considered an implementation detail.
However, [MSC2134](https://github.com/matrix-org/matrix-doc/pull/2134) changes
this: because hashing functions are case sensitive, we need both clients and
identity servers to follow the same policy regarding case sensitivity.

An initial version of this proposal proposed to mandate lowercasing e-mail
addresses instead of case folding them, however it was pointed out that this
solution might not be the best and most future-proof one.

Unicode normalisation was also looked at but judged unnecessary.

## Tradeoffs

Implementing this MSC in identity servers and homeservers might require the
databases of existing instances to be updated in a large part to case fold the
email addresses of existing associations, in order to avoid conflicts. However,
most of this update can usually be done by a background job running at startup,
so the UX improvement outweighs this trouble.

## Potential issues

### Conflicts with existing associations

Some users might already have two different accounts associated with the same
e-mail address but with different cases. This appears to happen in a small
number of cases, however, and can be dealt with by the identity server's or the
homeserver's maintainer.

For example, with Sydent, the process of dealing with such cases could look
like:

1. list all MXIDs associated with a variant of the email address, and the
   timestamp of that association
2. delete all associations except for the most recent one [0]
3. inform the user of the deletion by sending them an email notice to the email
   address

### Storing and querying

Most database engines don't support case folding, therefore querying all
e-mail addresses matching a case folded e-mail address might not be trivial,
e.g. an identity server querying all associations for `strauss@example.com` when
processing a `/lookup` request would be expected to also get associations for
`Strauß@Example.com`.

To address this issue, implementation maintainers are strongly encouraged to
make e-mail addresses go through a full case folding before storing them.

### Implementing case folding

The need for case folding in services on the Internet doesn't seem to be very
large currently (probably due to its young age), therefore there seem to be only
a few third-party implementation libraries out there. However, both
[Go](https://godoc.org/golang.org/x/text/cases#Fold), [Python
2](https://docs.python.org/2/library/stringprep.html#stringprep.map_table_b3)
and [Python 3](https://docs.python.org/3/library/stdtypes.html#str.casefold)
support it natively, and [a third-party JavaScript
implementation](https://github.com/ar-nelson/foldcase) exists which, although
young, seems to be working.

## Footnotes

[0]: This is specific to Sydent because of a bug it has where v1 lookups are
already processed case insensitively, which means it will return the most recent
association for any case of the given email address, therefore keeping only this
association won't change the result of v1 lookups.
