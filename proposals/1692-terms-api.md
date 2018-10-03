# Terms of service / privacy policy API

Homeservers may wish to force users to accept a set of policies or otherwise have
users be aware of changes to the terms of service, privacy policy, or other document.
This proposal describes a "Terms API" that gives homeservers the option of enforcing
a terms of service (or other legal document) upon a user before they can use the service.


# General principles and motivation

* The homeserver should be able to support multiple documents (ie: a TOS, privacy policy,
  and acceptable use policy).
* The policies should be versioned.
* The homeserver should be able to prevent use of the service if a given version of a document
  has not been accepted.

The primary use of this functionality is to address a user experience issue in most clients
where they are not aware of the terms of service until after they've registered. Given the
terms of service can change at any time, having a versioned set of documents is required to
ensure everyone has accepted the updated terms of service. Homeservers should additionally
be able to decide if the given change to their terms of service requires everyone to accept
the new terms or if no action is required by users.

The version for a policy should be arbitrary and potentially non-linear, similar to room
versions. The acceptable range of characters for a version is `[a-zA-Z0-9.-]`.


# UI authentication changes

This API makes changes to the registration and login flows for UI auth, and makes use of UI
auth at a later stage in this proposal.


## Registration

During registration it may be important to the homeserver that the user accepts a given policy.
This is described as a `m.login.terms` authentication type. The parameters for this login type
are:

```json
{
    "policies": [
        {
            "name": "Terms of Service",
            "url": "https://example.org/somewhere/terms.html",
            "version": "1.2"
        },
        {
            "name": "Privacy Policy",
            "url": "https://example.org/somewhere/privacy.html",
            "version": "1.2"
        }
    ]
}
```

The `name` of a policy is human-readable name for the document. The `url` may point to any
location. The `version` is provided for convenience to the client. The `name` must also be
unique amongst the policies.

Policies supplied via this method are implied to be required and therefore blocking for the
registration to continue.

The client is not required to supply any additional information in the auth dict to complete
this stage. The client should present the user with a checkbox to accept each policy with a
link to said policy, or otherwise rely on the homeserver's fallback.


## Login

Similar to registration, the homeserver may provide a required `m.login.terms` stage with the
same information. Because the homeserver is not aware of who is trying to authenticate until
after UI auth is started, the homeserver should present the latest version of each policy in
the login terms stage, and have the login terms stage be one of the last stages in the flow.
Once the homeserver is reasonably certain about who is authorizing themselves, the homeserver
should determine if the user has already accepted the policies they need to. If they have,
the homeserver should append the stage to the `completed` array, or by skipping to the end of
the UI auth process if possible. Under the current specified API, this is already possible
for a homeserver to do and therefore should not require changes to clients.


# Asking for acceptance after login/registration

The homeserver should maintain a read-only `m.terms` account data event with `content` similar
to:

```json
{
    "accepted": [
        {
            "name": "Terms of Service",
            "url": "https://example.org/somewhere/terms.html",
            "version": "1.2"
        },
        {
            "name": "Privacy Policy",
            "url": "https://example.org/somewhere/privacy.html",
            "version": "1.2"
        }
    ],
    "pending": [
        {
            "name": "Terms of Service",
            "url": "https://example.org/somewhere/terms-2.html",
            "version": "2.0",
            "required": true
        },
        {
            "name": "Code of Conduct",
            "url": "https://example.org/somewhere/code-of-conduct.html",
            "version": "1.0",
            "required": false
        }
    ]
}
```

In this example, the user has already accepted the Terms of Service v1.2 and Privacy Policy v1.2,
but has not signed the new Terms of Service or accepted the Code of Conduct. This provides homeservers
with a way to communicate new policies as well as updates to policies. Because the `name` is unique
amongst policies, the client can determine whether a policy is being updated or introduced. The
homeserver will push this account data event to the client as it would for any other account data
event.

The `required` boolean indicates whether the homeserver is going to prevent use of the account (without
logging the user out) by responding with a 403 `M_TERMS_NOT_SIGNED` error. The error will include an
additional `policy` property like in the following example:

```json
{
    "errcode": "M_TERMS_NOT_SIGNED",
    "error": "Please sign the terms of service",
    "policy": {
        "name": "Terms of Service",
        "url": "https://example.org/somewhere/terms-2.html",
        "version": "2.0"
    }
}
```

The homeserver should not prevent the use of `/sync` (and similar endpoints) but may withhold any
event that is not an update to the `m.terms` account data event. This is to ensure that clients
are not left in the dark when another client for the user accepts the terms of service, or when
the user accepts the terms elsewhere.

In addition, the homeserver should not prevent the use of the special "terms acceptance" API
described in the next section.


## Terms acceptance API

One way to accept the terms of service is to force the user to log in again, however that is
likely to be less than desireable for most users. Instead, the client may make a request to
`/_matrix/client/r0/terms` using the user-interactive authentication approach with a valid
access token. The homeserver may decide which additional stages it wants the user to complete
but must at least include the `m.login.terms` stage in every flow. The behaviour of the stage
is exactly the same as how it works for registering an account: the policies the homeserver
wants the user to accept are provided as the parameters for the stage, which should include
policies that are `"required": false` in the user's account data. This is because the same
API is used by the client to acknowledge a non-blocking policy (such as the Code of Conduct
in the prior example).


# Why use account data and not a special /sync property or polling API?

The user's account data was picked because (almost) every client is aware of the concept and
requires few changes to support it. Many clients additionally have optimized the lookup for
account data via caching, making the information essentially always available. If
[MSC1339](https://github.com/matrix-org/matrix-doc/issues/1339) were to be approved, this
lookup becomes even easier.

Clients are almost certainly going to want to show the information somewhere in their UI,
sometimes due to a legal requirement. The information should therefore be easily accessible.

A special key in `/sync` was not picked because it leads to clients having to support yet
another field on the sync response. It would also require clients that don't sync to sync,
which should not be the case (although currently they would until MSC1339 lands anyways).

A dedicated API for the client to poll against was also not picked due to similar reasons.
The client shouldn't have to poll yet another API just for policies.
