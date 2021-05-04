# SSO IdP brand registry

This informal document contains specification for common brands that clients might experience
in the wild as part of `m.login.sso` flows. To add your brand, open a PR against this document
with the relevant additions (using the existing specification as reference) - an MSC is not
required. Once opened, mention your PR in [#sct-office:matrix.org](https://matrix.to/#/#sct-office:matrix.org)
on Matrix so it doesn't end up lost.

Please also take some time to read the [contributing guidelines](https://github.com/matrix-org/matrix-doc/blob/master/CONTRIBUTING.rst)
for an overview of PR requirements.

<!--
Author's note: This document intentionally has 2 blank lines between brands for easier distinction
in the plaintext version. Please maintain them for new & existing brands.
-->

## Brands

For the brands listed here, the `identifier` would be used as the `brand` value in an IdP definition
under `m.login.sso`'s flow.

Note that each brand may have their own requirements for how they are represented by clients, such as
Facebook/Twitter wanting their signature blues for button backgrounds whereas GitHub is not as particular
about the press requirements. Clients should not rely on this document for guidance on press requirements
and instead refer to the brands individually.


### Apple

**Identifier**: `apple`

Suitable for "Sign in with Apple": see https://developer.apple.com/design/human-interface-guidelines/sign-in-with-apple/overview/buttons/.


### Facebook

**Identifier**: `facebook`

"Continue with Facebook": see https://developers.facebook.com/docs/facebook-login/web/login-button/.


### GitHub

**Identifier**: `github`

Logos available at https://github.com/logos.


### GitLab

**Identifier**: `gitlab`

Logos available at https://about.gitlab.com/press/press-kit/.


### Google

**Identifier**: `google`

Suitable for "Google Sign-In": see https://developers.google.com/identity/branding-guidelines.


### Twitter

**Identifier**: `twitter`

Suitable for "Log in with Twitter": see https://developer.twitter.com/en/docs/authentication/guides/log-in-with-twitter#tab1.
