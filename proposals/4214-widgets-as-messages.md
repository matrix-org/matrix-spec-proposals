# MSC4214: Embedding Widgets in Messages

*This proposal introduces the ability to embed widgets directly within messages in the Matrix
timeline. By allowing users to post interactive elements like games, polls, or other tools directly
in messages, this MSC enhances user engagement and interactivity beyond the current room-scoped
widgets.*

## Proposal

Currently, Matrix supports room-level widgets that provide collaborative and interactive
capabilities but are not tied to individual messages. This MSC proposes a method to embed widgets
directly within messages, enabling rich, contextual interactions without attaching them as
room-level widgets.

This proposal uses the extensible events format (per MSC1767) to ensure future compatibility and
flexibility, aligning with modern Matrix practices. The aim is to keep the implementation
lightweight while enabling various use cases.

## Event Schema

### New Event Type

- **Event Type**: `m.widget`
- **Format**: Extensible event

### Event Content

The message event containing the embedded widget will include the following fields:

- **`m.text`**: A caption for the widget, providing context or instructions (similar to image
  captions). Clients that do not support widgets should display this field as a fallback.
- **`m.widget`**: An object containing details about the widget:
  - `url`: The URL of the widget (e.g., a hosted game or tool).
  - `name`: A human-readable name for the widget.
  - `type` *(optional)*: A namespaced identifier to distinguish different types of widgets.
  - `data` *(optional)*: An object containing any initial configuration or data required by the widget.
  - `id` *(optional)*: A unique identifier for the widget instance.

### Example Event

```json
{
  "type": "m.widget",
  "content": {
    "m.text": [
      {"body": "Check out this interactive Tic-Tac-Toe game!"}
    ],
    "m.widget": {
      "url": "<https://example.com/widgets/tictactoe>",
      "name": "Tic-Tac-Toe",
      "type": "net.example.tictactoe",
      "data": {
        "game_id": "abc123"
      },
      "id": "widget-xyz789"
    }
  }
}
```

## Client-Server API Changes

### **Posting a Widget in a Message**

To post a widget, clients send a `m.widget` message event containing the structure above. Clients
that do not support widgets will render the `m.text` caption as a fallback.

### **Rendering and Interaction**

- **Widget Rendering**: Clients supporting `m.widget` should render the widget inline within the
  timeline. Widgets must be sandboxed using an `<iframe>` with appropriate restrictions to ensure
  security.
- **User Controls**:
  - **Load Confirmation**: Clients may prompt users before loading the widget to prevent unwanted
    content execution.
  - **Security Indicators**: Clients should display warnings or indicators for untrusted widgets
    from external sources.

## Capabilities

A new capability `m.widget_messages` will be advertised in the capabilities endpoint
(`GET /_matrix/client/v3/capabilities`) to signal client support for embedding widgets.

**Example**:

```json
{
  "capabilities": {
    "m.widget_messages": {
      "enabled": true
    }
  }
}
```

- **Behaviour**:
  - When `enabled` is `false`, clients should display the `m.text` fallback only.
  - When `enabled` is `true`, clients may render widgets inline and interact with them according to
    their capabilities.

## Privacy Considerations

- **Data Exposure**: Loading widgets may expose user data (e.g., IP address) to the external server
  hosting the widget. Users should be informed and prompted for consent before loading a widget
  from an untrusted source.

- **Opt-Out Settings**: Clients must provide settings to disable automatic loading of widgets in
  messages, requiring manual approval for each instance.

## Security Considerations

- **Sandboxing**: Widgets must be rendered within a secure, sandboxed environment
  (e.g. an `<iframe>` with the `sandbox` attribute to restrict permissions).

- **Content Security Policy (CSP)**: Clients should enforce strict CSP rules to limit widget access
  to only what is necessary. For example, a CSP could be set to only allow scripts and resources
  from trusted domains.

  **Example CSP**:

  ```http
  Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.widgetsource.com; object-src 'none';
  ```

- **Permissions**: Widgets that request additional permissions should require explicit user
  approval, with clear communication about the implications.

- **Power-Level Event for Authorisation**: Introduce a new power-level event `m.widget_send` to
  control which users are authorised to send `m.widget` events. This allows room administrators to
  manage who can send widgets, reducing the risk of spam or malicious widgets.

**Example Power-Level Configuration**:

```json
{
   "events": {
       "m.widget_send": 20
   }
}
```

## Federation Considerations

Federation will support the transmission of `m.widget` events without additional requirements.
The existing homeserver processing and filtering logic will handle these events as regular
extensible events.

## Implementation Details

- **Caching and Performance**: Clients should cache widgets judiciously and free resources when the
  widget is out of view to maintain performance.

- **Consistency Across Clients**: Ensuring a consistent experience across clients requires adopting
  standard rendering and security practices. Widgets should degrade gracefully for clients that
  only support `m.text` fields.

## Potential Issues

- **Malicious Content**: Widgets could deliver harmful content or scripts. Proper validation,
  sandboxing, and security checks are essential to mitigate risks.

- **Performance Impact**: Rendering multiple widgets may degrade client performance. Developers
  must optimise memory and resource usage when displaying widgets.

- **User Privacy**: Widgets may inadvertently collect user data. Strict privacy policies and user
  prompts are necessary to safeguard user information.

## Unstable Prefixes

While the feature is under development and testing, the event type and capability will use an
unstable prefix:

- **Event Type**: `uk.tcpip.msc.widget`
- **Capability**: `uk.tcpip.msc.widget_messages`

**Example Usage**:

```json
{
  "type": "uk.tcpip.msc_widget",
  "content": {
    "m.text": [
      {"body": "Here's a fun game for the group!"}
    ],
    "m.widget": {
      "url": "https://example.com/widgets/poll",
      "name": "Group Game",
      "type": "net.example.game",
      "id": "widget-game456"
    }
  }
}
```

## Alternatives Considered

### Room-Level Widgets

Using `m.room.widget` events for embedding widgets is not suitable for all scenarios, as these are
room-scoped and don't provide the contextual interaction that message-specific widgets offer.

### Extending Existing Message Types

Embedding widgets within existing message types like `m.rich_text` could complicate rendering and
doesn't clearly define behaviour for clients, making it harder to ensure consistent support.

## Future Extensions

This MSC provides a basic framework for embedding widgets. Future MSCs may build upon this by:

- Introducing more standardised widget types and capabilities.
- Enhancing interactions (e.g. collaborative widgets) with shared state.
- Improving privacy and security controls based on user and community feedback.
