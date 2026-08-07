# MSC4173: Test Pusher

It is often useful for both client developers and end-users to be able to test
their push notification configuration.

Today, client applications can test their push gateway by sending a message
directly to the gateway with a test event id. They can check they receive the
test message by comparing the event id (cf. Element-X Android [1]).

Nevertheless, it is not possible to test if the home server can reach the push
gateway. This happens if the home server have some SSRF protection and the
gateway IP is not whitelisted (cf. Synapse [2]), when the machine hosting the
home server can't resolve the gateway domain (which happens on containers) or
because of other network issues, like networks without hairpinning. This
inability to test the request from the home server to the gateway has led to
many issues and request for debugs. (eg. [3], [4]).

In order to facilitate the configuration troubleshoot, a new API is proposed
to send a test message from the homeserver to the push gateway.

An MSC [5] was already open for this new API, but was abandoned because it was
not actively worked on. It was suggested to open a new MSC.

[1] https://github.com/element-hq/element-x-android/blob/v0.5.0/libraries/push/impl/src/main/kotlin/io/element/android/libraries/push/impl/test/TestPush.kt#L49
[2] https://matrix-org.github.io/synapse/latest/usage/configuration/config_documentation.html#ip_range_whitelist
[3] https://github.com/element-hq/element-x-android/issues/2340#issuecomment-2109408945
[4] https://github.com/element-hq/element-android/issues/7069#issuecomment-2109439991
[5] https://github.com/matrix-org/matrix-spec-proposals/pull/2821

## Proposal

A new endpoint is to be added which will allow testing push notifications. It
requires the `pushkey` and `app_id` parameters, which should match a previously
added pusher. It requires `event_id` which will be send by the home server.

Note: The specifications are not very clear about what should uniqly identify a pusher. It seems to be its app_id + its pushkey + its user (eg Synapse [6]).

[6] https://github.com/element-hq/synapse/blob/v1.111.0/synapse/storage/schema/main/delta/40/pushers.sql#L51

```
POST /_matrix/client/r0/pushers/push HTTP/1.1
Content-Type: application/json

{
  "app_id": "com.example.app.ios",
  "pushkey": "APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvPVGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7hH5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMCg2ZXKqpc8FXKmhX94kIxQ",
  "event_id": "$TEST_EVENT_ID"
}
```

A 200 response is returned with the status of the push message. The status can be:
- `ok` if the push was successfully sent to the gateway and the key wasn't rejected;
- `rejected` if the push was successfully sent to the gateway but the gateway rejected the key;
- `unreachable` if the push gateway can't be reached (can be a network error);
- `rate_limited` if the gateway send a rate-limited response;
- `not_registered` if the `push_key` with the `app_id` are not registered on the server for this user;

```
{
  "status": "rejected"
}
```

The homeserver sends as test event. The device in the `devices` array contains the
attributes of the device as set during registration. The `event_id` contains the
id send to the new API.

```
{
  "notification": {
    "devices": [
      {
        "app_id": "com.example.app.ios",
        "data": {
          "url": "https://push.example.tld/_matrix/push/v1/notify"
        },
        "pushkey": "APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvPVGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7hH5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMCg2ZXKqpc8FXKmhX94kIxQ",
        "pushkey_ts": 12345678,
        "tweaks": {
          "sound": "bing"
        }
      }
    ],
    "event_id": "$TEST_EVENT_ID"
  }
}
```

## Additional thoughts

`unreachable` and `rate_limited` may be merged into `temp_unavailable`.

## Security considerations

The event_id is useful only for debugging purpose. To avoid any issue with
during deserialization, loads or other, this event_id can be restricted to the
following expression: `\$[a-zA-Z0-9-_]{1,128}`.

## Unstable prefix

TODO
