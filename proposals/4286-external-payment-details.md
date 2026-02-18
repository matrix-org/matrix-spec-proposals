# MSC4286: App store compliant handling of payment links within events

## Background

Developers of Matrix clients that are distributed via the Apple [App Store](https://www.apple.com/app-store/)
must comply with the [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/).

These guidelines include restrictions on which payment methods are offered and how they are accessed.

If a homeserver operator requires a paid plan for usage of some capabilities then a conflict of
interests can arise between the homeserver operator and the application developer:

The homeserver operator may wish to promote the paid service by sending
[Server Notices](https://spec.matrix.org/v1.14/client-server-api/#server-notices) to the user or
some equivalent mechanism. However, the App Review Guidelines impose restrictions on the Matrix
client such as:

> **3.1.3(f) Free Stand-alone Apps:** Free apps acting as a stand-alone companion to a paid web
> based tool (e.g. VoIP, Cloud Storage, Email Services, Web Hosting) do not need to use in-app
> purchase, provided there is no purchasing inside the app, or calls to action for purchase outside
> of the app.

A Server Notice that contains a link to an account management page that offers sign up would likely
fall within the class of *"calls to action for purchase outside of the app"*.

As things stand today, if the homeserver wishes to allow users to use whichever client they wish
then the homeserver operator cannot put payment links into the events.

This MSC proposes a way in which the homeserver and the client developer can collaborate to provide
a satisfactory user experience whilst also remaining compliant.

## Proposal

Build on the `org.matrix.custom.html` format and add a permitted attribute
`data-mx-external-payment-details` to the `<span>` tag.

This would mean that clients can choose whether to render the `<span>`.

This is similar to how [spoilers](https://spec.matrix.org/v1.14/client-server-api/#spoiler-messages) work today.

An example of full event might look as follows:

```json
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "Please use a web browser to manage your account",
    "formatted_body": "Please use a web browser to manage your account<span data-mx-external-payment-details> or click <a href=\"https://account.example.com/plan\">here</a></span>"
}
```

On a client that is aware of the new attribute and chooses to not render, it would appear as:

> Please use a web browser to manage your account

However, on a client that is either not-aware or chooses to render, then it would appear as:

> Please use a web browser to manage your account or click [here](https://account.example.com/plan)

## Potential issues

### Opt-in for clients means potentially not compliant by default

When formulating this proposal, it was considered what would be the best approach to balance: work
effort, client compliance, and user experience.

The following table outlines the options that were considered:

Approach | Description | For | Against
-|-|-|-
Restricted clients opt-in (as proposed) | Additional metadata is added to events so that"restricted" clients can hide the restricted content | - Only restricted clients (e.g. iOS) need to be updated<br>- No change needed for other clients | - Restricted clients may not be compliant by default, as they need to be aware of and implement this new capability
Compliant by default | Remove payment links from events. Then provide metadata to say that there is version of the content with links | - All clients are compliant by default as no payment links are present| - All non-restricted clients would ideally be updated to be aware of the presence of the extended content and  deliver the best UX

The first approach was chosen as it is the least disruptive to existing clients and that there is a
small number of known iOS clients to consider.

### Per territory restrictions

Some App Store restrictions apply per territory. In such cases a client may base the decision
whether to render on both the presence of the `data-mx-external-payment-details` attribute and the
territory that the device is configured against.

## Alternatives

### Additional field along side the `formatted_body`

Instead of modifying the `formatted_body` you could add a field alongside that the client could
choose to render.

e.g.

```json
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "Please use a web browser to manage your account",
    "formatted_body": "Please use a web browser to manage your account",
    "formatted_body_with_external_payment_details": "You can manage your account <a href=\"https://account.example.com/plan\">here</a>"
}
```

Or the inverse:

```json
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "Please use a web browser to manage your account",
    "formatted_body": "You can manage your account <a href=\"https://account.example.com/plan\">here</a>",
    "formatted_body_without_external_payment_details": "Please use a web browser to manage your account"
}
```

A benefit of this approach is that the entire rendering can be replaced and not just that which is
covered by the `span`.

### Extensible events

One could define a mix-in called `m.payment_details_hidden` with content which should be displayed
by clients which know they should hide payment details. Something like this:

```json
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "Please use a web browser to manage your account",
    "formatted_body": "You can manage your account <a href=\"https://account.example.com/plan\">here</a>",
    "m.payment_details_hidden": {
        "m.text": "Please use a web browser to manage your account",
        "m.html": "Please use a web browser to manage your account",
    }
}
```

However, this is clunky and has more duplication, and the spoiler-text inspired approach seems good enough.

## Security considerations

No additional requirements. The client should continue apply the existing security constraints to `formatted_body`.

## Unstable prefix

The following should be used:

- `data-msc4286-external-payment-details` instead of `data-mx-external-payment-details`

## Dependencies

None.
