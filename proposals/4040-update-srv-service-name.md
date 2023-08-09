# MSC4040: Update SRV service name to IANA registration

The Internet Assigned Numbers Authority (IANA) holds a registry of all service names and ports in use
by Internet applications. Unfortunately, the service name `matrix` was registered an eternity ago for
use in an unrelated project, which makes our usage of it improper at best. On August 4, 2023 our
registration of port 8448 was accepted, with an included service name of `matrix-fed`. This MSC
proposes a backwards-compatible change to use this newly registered service name.

The registrations with keyword "matrix" can be found [here](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=matrix).

This fixes https://github.com/matrix-org/matrix-spec/issues/400

See also https://github.com/matrix-org/matrix-spec/issues/1576

## Proposal

The [current specification](https://spec.matrix.org/v1.7/server-server-api/#resolving-server-names) for
resolving server names requires an implementation to look up `_matrix._tcp` SRV records in some steps.
Those steps become *deprecated* and new steps which use `_matrix-fed._tcp` are added immediately before
each existing step.

Deprecation in context of this MSC is to discourage continued use, and to queue the affected steps for eventual
removal from the specification under the [deprecation policy](https://spec.matrix.org/v1.7/#deprecation-policy).

The new steps thus become:

1. (unchanged) If the hostname is an IP literal, then that IP address should be used, together with the
   given port number, or 8448 if no port is given. The target server must present a valid certificate for
   the IP address. The `Host` header in the request should be set to the server name, including the port if
   the server name included one.

2. (unchanged) If the hostname is not an IP literal, and the server name includes an explicit port, resolve
   the hostname to an IP address using CNAME, AAAA or A records. Requests are made to the resolved IP address
   and given port with a `Host` header of the original server name (with port). The target server must present
   a valid certificate for the hostname.

3. (steps added/deprecated) If the hostname is not an IP literal, a regular HTTPS request is made to `https://<hostname>/.well-known/matrix/server`,
   expecting the schema defined later in this section. 30x redirects should be followed, however redirection
   loops should be avoided. Responses (successful or otherwise) to the `/.well-known` endpoint should be
   cached by the requesting server. Servers should respect the cache control headers present on the response,
   or use a sensible default when headers are not present. The recommended sensible default is 24 hours. Servers
   should additionally impose a maximum cache time for responses: 48 hours is recommended. Errors are recommended
   to be cached for up to an hour, and servers are encouraged to exponentially back off for repeated failures.
   The schema of the `/.well-known` request is later in this section. If the response is invalid (bad JSON,
   missing properties, non-200 response, etc), skip to step 4. If the response is valid, the `m.server`
   property is parsed as `<delegated_hostname>[:<delegated_port>]` and processed as follows:

   1. (unchanged) If `<delegated_hostname>` is an IP literal, then that IP address should be used together
      with the `<delegated_port>` or 8448 if no port is provided. The target server must present a valid TLS
      certificate for the IP address. Requests must be made with a `Host` header containing the IP address,
      including the port if one was provided.

   2. (unchanged) If `<delegated_hostname>` is not an IP literal, and `<delegated_port>` is present, an IP
      address is discovered by looking up CNAME, AAAA or A records for `<delegated_hostname>`. The resulting IP
      address is used, alongside the `<delegated_port>`. Requests must be made with a `Host` header of
      `<delegated_hostname>:<delegated_port>`. The target server must present a valid certificate for `<delegated_hostname>`.

   3. **(ADDED)** If `<delegated_hostname>` is not an IP literal and no `<delegated_port>` is present, an
      SRV record is looked up for `_matrix-fed._tcp.<delegated_hostname>`. This may result in another hostname
      (to be resolved using AAAA or A records) and port. Requests should be made to the resolved IP address and
      port with a `Host` header containing the `<delegated_hostname>`. The target server must present a valid
      certificate for `<delegated_hostname>`.

   4. **(DEPRECATED)** If `<delegated_hostname>` is not an IP literal and no `<delegated_port>` is present, an
      SRV record is looked up for `_matrix._tcp.<delegated_hostname>`. This may result in another hostname (to
      be resolved using AAAA or A records) and port. Requests should be made to the resolved IP address and port
      with a `Host` header containing the `<delegated_hostname>`. The target server must present a valid certificate
      for `<delegated_hostname>`.

   5. (unchanged) If no SRV record is found, an IP address is resolved using CNAME, AAAA or A records. Requests
      are then made to the resolve IP address and a port of 8448, using a `Host` header of `<delegated_hostname>`.
      The target server must present a valid certificate for `<delegated_hostname>`.

4. **(ADDED)** If the `/.well-known` request resulted in an error response, a server is found by resolving an
   SRV record for `_matrix-fed._tcp.<hostname>`. This may result in a hostname (to be resolved using AAAA or A
   records) and port. Requests are made to the resolved IP address and port, using 8448 as a default port, with
   a `Host` header of `<hostname>`. The target server must present a valid certificate for `<hostname>`.

5. **(DEPRECATED)** If the `/.well-known` request resulted in an error response, a server is found by resolving
   an SRV record for `_matrix._tcp.<hostname>`. This may result in a hostname (to be resolved using AAAA or A
   records) and port. Requests are made to the resolved IP address and port, using 8448 as a default port, with a
   `Host` header of `<hostname>`. The target server must present a valid certificate for `<hostname>`.

6. (unchanged) If the `/.well-known` request returned an error response, and the SRV record was not found, an IP
   address is resolved using CNAME, AAAA and A records. Requests are made to the resolved IP address using port
   8448 and a `Host` header containing the `<hostname>`. The target server must present a valid certificate for
   `<hostname>`.

## Potential issues

Us using `matrix` as a service name has been an issue all along. This MSC aligns the specification with our
formal IANA registration.

## Alternatives

We could modify our IANA registration further to pick a different name, however the service name needs to be
descriptive and short. The author notes that `matrix-server` was attempted in registration, which was declined
during Expert Review of the application.

`matrix` cannot be taken over via IANA process. It was assigned before dates were put on records in 2000.

Non-options for names include `mxfed`, `matrixf`, and similar.

A potential way forward is to remove SRV resolution entirely, however prior effort via
[MSC3922](https://github.com/matrix-org/matrix-spec-proposals/pull/3922) are expected to be *rejected* instead
(as of writing, August 4th, 2023).

## Security considerations

Increased

## Unstable prefix

None applicable.

## Dependencies

None applicable.
