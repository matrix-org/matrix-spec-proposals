# MSC3517: Mention Pushrule

Pings in matrix can be inconsistent for someone coming from an environment where pings are explicit
(e.g. Discord, Telegram, Slack, Whatsapp, etc.)

Currently, personal pings are governed by 2 push rules; match on display name, and match on username.

However, due to a variety of reasons, these push rules can have false-positives, and a suitable
alternative that only gives notifications on explicit pings does not exist.

## Proposal

This proposal aims to change that, adding the following default push rule:

```json
{
    "rule_id": ".m.rule.pings_mxid",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "mxid_ping"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        },
        {
            "set_tweak": "highlight"
        }
    ]
}
```

And the following condition; `mxid_ping`.

Currently, this condition should trigger if the user's MXID is found in `content.body`,
or `content.formatted_body`.

Rationale:
> This is called MXID "ping", as "mention" and "contains" would not be good fits for
> future-proofing, one of the benefits of a separate condition is that, in the future,
> once more comprehensive mention techniques come to fruition (such as putting mentions
> in an array), the rule could still automatically apply with a small tweak.

## Unstable prefix

The unstable should be `.nl.automatia.rule.pings_mxid`
