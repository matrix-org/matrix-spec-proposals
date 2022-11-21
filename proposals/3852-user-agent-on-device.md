# MSC3852: Expose user agent information on `Device`

Currently, sessions are only easily recognisable by their `device_name`. Depending on client implementation, this may
include some stringified information about the session. (For example, Element web uses `'%(appName)s (%(browserName)s,
%(osName)s)'`). This information can become stale, and if edited by the user any device detail is lost.

By exposing more detailed and up to date session information, users will be able to more easily recognise their
sessions. This gives users  more confidence in removing stale or suspicious sessions.

## Proposal
Homeservers already record the user agent per session today to expose it in the admin API [GET
/_matrix/client/v3/admin/whois/{userId}](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3adminwhoisuserid).
This MSC proposes optionally exposing the latest recorded user agent as `last_seen_user_agent` on the `Device` model
returned by Client-Server API endpoints [GET
/_matrix/client/v3/devices](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3devices) and [GET
/_matrix/client/v3/devices/{deviceId}](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3devices). If
the user agent is not available, or the server chooses not to expose it, the value should be omitted from the response. 

| Name | Type | Description |
|------|------|-------------|
| `last_seen_user_agent` | string | **Optional** The latest recorded user agent for the session. 

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
### HTTP client hints
User agent strings are on their way to being [deprecated.](https://www.chromium.org/updates/ua-reduction/). Instead of
relying on UA string, the server could use [user agent hints](https://wicg.github.io/ua-client-hints/#http-ua-hints) to
record equivalent information about sessions.

A server should set an `Accept-CH: Sec-CH-UA, Sec-CH-UA-Mobile, Sec-CH-UA-Platform` header. When `Sec-CH-UA,
Sec-CH-UA-Mobile, Sec-CH-UA-Platform` headers are present in server requests the values should be saved against the
session. The latest recorded values should be exposed on the device model:

```jsonp
{
  "device_id": "QBUAZIFURK",
  "display_name": "android",
  "last_seen_ip": "1.2.3.4",
  "last_seen_ts": 1474491775024,
  "platform": "macOS",
  "isMobile": "false",
  "clientBrand": "Firefox",
  "clientVersion": "123"
}
```

[Not yet supported](https://caniuse.com/?search=Sec-CH-UA) on Firefox or Safari.

### Explicitly save client information from matrix clients on device model
Add optional client information fields to the device model, and allow Matrix clients to set these values using existing
device update APIs. It is up to the client to use user agent, client hints, mobile platform's standard library, etc, or
to opt out of recording client information. The new fields should be returned as part of the device model (as above). As
it relies on the client to detect changes in values and update them manually, it is easy for data to get stale.

## Security considerations
The user agent is currently only exposed in the admin API and following this MSC would be accessible to normal users.
The `/devices` endpoints only return device information for the current user, so this is not a concern.


## Unstable prefix
While this MSC is not included in the spec `last_seen_user_agent` should use the unstable prefix
`org.matrix.msc3852.last_seen_user_agent`
