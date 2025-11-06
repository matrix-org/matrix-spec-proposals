# MSC4302: Exchanging FHIR resources via Matrix events

[FHIR] (pronounced "fire") is a globally established standard for exchanging healthcare information
electronically. The base building blocks of FHIR are so called resources, such as [`Patient`]. These
resources can be serialised into JSON or XML which allows them to be transmitted via the [`m.file`]
message type with a MIME type of `application/fhir+json` or `application/fhir+xml`. The generic MIME
type doesn't provide clients with any information about what resources are contained in the file,
however, and requires them to download it for further processing. This is suboptimal because clients
may want to render only some resources, such as [Questionnaire], with a rich UI. Furthermore, even
if a client chooses to present all FHIR resources as opaque files, users would benefit from getting
some information about a file's content without having to download it. Finally, FHIR resources may
in certain cases be small enough to be inlined into Matrix events which would significantly simplify
client-side processing.

To address these shortcomings, this proposal introduces an event type for transmitting FHIR
resources and type information over Matrix in either inlined or uploaded form.

## Proposal

A new event type `m.fhir.resource` is introduced with the following properties in `content`:

- `canonical_url` (string, required): The resource's [canonical URL], that is the globally unique
  identifier defining its schema. MAY contain a version suffix separated by `|` as per the FHIR
  specification.
- `m.fhir.resource` (object): The serialised JSON if it fits within the [64 KiB event size limit].
  Required if `m.file` is missing.
- `m.file` (object): An [MSC3551] content block describing an uploaded JSON or XML serialisation of
  the resource if it is too large to be inlined. Required if `m.fhir.resource` is missing.

``` json5
{
  "type": "m.fhir.resource",
  "content": {
    "canonical_url": "http://hl7.org/fhir/patient.html|4.0.1",
    "m.fhir.resource": {
      "resourceType": "Patient",
      "name": [{
        "use": "official",
        "given": ["John", "James"],
        "family": "Doe"
      }],
      "gender": "male",
      "birthDate": "1970-01-01",
      // further properties as per the Patient schema
    },
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "mimetype": "application/fhir+json",
      // further properties as per MSC3551
  }
}
```

## Potential issues

FHIR includes generic resources such as [`Bundle`] which wrap other resources. The `canonical_url`
will not help clients understand the wrapped content without downloading it in these cases.
Dedicated event types may be introduced in future to cater to these situations.

## Alternatives

Dedicated MIME types per resource, version and serialisation format could be introduced. Since FHIR
supports a vast number of resources this doesn't appear practical, however.

[RFC 2045] allows MIME types to include modifying parameters. The canonical URL could, therefore, be
included alongside the media type[^1].

    Content-type: application/fhir+json; canonical_url="http://hl7.org/fhir/patient.html|4.0.1"

This would allow reusing the `m.file` message type but leaks the resource type to the home server in
[`POST /_matrix/media/v3/upload`].

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable, the event type `m.fhir.resource` should be referred to as
`de.gematik.msc4302.fhir.resource`.

## Dependencies

None.

[^1]: This could also be done by reusing the `profile` parameter from [RFC 6906]. Since the term
    "profile" already has a specific meaning within the FHIR standard, this could be confusing,
    however.

  [FHIR]: https://hl7.org/fhir/
  [`Patient`]: http://hl7.org/fhir/R4/patient.html
  [`m.file`]: https://spec.matrix.org/v1.14/client-server-api/#mfile
  [Questionnaire]: https://www.hl7.org/fhir/questionnaire.html
  [canonical URL]: https://build.fhir.org/references.html#canonical
  [64 KiB event size limit]: https://spec.matrix.org/v1.14/client-server-api/#size-limits
  [MSC3551]: https://github.com/matrix-org/matrix-spec-proposals/pull/3551
  [`Bundle`]: http://hl7.org/fhir/StructureDefinition/Bundle
  [RFC 2045]: https://datatracker.ietf.org/doc/html/rfc2045#section-5
  [`POST /_matrix/media/v3/upload`]: https://spec.matrix.org/v1.14/client-server-api/#post_matrixmediav3upload
  [RFC 6906]: https://datatracker.ietf.org/doc/html/rfc6906
