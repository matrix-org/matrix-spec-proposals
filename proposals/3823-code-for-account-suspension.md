# MSC3823: A code for account suspension

This MSC introduces a new error code that servers may send to clarify that an account has been
suspended *temporarily* but may still be reactivated.

## Proposal

### Introduction

Matrix has a code `M_USER_DEACTIVATED` that a server may return to describe an account that has been
deactivated. So far, this code has been used to represent accounts that have been *permanently*
deactivated. In particular, clients that interpret this error code display it imply that the account
has been *permanently* deactivated.

However, some countries (e.g. UK) have laws that require the ability to appeal account
deactivations. This requires the ability to specify that an account is *reversibly*
suspended and let users know about the appeals procedure.

This MSC simply introduces a new error code `M_USER_ACCOUNT_SUSPENDED` that servers may send to
clarify that an account has been suspended but that the solution may still be resolved either by
an appeal or by e.g. clearing up some abusive messages.

This MSC does *not* specify a mechanism to suspend or unsuspend the account or to handle appeals.

### Proposal

Introduce a new error code `M_USER_ACCOUNT_SUSPENDED`. This error code MAY be sent by the server
whenever a client attempts to use an API on behalf of a user whose account has been suspended.

| Name | Type | Value |
|------|------|-------|
| `href` | string | (optional) If specified, a URL containing more information for the user, such as action needed. |

The client is in charge of displaying an error message understandable by the user in case of `M_USER_ACCOUNT_SUSPENDED`,
as well as a link to `href`.

The web server serving `href` is in charge of localizing the message, using existing HTTP mechanisms,
to adapt the page to the end user's locale.

#### Examples

Returning a static page:

```json
{
  "errcode": "M_USER_ACCOUNT_SUSPENDED",
  "error": "The user account has been suspended, see link for details",
  "href": "https://example.org/help/my-account-is-suspended-what-can-i-do
}
```

Returning a dynamic page customized for this specific user:

```json
{
  "errcode": "M_USER_ACCOUNT_SUSPENDED",
  "error": "The user account has been suspended, see link for details",
  "href": "https://example.org/action-needed/please-redact-events?event-id=$event_1:example.org&event-id=$event_2:example.org
}
```


### Potential issues

See security considerations.

### Alternatives

We could reuse `M_USER_DEACTIVATED` and introduce an additional field:

| Name | Type | Value |
|------|------|-------|
| `permanent` | boolean | (optional) If `false`, the account may still be reactivated. |

in addition to the fields mentioned previously.

### Security considerations

This has the potential to expose private data.

To avoid this, any `M_USER_ACCOUNT_SUSPENDED` MUST NOT be sent without authentication.