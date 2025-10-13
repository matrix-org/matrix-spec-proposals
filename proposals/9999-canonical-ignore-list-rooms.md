# MSC999: Canonical ignore list rooms

Keeping up with spam in ignore lists can be hard, and currently requires either a lot of manual labor
or thoughtfully designed bots to bridge policy lists with user's ignore lists. This has a chance to
majorly impact server performance at scale. I wish there was a better way to achieve this.


## Proposal

I would like to propose adding a `ignored_user_list_rooms` property to `m.ignored_user_list`, to serve
as an "include"-list for Moderation Policies as they exist today. 

Some of you may already be familiar with a feature that works a lot like this: Element Web's
"New Ways To Ignore Users" Labs feature!

I would like to have the server help out with this, and prevent clients from receiving the events
in the first place, as well as eliminating the need to use bot to achieve this behavior.

Example of an updated `m.ignored_user_list`:
```diff
{
  "content": {
    "ignored_users": {
      "@someone:example.org": {}
    },
+    "ignored_user_list_rooms": {
+      "!fTjMjIzNKEsFlUIiru:neko.dev": {
+        "use_globs": true,
+        "use_server_bans": true,
+        "use_banned_rooms": true,
+        "apply_retroactively": true
+      }
+    }
  },
  "type": "m.ignored_user_list"
}
```

You may notice these additional properties in the schema, that may not make it into the final version of this MSC.
All of these are optional:
- `use_globs`: Whether to enable parsing globs, as commonly used in policy lists. These can be a performance hazard.
- `use_server_bans`: Whether to also ignore users matched by a `m.policy.rule.server` policy.
- `use_banned_rooms`: Whether to automatically leave rooms banned by a given policy list (including invites).
- `apply_retroactively`: Whether clients should explicitly remove locally cached messages upon a new policy being written.

To follow a banlist, the user MUST be a joined member of the policy list. This allows servers to always have at least
one local member in the room.

I would RECOMMEND that clients consider hiding events from users ignored through a policy list retroactively,
as policy list maintainers or server administrators may wish use this mechanic as a way to hide or remove illegal
content content, or content that otherwise violates the homeserver's Terms Of Service/Acceptable Use Policy.

## Potential issues

Clients that do clientside filtering for cached messages may not scale very well with this, and will need to be updated
to handle enforcing policy lists.

## Alternatives

- Keep using a bot for this. Clients that filter their local timeline with the ignored users list will have performance
ramifications if banlists are being imported with >10k policies (see eg. #community-moderation-effort-bl:neko.dev).

- Implement the bot solution as part of clients. This will cause synchronisation issues as they all race to update the
ignored user list.

- Do the bridging server side by expanding `ignored_users`. This has the same performance ramifications as the previous
2 alternatives, as clients aren't being expected to explicitly handle the case of having 10k+ ignore list entries.

## Security considerations

I did not find anything relevant in the OWASP TOP 10.

Thinking logically, there is two ways this could be exploited, that I personally would consider intentional:
- Servers may be adding a set of required ignore lists on behalf of users. This may be considered beneficial in order to
keep local users safe in accordance to local server policies.

- Malicious policy list writers may cause mayhem by banning rooms or other users. It is up to the user to pick policy
lists to follow, that they themselves place trust in.

## Unstable prefix

`s/ignored_user_list_rooms/gay.rory.msc9999.ignored_user_list_rooms/`

## Dependencies

No known dependencies.