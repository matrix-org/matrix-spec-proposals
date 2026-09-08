# MSC4149: Update CSP Directives for Media Repository

## Introduction

The current Content Security Policy (CSP) directives recommended for the media repository in the
Matrix specification contain outdated and potentially insecure directives. This proposal aims to
update these directives to enhance security and align with modern web standards.

## Proposal

The current CSP directives for the media repository are as follows:

```plaintext
sandbox; default-src 'none'; script-src 'none'; plugin-types application/pdf;
style-src 'unsafe-inline'; object-src 'self';
```

The proposed changes are to update the CSP directives to:

```plaintext
sandbox; default-src 'none'; script-src 'none'; font-src 'none';
frame-ancestors 'none'; form-action 'none'; base-uri 'none';
```

### Details of the Proposal

#### Remove `plugin-types application/pdf;`

Modern browsers no longer use the `plugin-types` directive. It was originally intended for use with
legacy plugins such as those for PDF viewing, which are no longer common practice. Furthermore,
[MSC2702](https://github.com/matrix-org/matrix-doc/pull/2702) recommends against the use of PDFs,
making this directive unnecessary and potentially misleading.

References:

- [CSP recommendations by Mozilla Security](https://infosec.mozilla.org/guidelines/web_security#content-security-policy)
- [XMPP's XEP-0363 on CSP](https://xmpp.org/extensions/xep-0363.html#server)

#### Remove `style-src 'unsafe-inline';`

The directive `style-src 'unsafe-inline';` allows the use of inline styles. While this may be
convenient, it poses a significant security risk by enabling potential Cross-Site Scripting (XSS)
attacks. By removing this directive, we enforce the use of external stylesheets, which are safer
and more manageable.

References:

- [Google's CSP validator](https://csp-evaluator.withgoogle.com/)
- [internet.nl's website security tester on CSP](https://internet.nl/faqs/appsecpriv/)

#### Remove `object-src 'self';`

The `object-src` directive is related to the use of `<object>` elements, which are also a legacy
feature. This directive is largely obsolete as modern web development practices do not rely on
`<object>` elements. Additionally, removing this directive simplifies the CSP and eliminates
potential attack vectors.

References:

- [CSP recommendations by Mozilla Security](https://infosec.mozilla.org/guidelines/web_security#content-security-policy)

### New CSP Directives

The updated CSP directives aim to provide a more secure baseline by eliminating unnecessary and
insecure directives. The new set of directives is:

```plaintext
sandbox; default-src 'none'; script-src 'none'; font-src 'none';
frame-ancestors 'none'; form-action 'none'; base-uri 'none';
```

These directives ensure that:

- No content is allowed to load by default (`default-src 'none';`).
- No fonts can be loaded (`font-src 'none';`).
- No scripts can be executed (`script-src 'none';`).
- The content cannot be embedded into other sites (`frame-ancestors 'none';`).
- Forms cannot be submitted (`form-action 'none';`).
- The document’s base URL cannot be overridden (`base-uri 'none';`).

## Potential Issues

### Developer Adaptation

This Content Security Policy is already in use on a number of live homeservers as it reflects
modern web application design, and specifically modern Matrix client usage. As such, it is not
expected that developers will need to make any changes, and this policy may in fact protect users
from developer error.

## Alternatives

One alternative is to maintain the current CSP directives, accepting the associated security risks
and reliance on outdated web standards. However, this approach would not align with the goal of
improving the security posture of the Matrix media repository.

Another alternative could be to adopt a more permissive CSP, but this would compromise security and
increase the risk of XSS attacks and other vulnerabilities.

## Security Considerations

The primary goal of updating these CSP directives is to enhance security. By removing obsolete
directives and disallowing insecure practices such as inline styles, we reduce the risk of XSS
attacks and other vulnerabilities. The new directives provide a stricter and more secure baseline
for handling content in the media repository.

## Unstable Prefix

This proposal does not introduce new endpoints or features requiring an unstable prefix.
The changes are confined to the update of CSP directives, which should be implemented directly
once approved.

## Dependencies

This MSC builds on the understanding and practices outlined in
[MSC2702](https://github.com/matrix-org/matrix-doc/pull/2702), which recommends against the use
of certain media types, such as PDFs. There are no other direct dependencies for this proposal.
