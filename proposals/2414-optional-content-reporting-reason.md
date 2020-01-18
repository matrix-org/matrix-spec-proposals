# MSC2414: Make `reason` optional for reporting content

Currently, the spec says that the `reason` parameter on the content reporting
endpoint is required, but also says that the string "may be blank." This
seems to be a contradiction.

This MSC proposes that the `required` flag for this parameter be removed, as
well as the "may be blank" clause in the description.

Note that the kicking and banning endpoints already have optional `reason`
parameters. The other endpoints mentioned in #2367 will likely also add
optional `reason` parameters, so it seems that it would be more more consistent
with the rest of the spec to make this optional as well.