# MSC4078: Registering pushers against push notification services should forward back failures

## Background

It's quite common for push notification services to throw back various errors when trying to register a pusher. [The
spec](https://spec.matrix.org/v1.8/client-server-api/#post_matrixclientv3pushersset) doesn't currently specify that
those errors should be sent back to the client, letting it believe everything is fine. It handles missing
parameters in the request body and rate-limiting but nothing coming back from the push notification service.

The push notification service can decide to deny requests for a variety of reasons ranging from bad request and internal
errors to certificate and device token expirations e.g. [APNs errors](https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/handling_notification_responses_from_apns)

## Problem

We are getting reports that users are missing push notifications entirely which we tracked down to APNs returning 410s
behind the scenes. As the application is never informed about this there is no straight forward way for it to try to
re-register a pusher with a new device token. The application does try to update its pusher every time it becomes active
but that's no good if the token it's using is always the same.

## Proposal

The most straight forward solution would be to expose the underlying errors on POST `/pushers` to the final clients. We cannot know
beforehand what the actual push notification service used is so we shouldn't attempt to map errors but we should return Matrix specific ones.

As such, we introduce 2 new fields to the standard error response: 

* `upstream_errcode` (String) - upstream error code. Intentionally generic to allow for error codes other than HTTP
* `upstream_error` (String) - a description of the error, also generic. May not be a human readable string, such as HTML, XML, or encoded binary depending on the upstream system.

Example: 

```
{
  "errcode": "M_UNKNOWN",
  "error": "Unable to register pusher",
  "upstream_errcode": "410", // intentionally a string, to allow for `GOOG_FAIL` or whatever else goes on in the wild
  "upstream_error": "Words from the upstream about what a 410 actually means"
}
```

Homeservers can decide to sanitise the upstream errors but that normally shouldn't be the case.

Exposing these errors would allow the application to handle token expirations every time it would normally register a
pusher. For example if the app normally registers a pusher every time it becomes active then the number of users
realising push notifications are broken will drop significantly without the need to introduce more complex mechanisms.

## Alternatives

A option would be for the client to always GET `/pushers` after setting a new one and try to understand if the
underlying request succeeded or not. Doing that is not only cumbersome but it can also become non-trivial depending on
the homeserver implementation and when it decides to actually invoke the push notification service.

Another solution would be to expose notification service errors and homeserver side pusher deletions on the sync
responses which would indeed help handle more cases but also introduce a lot of complexity and extra traffic.

## Unstable prefix

Not required.