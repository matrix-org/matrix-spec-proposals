# MSC3283: Expose enable_set_displayname, enable_set_avatar_url and enable_3pid_changes in capabilities response 

Some home servers like [Synapse](https://github.com/matrix-org/synapse/blob/756fd513dfaebddd28bf783eafa95b4505ce8745/docs/sample_config.yaml#L1207) 
can be configured to `enable_set_displayname: false`, `enable_set_avatar_url: false` or `enable_3pid_changes: false`. 
To enable clients to handle that gracefully in the UI this setting should be exposed.

## Proposal

The `/_matrix/client/r0/capabilities` endpoint should be decorated to provide more information on capabilities.
```jsonc
{
  "capabilities": {
    "m.set_displayname": { "enabled": false },
    "m.set_avatar_url": { "enabled": false },
    "m.3pid_changes": { "enabled": false },
    "m.room_versions": {...},
  }
}
```
As part of this MSC, a capability for each setting will be added that exposes the server setting:
- `m.set_displayname`

Whether users are allowed to change their displayname after it has been initially set. 
Useful when provisioning users based on the contents of a third-party directory.

- `m.set_avatar_url`

Whether users are allowed to change their avatar after it has been initially set. 
Useful when provisioning users based on the contents of a third-party directory.

- `m.3pid_changes`

Whether users can change the 3PIDs associated with their accounts
(email address and msisdn).

## Client recommendations
When presenting profile settings, clients should use capabilities in order to display the correct UI.

Capability should always be present.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3283.` in place of `m.` throughout this proposal.
