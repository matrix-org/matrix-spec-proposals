# MSC4175: Profile field for user time zone

Knowing another user's time zone is useful for knowing whether they are likely
to respond or not. Example uses include:

* Showing a user's time zone or time zone offset directly.
* Showing a user's local time (with hints of whether it is day or night there).


## Proposal

Profiles can provide an optional `m.tz` field with values equal to names from the
[IANA Time Zone Database](https://www.iana.org/time-zones).
Clients can set and fetch this via the [normal API endpoints](https://spec.matrix.org/v1.14/client-server-api/#profiles).

* Servers MAY validate that the value is a valid IANA time zone. If deemed invalid
  they MUST return a 400 error with error code `M_INVALID_PARAM`.
* Clients MUST handle invalid or unknown values. One approach may be processing the value as though it was never set.

The rationale for somewhat loose validation is that different clients/servers may have
different understanding of valid time zones, e.g. different versions of the time zone
database.

If the field is not provided, it SHOULD be interpreted as having no time zone information
for that user.

An example request to set the time zone would be:

```
PUT /_matrix/client/v3/profile/@alice:example.org/m.tz

{
  "m.tz": "America/New_York"
}
```

Similarly when retrieving a user's profile:

```
GET /_matrix/client/v3/profile/@alice:example.org

{
  "displayname": "Alice",
  "m.tz": "Europe/Paris"
}
```


## Potential issues

Clients may need to understand IANA time zone names to show useful information to users.
Some languages make this easy, e.g. JavaScript can handle this using
[`Date.toLocaleString()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toLocaleString).
This may cause clients to bundle the IANA time zone database (and thus also keep it
up to date).

Using the IANA time zone name has the downside that it does now allow arbitrary offsets,
which may be required for time zones which are not internationally recognized.

Clients will need to manually update the profile field when the user changes time zone.
This could be automated by clients based on location, or left as a manual change to
users.

Clients may wish to periodically fetch the time zone of other users as it is
liable to change somewhat frequently. Currently, profile data isn't propagated/synchronized
between servers, but that's left to a future MSC to solve. It is recommended that
clients cache the value for 12 - 24 hours.

There should not be backwards compatibility concerns since clients should be ignoring
unknown profile fields.


## Alternatives

The time zone offset could be included directly (in minutes/seconds or in `[+-]HH:MM` form).
This would require clients to manually update the profile field during daylight
savings. Using the IANA time zone name is robust against this.


### Delegate profile fields

There are several standards related to storing of contact information electronically,
notably vCard and its derivatives (see below). It is unclear if Matrix profile
information is similar enough to the contact information found in vCard to warrant using
that format directly, although there is certainly some overlap.

Some of the JSON formats for vCard which include time zone information are detailed below:

[RFC7095: jCard The JSON Format for vCard](https://datatracker.ietf.org/doc/html/rfc7095)
format could be used instead, but this doesn't make much sense unless the entire
profile was replaced.

[RFC9553](https://datatracker.ietf.org/doc/html/rfc9553) offers an alternative
representation for contacts (which is not backwards compatible with vCard). There
exists `timeZone` field under the `addresses` field which uses an time zone name
from the IANA Time Zone Database.

Note there's an alternative [jCard](https://microformats.org/wiki/jCard) format
which is a non-standard derivative of [hCard](https://microformats.org/wiki/hcard).


### Competitive analysis

Slack's [`users.info` API call](https://api.slack.com/methods/users.info) includes
3 separate fields:

* `tz`: the time zone database name (e.g. `"America/New_York"`)
* `tz_label`: a friendly name (e.g. `"Eastern Daylight Time"`)
* `tz_offset`: offset in seconds as an integer (e.g. `-14400`)

XMPP uses either:

* [XEP-054](https://xmpp.org/extensions/xep-0054.html) uses vCard
  ([RFC2426](https://datatracker.ietf.org/doc/html/rfc2426)) converted to XML via
  [draft-dawson-vcard-xml-dtd-01](https://datatracker.ietf.org/doc/html/draft-dawson-vcard-xml-dtd-01)
* [XEP-0292](https://xmpp.org/extensions/xep-0292.html) uses xCard: vCard XML Representation
  ([RFC6351](https://datatracker.ietf.org/doc/html/rfc6351)), see also vCard4
  ([RFC6351](https://datatracker.ietf.org/doc/html/rfc6351))

Rocket.Chat provides a user's [time zone offset](https://developer.rocket.chat/docs/user)
in the `utcOffset` field.

Mattermost [returns an object](https://api.mattermost.com/#tag/users/operation/GetUser)
with the user's manual and/or automatic IANA time zone name.

Discord, Twitter, and IRC don't provide a user's time zone.


## Security considerations

Showing a user's time zone gives some information to their location. There is currently
no way to limit what profile fields other users can see.

Clients may wish to warn users when providing a time zone and give
the option to not include it in their profile.


## Unstable prefix

`us.cloke.msc4175.tz` should be used in place of `m.tz`. 

Clients may immediately use the stable profile field once this MSC is accepted. This is
a client-to-client protocol and no feature negotiation is necessary.


## Dependencies

Requires [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).
