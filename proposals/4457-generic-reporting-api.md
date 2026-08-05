# MSC4457: Generic reporting API

*This MSC is part of “Reporting v2” - a project led by the Foundation’s T&S team to improve communication
and effectiveness of reports on Matrix.*

Matrix’s [existing module](https://spec.matrix.org/v1.18/client-server-api/#reporting-content) for
reporting content gives capability for users to report other users, rooms, and events. These reports
are supported by 3 separate APIs, each with similar-but-different semantics. Those API endpoints
additionally do not support reporting media items, server names, complaints about the system itself,
or appeals to past moderation action.

There are other issues with the reporting APIs, such as the vast majority of reports ending up in a
database for other tooling to pull from. This proposal does *not* solve those other concerns, but
does outline what future (or existing, in some cases) MSCs might do to help solve these problems.
Collectively, the series of MSCs to fix reporting is called “Reporting v2”.

This MSC generifies the 3 report endpoints to a single endpoint. Support for future MSCs is carved out,
though unspecified, by this refactoring as well.


## Proposal

The following endpoints are deprecated in favour of a new single endpoint:

* [`POST /_matrix/client/v3/rooms/{roomId}/report`](https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3roomsroomidreport)
* [`POST /_matrix/client/v3/rooms/{roomId/report/{eventId}`](https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3roomsroomidreporteventid)
* [`POST /_matrix/client/v3/users/{userId}/report`](https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3usersuseridreport)

The new single endpoint is defined to cover a broader range of reportable entities:

```
POST /_matrix/client/v1/safety/report/{txnId}
Authorization: <normal Client-Server API authentication>
Content-Type: application/json

{
  "type": "complaint", // future scope: "appeal" and possibly other types
  // ... other fields per `type`
}
```

Currently, only the `complaint` type is specified. A future MSC will add an `appeal` type. Other types
may be added by other MSCs.

The `txnId` is a [Transaction Identifier](https://spec.matrix.org/v1.18/client-server-api/#transaction-identifiers).

If the `type` is `complaint`, the following *additional* fields are present on the request body at
the top level:

```jsonc
{
  // The *primary* identifier (user ID, etc) the complaint is regarding. Currently can be one of the following:
  // * A user ID
  // * An event ID
  // * A room ID
  // * A room alias (noting that room ID reports are more reliable because aliases can drift between rooms)
  // * A server name (prefixed with "server:" to distinguish it from a namespaced ID below)
  // * An MXC URI (media URI)
  // * The string "m.system" to denote a complaint regarding the reporting system itself
  // * A common namespaced identifier (https://spec.matrix.org/v1.18/appendices/#common-namespaced-identifier-grammar)
  //
  // The above identifiers are structured so the server can identify each one individually. For example, the server
  // knows it's dealing with a user report if `regarding` starts with `@`.
  //
  // REQUIRED.
  "regarding": "<identifier>",

  // The type of harm being reported in this complaint. Currently, the available harms are defined
  // by MSC4456: https://github.com/matrix-org/matrix-spec-proposals/pull/4456
  // A future MSC is expected to advertise which custom harms (if any) the server supports. Servers
  // reject the request if the harm identifier is unknown.
  //
  // Note: This is the reporter's opinion and is not necessarily fact.
  //
  // REQUIRED.
  "harm": "<harm identifier>",

  // The text the user supplied to support this complaint. The input field presented to the user SHOULD ask them
  // to *briefly* describe the content or harm caused.
  //
  // Cannot exceed 1024 bytes (before trimming whitespace).
  //
  // REQUIRED if `harm` is for a "General/Other" identifier, starts with `m.other`, or is a custom identifier.
  // OPTIONAL otherwise. When provided, cannot be an empty string after trimming whitespace. Custom identifiers
  // have a required `description` because the server/client cannot reasonably determine how self-describing
  // the identifier is.
  "description": "This user is spamming",
}
```

*Author's note*: This proposal doesn't use the word `reason` because it's overly accusatory. Asking
for a description of the harm is more natural.

*Note:* Future MSCs are expected to add more fields, like where/who to send the report to (community
moderators, server admin, remote server, etc).

*Note*: The `regarding` field doesn't cover the case where a reporter wishes to say "all of Alice's
conduct in {this} room is bad". It's expected that when a future MSC introduces attachments that the
client can send a report with a *primary identifier* of `@alice:example.org` then append specific
events or room IDs in a followup. Clients can work around this for now by manually adding the room
ID or event IDs to the `description` alongside the user's own text.

If the report was successful, the server responds with:

```jsonc
{
  // An opaque identifier (https://spec.matrix.org/v1.18/appendices/#opaque-identifiers) to uniquely
  // represent this report in the homeserver's system. Currently has no use.
  //
  // REQUIRED.
  "report_id": "<opaque>"
}
```

*Note:* Future MSCs will use the report ID to allow appending further evidence of harm (screenshots,
events, etc) and likely support communication to the reporter regarding their report. Clients can
discard the report ID for now.

If the report was *not* successful, it will be for one of the following [error codes](https://spec.matrix.org/v1.18/client-server-api/#standard-error-response):

* `429 M_LIMIT_EXCEEDED` - Rate limited (“too many reports too quickly”).
* `400 M_BAD_JSON` - A `REQUIRED` field is missing, especially for the `type`, or a field is too long/short.
* `400 M_INVALID_PARAM` - The `type` or `harm` is unknown to the server.
  * Note: Servers MUST support at least `type: complaint` and possibly more in future MSCs. Servers
    MUST also support any specified harm identifiers, but are not required to support unstable ones.
* `404 M_NOT_FOUND` - The server cannot process the report because the reported identifier does not
  exist (or is unknown). Servers MUST NOT return this error for `m.system` complaints.
* `403 M_FORBIDDEN` - The caller cannot file this report. For example, the server has banned the
  caller from filing reports or the server has determined that the caller does not have visibility
  on the reported object/entity (ie: can’t see the event they’re complaining about, or can’t appeal
  someone else’s ban).


*Note:* Servers MAY use `404 M_NOT_FOUND` and `403 M_FORBIDDEN`. The remaining error codes MUST only
be returned in applicable cases. This optionality is to allow servers to customize their operations
to their individual regulatory requirements and needs. For example, a server might choose to validate
that a user can see an event, but also choose *not* to return an error if they can’t (instead, it’d
get flagged internally on the report). Always returning an error is not considered compliant.

The new report endpoint is available to [guests](https://spec.matrix.org/v1.18/client-server-api/#guest-access).

How the server processes the report remains an implementation detail. A future MSC will clarify where
exactly a report should be routed to. Implementations SHOULD NOT assume that reports will only go to
a single place in the future. This is important for implementations which provide the endpoint as
separate software from the bulk of the homeserver, as otherwise that software might assume that it’s
only going to have to populate a single destination queue.


## Future considerations

Future proposals are expected to expand this API's capabilities in the following ways:

* Being able to route reports to community moderators or other servers.
  * Possibly based on the harm itself ("you cannot refuse to send this to your server admin, but you
    can optionally send it to the mods too").
  * Possibly based on choice too ("do you want to send this to `remote.example.org` too? Should we
    tell them you send the report?").
* Adding attachments (screenshots, events, additional info) and amendments.
* Closing/cancelling reports (and generally the open/closed status of a report).
* Communication frameworks, like who to send updates to. Possibly including a "reply to" address to
  direct safety teams at a more responsive user ID, for example.
* Appeals with an actions database/ID. For example: "appeal {$this} ban".
* Possibly adding evidence to someone else's report, similar to a character witness statement.
  * This may be better handled by a new `information` report type.
* Endpoints to support a UX that can prevent a report from being submitted if it would be rejected.
  For example, ensuring required fields and information is present.
* Anything not listed above :)


## Potential issues

**TODO**: This section needs completing before proposing FCP.

Implementation and unstable usage of this MSC is expected to populate this section. Currently, expected
risks include:

* Not having a generic enough API to support appeals.
* Clients implementing something which makes it harder to add routing later.
* Returning a report ID only to discard it is a bit strange.
* Internal handling of reports may be difficult.
* Limiting to authenticated users (including guests) may prove to be an issue.


## Alternatives

No significant alternatives.


## Security considerations

* To avoid pages upon pages of text, `description` is limited to 1024 bytes. Bytes rather than characters
  was chosen to avoid the "is an emoji 1 character or 2" question. The specific number of 1024 was chosen
  arbitrarily: we don't want to limit users such that they can only provide minimal information, but we
  also don't want to support the Bee Movie script. 1024 was specifically chosen over 512 to permit system
  complaints to have more detail.

* Users can spam the reporting system by flooding it with reports. This is mitigated by rate limiting.

* Existence of a user or a user's ability to see an event can be hidden by returning 200 OK.


## Unstable prefix

While this proposal is not considered stable, implementations should use `/_matrix/client/unstable/org.matrix.msc4457/safety/report/{txnId}`
in place of `/_matrix/client/v1/safety/report/{txnId}`.

Support for the unstable endpoint is advertised as a [`/versions`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions)
unstable feature flag: `org.matrix.msc4457_report_api`.

Implementations which support the unstable endpoint SHOULD continue to do so for at least 6 months
after this proposal is in a tagged release of the specification. This is to ensure that users on outdated
clients continue seeing modern reporting flows.

There is no `/versions` flag for the time where the endpoint is stable but unreleased. Implementations
can continue using the unstable endpoint and switch to the stable one when they see a server supports
that spec version.


## Dependencies

* [MSC4456: Harms taxonomy](https://github.com/matrix-org/matrix-spec-proposals/pull/4456) - Used to
  populate the `harm` field on a complaint report.
