# MSC4216: Set Maximum Allowed Tags

[MSC4216](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4216-limit-creating-same-tag.md)

Enable matrix servers the choice to set a threshold on tags applied by a user, so the user can apply certain tags only to predefined maximum amount.

## Proposal

I'm proposing to add config to matrix servers that specify if the matrix server admin want to limit the tags or not. See the example below on limiting the user to apply the tag `u.pin` to only 3 rooms. This is useful because other chat systems use the same logic on restricting some tag. And with this change we can allow matrix servers admins to dynamically set the max to a tag. Also, if the admin wants to create tag `u.archive` and didn't add it to the config file, that tag will not be restricted to a threshold unlike `u.pin` and `u.favorite`.

```yaml
tags:
    - name: u.pin
      max: 3
    - name: u.favorite
      max: 10
```

## Potential issues

NA

## Alternatives

NA

## Security considerations

NA

## Dependencies

This MSC has no dependencies.
