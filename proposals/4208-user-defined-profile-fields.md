# MSC4208: Adding User-Defined Custom Fields to User Global Profiles

*This proposal depends on [MSC4133: Extending User Profile API](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).
It introduces user-defined custom fields in the `u.*` namespace for user profiles.*

## Proposal

This proposal aims to enable users to add arbitrary custom key:value pairs to their global user
profiles within the Matrix ecosystem. By leveraging the extended profile API introduced in
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133), users can enrich their
profiles with additional public information such as preferred languages, organisational roles, or
other relevant details.

### Key/Namespace Requirements

As per [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133), the profile API is
extended to allow additional fields beyond `avatar_url` and `displayname`. This MSC defines the use
of the `u.*` namespace for user-defined custom fields:

- **Namespace `u.*`**: Reserved for user-defined custom fields. The portion of the key name after
  the `u.` defines the display name of this field (e.g., `u.bio`). The values in this namespace
  must always be UTF-8 strings with content not exceeding 512 bytes.

### Client Considerations

- Clients SHOULD provide a UI for users to view and edit their own custom fields in the `u.*`
  namespace.

- When displaying other users' profiles, clients SHOULD retrieve and display custom fields in the
  `u.*` namespace.

- Clients SHOULD be cautious about the amount of data displayed and provide options to limit or
  filter the display of custom fields.

- Clients SHOULD implement appropriate content warnings and user education about the public nature
  of profile fields.

### Server Considerations

- Homeservers MAY impose limits on the number of custom fields, whether for storage reasons or to
  ensure the total profile size remains under 64KiB as defined in [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

- Homeservers MAY validate that keys in the `u.*` namespace conform to the required format and
  enforce size limits on values.

- Homeservers SHOULD use the existing `m.profile_fields` capability to control access to the `u.*`
  namespace. For example:

  ```json
  {
    "m.profile_fields": {
      "enabled": true,
      "disallowed": ["u.*"]
    }
  }
  ```

### Trust & Safety Considerations

The ability for users to set arbitrary freetext fields in their profiles introduces several
significant trust and safety concerns that implementations must consider:

#### Content Moderation

- **Hate Speech and Harassment**: Users could use profile fields to spread hate speech or harass
  others. Homeservers MUST implement appropriate content moderation tools.

- **Impersonation**: Custom fields could be used to impersonate others or create misleading
  profiles. Homeservers SHOULD have mechanisms to handle impersonation reports.

- **Spam and Malicious Links**: Profile fields could be used to spread spam or malicious links.
  Homeservers SHOULD implement link scanning and spam detection.

#### Privacy and Data Protection

- **Personal Information**: Users might inadvertently overshare personal information. Clients
  SHOULD warn users about the public nature of profile fields.

- **Data Mining**: Public profile fields could be scraped for data mining. Homeservers SHOULD
  implement rate limiting and monitoring for bulk profile access.

- **Right to be Forgotten**: Homeservers MUST ensure compliance with data protection regulations,
  including the ability to completely remove profile data when requested.

#### Implementation Requirements

To address these concerns:

1. **Content Filtering**:
   - Homeservers MUST implement content filtering capabilities for custom fields
   - Support for blocking specific patterns or content types
   - Ability to quickly respond to emerging abuse patterns

2. **Reporting Mechanisms**:
   - Integration with [MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202)
     or similar reporting systems
   - Clear processes for handling abuse reports
   - Tools for moderators to review and action reported content

3. **Rate Limiting**:
   - Limits on frequency of profile updates
   - Protection against automated abuse
   - Monitoring for suspicious patterns

4. **User Education**:
   - Clear warnings about public nature of fields
   - Guidelines for appropriate content
   - Privacy implications documentation

## Potential Issues

- **Privacy Concerns**: Users need to be aware that custom profile fields are public and visible to
  anyone who can access their profile.

- **Abuse Potential**: As with any user-generated content, there is potential for misuse. Servers
  and clients need to be prepared to handle offensive or inappropriate content.

- **Interoperability**: Until widespread adoption occurs, not all clients may support displaying
  custom fields, leading to inconsistent user experiences.

## Security Considerations

- **Content Moderation**: Homeservers SHOULD provide mechanisms to report and handle abusive
  content in custom profile fields. [MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202)
  provides an example of one such mechanism.

- **Data Protection**: Homeservers SHOULD ensure compliance with data protection regulations,
  especially regarding user consent and data retention.

## Unstable Prefixes

### Unstable Namespace

Until this proposal is stabilised, custom fields should use an unstable prefix in their keys:

- **Namespace `uk.tcpip.msc4208.u.*`**: For example, `uk.tcpip.msc4208.u.bio`.

## Dependencies

This proposal depends on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133),
which introduces the extended profile API to allow additional fields in user profiles.
