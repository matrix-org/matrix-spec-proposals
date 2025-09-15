# MSC4352: Customizable HTTPS permalink base URLs via server discovery

## Problem

Matrix currently supports two major ways to reference resources: the `matrix:` URI scheme and HTTPS-based permalinks
commonly using `matrix.to`. The specification explicitly documents the `matrix.to` form and even states that such URIs
"must always start with `https://matrix.to/#/`" for the matrix.to navigation format. This tight coupling to a single
domain prevents organizations and deployments from using their own branded resolver domains for invites and permalinks,
despite valid branding, trust and policy needs. It also fragments behavior across clients which already implement ad-hoc
overrides. \[Spec references: Appendices/URIs and matrix.to navigation; `matrix:` scheme\]

Concretely:

- Organizations want to share "Matrix links" on their own domain for branding and trust.
- Some clients (e.g. Element Web via `permalinkPrefix`) and homeservers (e.g. Synapse email via `client_base_url`)
  already support custom bases, but in incompatible, non-standardized ways.
- The spec text hardcodes `matrix.to`, creating friction for standard implementations and documentation.

## Proposal

This MSC introduces a **generic "Matrix link resolver"** concept for HTTPS permalinks and standardizes **discovery** of
a resolver base URL via `/.well-known/matrix/client`. The goal is to keep the **path/arguments format identical** to the
matrix.to navigation format, so that any compliant resolver is a **drop-in replacement**.

### 1. Terminology

- **Matrix link resolver**: An HTTPS service that accepts permalinks in the canonical matrix.to format and routes users
  to an appropriate client or intent. Example format:
  https://<resolver-domain>/#/<identifier>/<optional event>?via=example.org&via=alt.example.org

The path and query semantics are exactly those defined for matrix.to navigation in the Matrix spec (identifier encoding,
`via` parameters, etc.).

- **Permalink base URL**: The base `https://<resolver-domain>` used by a client/homeserver when generating shareable
  HTTPS permalinks.

### 2. Discovery (unstable → stable)

Clients SHOULD determine the permalink base URL using the following precedence:

1.  **Per-account or per-client explicit setting** (implementation-defined)
2.  **Well-known discovery** for the user's homeserver:

- During MSC incubation (unstable): clients MAY read `/.well-known/matrix/client` and use:
  ``` json
  {
    "org.matrix.msc4352.permalink_base_url": "https://links.example.com"
  }
  ```
- After acceptance: the key becomes **stable**:
  ``` json
  {
    "m.permalink_base_url": "https://links.example.com"
  }
  ```

3.  **Default fallback**: `https://matrix.to`

Clients MUST validate that the discovered value is a valid HTTPS origin and MUST NOT auto-upgrade non-HTTPS URLs.

### 3. Generation algorithm (normative)

**Scope:** This algorithm applies **only** to generating HTTPS permalinks for **outside‑Matrix** contexts (e.g. email,
social networks, the web). Clients **MUST NOT** use resolver‑based HTTPS links for in‑app mentions/links/navigation.

1.  Determine `permalink_base_url` by the precedence in Section 2 (user override → well‑known → client default).
2.  Construct the path using the matrix.to navigation grammar defined by the spec (identifier encoding, optional event
    segment, routing parameters like `via`, etc.).
3.  Produce `https://<permalink_base_url>/#/<encoded identifier>[/<encoded event>][?<args>]`.

Clients **SHOULD** continue to prefer the `matrix:` URI scheme for deep‑linking whenever appropriate.

#### In‑app usage (normative)

Clients **MUST NOT** use resolver‑based HTTPS permalinks for in‑app links (mentions, room/event links, or any links
displayed to Matrix users). Clients **MUST** prefer the `matrix:` URI scheme (or native navigation) for all in‑app UX.

#### Sending links in Matrix (normative)

When a user types/pastes a resolver‑style HTTPS permalink in a message composer, the client **SHOULD** preserve the
visible text but **MUST** emit, in `formatted_body`, an anchor whose `href` is the equivalent `matrix:` URI, to ensure
cross‑client interoperability. The plain‑text `body` may keep the original text.

