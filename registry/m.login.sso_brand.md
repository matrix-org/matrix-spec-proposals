# `m.login.sso` `brand` identifier registry

The following is a list of identifiers for use in the optional `brand` field of the
`identity_providers` property of the response to the [`GET /_matrix/client/r0/login`
endpoint](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-login).

This field was originally proposed in
[MSC2858](https://github.com/matrix-org/matrix-doc/pull/2858).

Links to other organisations' branding guidelines are provided on an
informational basis, to help client developers understand the expected
behaviour. No guarantee is given as to their accuracy, and each client author
remains responsible for maintaining their application according to the latest
best practices.

## Assignments

<!--
Note that the following list is alphabetical by identifier - please keep it
that way!
-->

 * Identifier: `com.apple`
   Description: "Sign in with Apple". See
   https://developer.apple.com/design/human-interface-guidelines/sign-in-with-apple/overview/buttons/.
 * Identifier: `com.facebook`
   Description: "Continue with Facebook". See
   https://developers.facebook.com/docs/facebook-login/web/login-button/.
 * Identifier: `com.github`
   Description: Logos available at https://github.com/logos.
 * Identifier: `com.gitlab`:
   Description: Login in via the hosted https:/gitlab.com SaaS platform.
 * Identifier: `com.google`:
   Description: "Sign in with Google". See
   https://developers.google.com/identity/branding-guidelines.
 * Identifier: `com.twitter`
   Description: "Log in with Twitter". See
   https://developer.twitter.com/en/docs/authentication/guides/log-in-with-twitter#tab1.



## Requesting updates to the list

Members of the community wishing to add new brands to this list are encouraged
to open a pull request to update the list.

Contributors are reminded that identifiers for the `brand` field should follow
the [common textual identifier
grammar](https://github.com/matrix-org/matrix-doc/blob/rav/proposals/textual_identifier_grammar/proposals/2758-textual-id-grammar.md).
