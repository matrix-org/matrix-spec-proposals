# MSC4462: Links in Profile

*This Proposal is related to future 
[MSC4464: Verifiable Links in Profile](https://github.com/matrix-org/matrix-spec-proposals/pull/4464)
but not dependent on it*

A lot of other chat platforms (like Discord) or social media platforms (like the fediverse) allow you
to put a list of links in your profile.

## Proposal

Profiles MAY have a `m.connections` field as an array of objects. These fields can be fetched through the
[profile API endpoints](https://spec.matrix.org/unstable/client-server-api/#profiles).

```json
{
   "m.connections": [
     {
        "description": "homepage",
        "uri": "https://example.org"
     },
     {
        "description": "mastodon",
        "uri": "https://mastodon.social/@example"
     },
     {
        "description": "alt-account",
        "uri": "matrix:u/alice:example.org"
     },
    {
        "description": "email account",
        "uri": "mailto:alice@example.org"
    }
   ]
}
```

Content of a object in `m.connections`:

- `description`: human readable description of what a client should show next to the link as label (free-form)
- `uri`: the link to show and render as link (it SHOULD be a valid http/https/matrix/mailto uri)

Clients can then display the links of a user in their respective user popup/profile view UI.

Clients SHOULD limit the length of `description` to 200 characters and the amount of links to at most 20.
If a profile does not conform to the length/amount of links limit a receiving client MAY truncate or ignore
entries exceeding these limits.

If a `uri` is some scheme other than `http`, `https`,`mailto`, or `matrix` a receiving client SHOULD consider these
links invalid and either hide them or mark them as being invalid.

## Potential issues

### claiming link ownership

This proposal doesn't introduce a way to verify link ownership (i.e. is that link really belonging
to @alice:example.org).

[MSC4464: Verifiable Links in Profile](https://github.com/matrix-org/matrix-spec-proposals/pull/4464)
will tackle verification using a dns based, http based, or matrix bidirectional link
in profile method. Verifying other kind of links will be considered out-of-scope tho.

### Trust & Safety

Links may lead to sites deemed inappropriate for a given context (e.g. NSFW sites, illegal content, etc...).
This could be solved by introducing room-local extensible profiles (not part of this proposal), so that
room moderators can do meaningful moderation of links in profiles.

## Alternatives

### Listing them in Bio

If MSC4440 gets accepted an alternative to this proposal would be to just put the links in the bio.

Most important difference being that this proposal introduces a structured way of saving it in the
profile, and so making it better readable for machines.
Clients can, when they recognize a link, for example `https://bsky.app/profile/alice.example.org`
display a appropriate logo next to the link.
Note that this proposal specifically doesn't include a `platform` or `logo` field, as that could
be abused way too easily.

## Security considerations

This proposal introduces user-controlled external links, which clients MUST treat as untrusted input. Clients
SHOULD take precautions against phishing and malicious URLs (e.g. safe rendering, URL previews, or warnings).
A malicious actor could use misleading values in the `description` field for phishing/social engineering.

Clients SHOULD mitigate misleading combinations of description and link, for example by exposing the raw
destination URL where appropriate.

Clients are strongly encouraged to implement defenses against Internationalized Domain Name (IDN) homoglyph
attacks. Instead of silently rendering Unicode domains, clients SHOULD detect mixed-script labels (e.g., a mix
of Latin and Cyrillic characters). In such cases, or when a domain is provided in Punycode format (`xn--...`),
the client SHOULD display the canonical Punycode representation to the user to reveal the actual destination
(for example: `bawü.social` to `xn--baw-joa.social`).

## Unstable prefix

implementations should use `fyi.cisnt.connections` instead of `m.connections` while this is unmerged

**Note**: it was previously under the unstable prefix `fyi.cisnt.links`.

## Dependencies

none