#### Receiving (parsing)

Clients **MUST** handle `matrix:` URIs. Clients **MAY** additionally recognise HTTPS permalinks that follow the
matrix.to navigation grammar regardless of hostname, but this is **not required** by this MSC.

#### Non‑goals

This MSC does **not** standardise applying resolver prefixes to in‑app mentions or in‑app permalinks. Clients **MUST
NOT** rewrite mentions or in‑app links to use resolver domains.

### 4. Resolution behavior

This MSC does **not** require clients to perform network requests to the resolver domain. Like `matrix.to`, clients
SHOULD treat HTTPS permalinks primarily as **hints** for in-app navigation: parse the identifier and act locally if
possible (join, open DM, navigate to event). The resolver service is optional infrastructure for environments without a
Matrix-aware client.

### 5. Server/Homeserver hints (optional)

Homeservers MAY surface the same base via account data or server configuration for convenience, but the normative
discovery mechanism for clients is `/.well-known/matrix/client` as above.

### 6. Backwards compatibility

- Existing permalinks using `https://matrix.to` remain valid.
- Clients without support for this MSC will keep generating `matrix.to` links.
- Element Web’s `permalinkPrefix` and Synapse email’s `client_base_url` can be aligned to this MSC to reduce
  fragmentation.

### 7. Security considerations

- **Phishing/brand impersonation**: Custom resolvers could be abused to masquerade as trusted brands. Requiring
  discovery via the user’s **homeserver well-known** prevents arbitrary third-party pages from being promoted by merely
  embedding a link. Clients MUST NOT trust a resolver domain solely because it appears in a received link; they should
  use it **only when generating links** for that user or after explicit user configuration.
- **Mixed content / TLS**: Only HTTPS origins are permitted. Clients MUST reject `http:` bases.
- **Open redirects**: Resolver implementations SHOULD avoid open redirects and SHOULD validate path/query inputs as per
  the matrix.to grammar.

### 8. Privacy considerations

- Using a custom resolver may leak that a user belongs to a particular deployment/organization when links are shared
  publicly. This is already true for `matrix.to`. Organizations MUST communicate this to users if privacy is a concern.

### 9. Alternatives considered

- **Use `matrix:` URIs exclusively**: Not sufficient for email/web contexts and platforms which strip custom URI
  schemes.
- **Client-only settings (status quo)**: Inconsistent across clients; no standard discovery; harder for orgs to deploy
  at scale.
- **Standardize Element’s `permalinkPrefix`**: Too implementation-specific; this MSC proposes a protocol-agnostic field
  in well-known instead.
- **Change the path grammar**: Would break compatibility. This MSC preserves the matrix.to grammar for drop-in
  replacement.

### 10. Unstable prefixes / feature flag

Until acceptance:

- Well-known key: `org.matrix.msc4352.permalink_base_url`

After acceptance:

- Well-known key: `m.permalink_base_url`

No new endpoints or event types are introduced; therefore no unstable REST namespace is required.

### 11. Dependencies

None.

### 12. Potential issues

- Some mobile clients might deep-link only selected resolver domains. This MSC recommends clients parse and act on
  permalinks locally to avoid resolver coupling.
- Organizations need guidance for hosting resolvers; this is intentionally out-of-scope (deployment doc), but we note
  parity with matrix.to behavior.

### 13. Implementation notes (non-normative)

- Element Web/Desktop can map existing `permalinkPrefix` to this MSC with minimal changes.
- Synapse can keep using `client_base_url` for email templates; admins should align it with `m.permalink_base_url` to
  avoid mismatches.

## References

- Matrix Spec process & proposal guidelines (how MSC numbers and filenames work).
- Spec: `matrix:` URI scheme (introduced in v1.1).
- Spec: matrix.to navigation grammar (Appendices/URIs).
- Existing ecosystem knobs: Element Web `permalinkPrefix`, Synapse email `client_base_url`.
