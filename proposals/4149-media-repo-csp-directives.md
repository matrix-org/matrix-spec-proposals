# MSC4149: Update CSP Directives for Media Repository

## Introduction

The current Content Security Policy (CSP) directives recommended for the media repository in the
Matrix specification contain outdated and potentially insecure directives. This proposal aims to
update these directives to enhance security and align with modern web standards.

The issues with the existing directives are as follows:

1. `plugin-types application/pdf;` is a legacy directive that modern browsers do not use, and PDFs
   are not allowed as per MSC2702.
2. `style-src 'unsafe-inline';` allows inline CSS, which poses security risks.
3. `object-src 'self';` relates to legacy web plugins and the `<object>` element, which are
   deprecated and under consideration for removal.

Updating these directives will improve the security posture of the Matrix media repository and
ensure compliance with contemporary web practices.

## Proposal

### Remove `plugin-types application/pdf;`

Modern browsers no longer use the `plugin-types` directive. This directive is redundant given the
deprecation of web plugins and is unnecessary since MSC2702 explicitly disallows PDFs.

### Update `style-src` Directive

The current directive is:

```plaintext
style-src 'unsafe-inline';
```

The proposed directive is:

```plaintext
style-src 'self';
```

Allowing `'unsafe-inline'` poses a significant security risk by enabling inline CSS, which can be
exploited for Cross-Site Scripting (XSS) attacks. Restricting `style-src` to `'self'` ensures that
styles are only loaded from the same origin, enhancing security.

### Remove `object-src 'self';`

The `object-src` directive pertains to legacy web plugins, which are deprecated. The use of
`<object>` elements is being reconsidered for removal, rendering this directive obsolete.

### Proposed CSP Directive

After the proposed changes, the updated CSP directive for the media repository would be:

```plaintext
Content-Security-Policy: default-src 'self'; style-src 'self';
```

## Potential issues

Updating CSP directives could potentially cause issues for implementations that rely on the
outdated directives. However, these changes should not adversely impact existing implementations as
the directives being removed or modified are related to deprecated features. Developers should
verify that their applications do not rely on these outdated directives.

## Alternatives

One alternative is to maintain the current CSP directives, accepting the associated security risks
and reliance on outdated web standards. However, this approach would not align with the goal of
improving the security posture of the Matrix media repository.

Another alternative could be to adopt a more permissive CSP, but this would compromise security and
increase the risk of XSS attacks and other vulnerabilities.

## Security considerations

Removing outdated directives and disallowing inline styles reduces the attack surface and mitigates
potential XSS attacks. These changes align with security best practices and ensure compliance with
modern web standards.

## Unstable prefix

As no actual functionality changes are proposed in any Matrix endpoints, it's not anticipated that
an unstable prefix is necessary.

## Dependencies

This MSC builds on [MSC2702](https://github.com/matrix-org/matrix-doc/pull/2702), which disallows
PDFs. No additional dependencies are identified at the time of writing.
