# MSC2422: Allow `color` as attribute for `<font>` in messages

Currently the spec recommends that you to use `data-mx-color` instead of the standard
`color` html attribute for the `<font>` tag. This is probably done to make it
consistent with `<span>`, where you may not want to allow a generic style tag for.

On the other hand the /rainbow command on almost every client just uses the
`color` attribute of the `<font>` tag. While some clients support
`data-mx-color` (i.e. Riot Web), most clients don't. Most clients support
rendering `color` however.

It would probably be for the best to allow or even prefer `color` on the
`<font>` tag.

## Proposal

Add the `color` attribute to the allowed attributes of `<font>` in section
13.2.1.7. No changes to the allowable values from the HTML spec are made here.

## Potential issues

- We now have a redundant attribute in the spec. While it matches what the
    clients currently do, it may be better to fix each client instead.
- Clients may not sanitize the color attribute and will let other color values
    through, increasing compatibility issues again.
- Clients may never support the data-mx-* attributes now.
- Old messages could loose their color
- This proposal doesn't touch span at all, maybe it should?

## Alternatives

- fix the clients  
  -> This currently seems not feasible. Multiple clients started using color first (i.e. RiotX, Gomuks) and if it isn't spelled out explicitly in the spec, this will probably continue.
- remove the `data-mx-color` and `data-mx-bg-color` attributes entirely, leaving us just with `color` for `<font>`  
  -> This would break old messages and can be done independently of this proposal at a later date, if it is deemed useful.
- Add a section to tell the clients to prefer `color` over `mx-data-color`  
  -> I don't really know, why mx-data-* was chosen, but I assume there was a reason, so I don't want to change that.
- Spec an entirely different format for messages (that would probably not make this proposal obsolete)  
  -> This wouldn't fix the issue, where some client may choose to remove the color tag, since it is discouraged in the spec. Migration would probably also take a while, so this proposal is a quick solution, that doesn't prevent other solutions at a later date.
