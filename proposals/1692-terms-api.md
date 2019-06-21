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
This is described as a `m.login.terms` authentication type. The parameters for this authentication
type are:

```json
{
    "policies": {
        "terms_of_service": {
            "version": "1.2",
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-1.2-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-1.2-fr.html"
            }
        },
        "privacy_policy": {
            "version": "1.2",
            "en": {
                "name": "Privacy Policy",
                "url": "https://example.org/somewhere/privacy-1.2-en.html"
            },
            "fr": {
                "name": "Politique de confidentialité",
                "url": "https://example.org/somewhere/privacy-1.2-fr.html"
            }
        }
    }
}
```

Policies have a unique identifer represented by the key under `policies`. The `version` is
provided as a convience to the client, and is alongside the different language options for
each of the policies. The `name` of a policy is human-readable name for the document. The
`url` may point to any location. The implicit ID may only contain characters in `[a-zA-Z0-9_]`.

Policies supplied via this method are implied to be required and therefore blocking for the
registration to continue.

The client is not required to supply any additional information in the auth dict to complete
this stage. The client should present the user with a checkbox to accept each policy with a
link to said policy, or otherwise rely on the homeserver's fallback.


## Login

Given the Client-Server specification doesn't use UI auth on the login routes, mimicking the
process used for registration is more difficult. The homeserver would not be aware of who is
logging in prior to the user submitting their details (eg: token, password, etc) and therefore
cannot provide exact details on which policies the user must accept as part of the initial login
process. Instead, the login endpoints should be brought closer to how UI auth works using the
following process:

1. The client requests the login flows (unchanged behaviour) - policies are not referenced yet.
2. The client submits the user's details (eg: password) to the homeserver (unchanged behaviour).
3. If the credentials are valid, the homeserver checks if the user has any required policies to
   accept. If the user does not have any pending policies, skip to step 6.
4. The homeserver responds with a 401 as per the UI auth requirements (an `errcode` of `M_FORBIDDEN`
   and `error` saying something like `"Please accept the terms and conditions"`). The `completed`
   stages would have the user's already-accepted step listed (eg: `m.login.password`). The
   `m.login.terms` authentication type shares the same data structure as the one used during
   registration.
5. The client submits the request again as if it were following the UI auth requirements (ie: for
   the purpose of `m.login.terms`, submitting an empty auth dict).
6. The homeserver logs the user in by generating a token and returning it to the client as per
   the specification.

This process is chosen to begin introducing the UI auth mechanism to login without breaking clients.
In the future, the login endpoints should be migrated fully to use UI auth instead of a different
approach. By nature of having the homeserver return a 401 when the user must accept terms before
continuing, older clients will not be able to work around the limitation. Modern clients would be
expected to support the UI auth flow (after the initial password submission), therefore allowing
the user to actually log in.

# Asking for acceptance after login/registration

The homeserver should maintain a read-only `m.terms` account data event with `content` similar
to:

```json
{
    "accepted": {
        "terms_of_service": {
            "version": "1.2",
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-1.2-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-1.2-fr.html"
            }
        },
        "privacy_policy": {
            "version": "1.2",
            "en": {
                "name": "Privacy Policy",
                "url": "https://example.org/somewhere/privacy-1.2-en.html"
            },
            "fr": {
                "name": "Politique de confidentialité",
                "url": "https://example.org/somewhere/privacy-1.2-fr.html"
            }
        }
    },
    "pending": {
        "terms_of_service": {
            "version": "2.0",
            "required": true,
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-2.0-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-2.0-fr.html"
            }
        },
        "code_of_conduct": {
            "version": "1.0",
            "required": false,
            "en": {
                "name": "Code of Conduct",
                "url": "https://example.org/somewhere/code-of-conduct-1.0-en.html"
            },
            "fr": {
                "name": "Code de conduite",
                "url": "https://example.org/somewhere/code-of-conduct-1.0-fr.html"
            }
        }
    }
}
```

In this example, the user has already accepted the Terms of Service v1.2 and Privacy Policy v1.2,
but has not signed the new Terms of Service or accepted the Code of Conduct. This provides homeservers
with a way to communicate new policies as well as updates to policies. Because the `name` is unique
amongst policies, the client can determine whether a policy is being updated or introduced. The
homeserver will push this account data event to the client as it would for any other account data
event.

*Note*: [MSC2140](https://github.com/matrix-org/matrix-doc/pull/2140) requires the client to treat
URLs for policies returned by this API to be de-duplicated. The expectation is that clients will
continue to use this terms of service API to manage approval of policies with their homeserver and
consider duplicated policies from the identity server/integration manager where appropriate. Ultimately,
the client may end up making several requests to all 3 servers despite only rendering a single
checkbox for the user to click. This only applies to a post-MSC2140 world and does not otherwise
affect this proposal.

The `required` boolean indicates whether the homeserver is going to prevent use of the account (without
logging the user out) by responding with a 403 `M_TERMS_NOT_SIGNED` error. The error will include an
additional `policies` property like in the following example:

```json
{
    "errcode": "M_TERMS_NOT_SIGNED",
    "error": "Please sign the terms of service",
    "policies": {
        "terms_of_service": {
            "version": "2.0",
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-2.0-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-2.0-fr.html"
            }
        }
    }
}
```

The homeserver should not prevent the use of `/sync` (and similar endpoints) but may withhold any
event that is not an update to the `m.terms` account data event. If a server is witholding events,
it MUST set `withheld: true` as a top level field in the sync response. This is to ensure
that clients are not left in the dark when another client for the user accepts the terms of service,
or when the user accepts the terms elsewhere.

*Note*: `withheld` was chosen over `limited` due to `limited` already having special meaning in
the context of sync.

In addition, the homeserver should not prevent the use of the special "terms acceptance" API
described in the next section.


## Terms acceptance API

One way to accept the terms of service is to force the user to log in again, however that is
likely to be less than desireable for most users. Instead, the client may make a request to
`/_matrix/client/r0/terms` using the user-interactive authentication approach with a valid
access token. The homeserver may decide which additional stages it wants the user to complete
but must at least include the `m.login.terms` stage in every flow. The authentication type's
behaviour is exactly the same as how it works for registering an account: the policies the
homeserver wants the user to accept are provided as the parameters for the stage, which should
include policies that are `"required": false` in the user's account data. This is because the
same API is used by the client to acknowledge a non-blocking policy (such as the Code of Conduct
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
