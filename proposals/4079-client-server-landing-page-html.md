# MSC4079: Server-Defined User Home Pages

## Abstract 

This proposal extends the Matrix protocol to allow servers to define custom
HTML-formatted documents that can be rendered by clients as a user home page. This feature
introduces a non-intrusive yet flexible manner to communicate server-specific information such as
donation requests, scheduled maintenance, updates, new features, and changelogs.

## Background 

Currently, there is no standardized method in Matrix for server admins to communicate information
directly within user clients in a passive way. While rooms can serve this purpose, they lack the
persistence and prime visibility that many server administrators desire. Similarly, server-notices
are aggressive notifications to users that can cause unnecessary noise, and are implemented as
rooms.

## Proposal 

Introduce an optional configuration for matrix servers that allows them to specify an
HTML-formatted document, adhering to the current subset of HTML utilized for message formatting.
Clients can render this document in a dedicated "home" view or as a placeholder page when no active
conversations are selected.

## Use Cases

- Server administrators want to communicate an upcoming maintenance window without emailing all
  users.
- A non-profit Matrix server could display donation information on the home page to encourage
  support from its users.
- Announcement of new features or user guides following an update can be nicely formatted and made
  readily available upon client login.
- Changelogs for server updates can be displayed, helping users to understand recent changes without
  external navigation.
- Links to other supported clients may be supplied in case users are looking for alternative
  interfaces.

## Specification

- A new optional field will be defined within the well-known Matrix configuration for clients:
  user_home_page.
- The user_home_page field can be defined by either in-line HTML content or a fully-qualified domain
  name and path to an HTML document.
- The HTML content will be sanitized by the client and restricted to the subset of HTML currently
  allowed for messages.
- This field can be queried by clients during the login or initial loading process, and refreshed at
  least once every 12 hours if the client has been open the entire time.
- Clients may choose to implement this feature as a "home" button or as default content in the main
  view when no conversation is active.

## Examples

Advertisement of the content for clients to use would be done via `/.well-known/matrix/client`
within the existing `m.homeserver` object.

Example formatting using a file URI:

```
{ 
  "m.homeserver": { 
    "user_home_page_uri": "https://your.website/user_home.html"
  }
}
```

Example formatting using in-line HTML:

``` 
{ 
  "m.homeserver": { 
    "user_home_page_html": "<h1>Welcome to our Matrix Homeserver!</h1><p>Visit our website to make a donation.</p>" 
  } 
}
```

Only one value is needed. If both in-line and URI definitions are defined, clients will prioritize
the in-line HTML.


## Security Considerations 

To mitigate any potential security risks from malicious content:

- Clients MUST sanitize the HTML content according to the existing rules for message content
  sanitation.
- External resources (e.g., images, stylesheets) MUST NOT be fetched by default to avoid privacy
  leaks and must be explicitly allowed by the client.

## Privacy Considerations 

As this feature may potentially be used to track user interaction with the
home page content, it's important to:

- Provide clients the ability to disable external resource fetching.
- Ensure that user privacy preferences are respected when displaying this content.

## Conclusion 

This spec change proposal seeks to empower server administrators with the ability to
directly communicate important information to their users within the Matrix client, enhancing the
user experience by providing relevant and timely information while respecting user privacy and
security.
