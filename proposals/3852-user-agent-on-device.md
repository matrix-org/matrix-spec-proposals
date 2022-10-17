# MSC3852: Expose user agent information on `Device`

Currently, sessions are only easily recognisable by their `device_name`. Depending on client implementation, this may
include some stringified information about the session. (For example, Element web uses `'%(appName)s (%(browserName)s,
%(osName)s)'`). This information can become stale, and if edited by the user any device detail is lost.

By exposing more detailed and up to date session information, users will be able to more easily recognise their
sessions. This gives users  more confidence in removing stale or suspicious sessions.

## Proposal
Homeservers already record the user agent per session today to expose it in the admin API [GET
/_matrix/client/v3/admin/whois/{userId}](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3adminwhoisuserid).
This MSC proposes exposing the latest recorded user agent as `last_seen_user_agent` on the `Device` model returned by
Client-Server API endpoints [GET
/_matrix/client/v3/devices](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3devices) and [GET
/_matrix/client/v3/devices/{deviceId}](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3devices).

```jsonp
{
  "device_id": "QBUAZIFURK",
  "display_name": "android",
  "last_seen_ip": "1.2.3.4",
  "last_seen_ts": 1474491775024,
  "last_seen_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}
```

## Alternatives
N/A

## Security considerations
The user agent is currently only exposed in the admin API and following this MSC would be accessible to normal users.
The `/devices` endpoints only return device information for the current user, so this is not a concern.


## Unstable prefix
While this MSC is not included in the spec `last_seen_user_agent` should use the unstable prefix
`org.matrix.msc3852.last_seen_user_agent`
