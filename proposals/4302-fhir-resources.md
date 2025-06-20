# MSC4302: Exchanging FHIR resources via Matrix events

[FHIR] (pronounced 🔥) is a globally established standard for exchanging healthcare information
electronically. The base building block of FHIR are so called resources, such as [`Patient`]. These
resources can be serialised into JSON or XML which allows them to be transmitted via the [`m.file`]
message type. This is insufficient, however, because a generic MIME type of `application/xml` or
`application/json` doesn't let clients recognise the content as FHIR before downloading it. The
`m.file` mechanism also doesn't allow clients to infer any details about the types of resources
contained in the file ahead of downloading it. Furthermore, in many cases FHIR resources are small
enough to be inlined into Matrix events which significantly simplifies client-side processing.

This proposal introduces an event type for transmitting FHIR resources and type information over
Matrix in either inlined or uploaded form.

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
      "resourceType" : "Patient",
      "name" : [{
        "use" : "official",
        "given" : ["John", "James"],
        "family" : "Doe"
      }],
      "gender" : "male",
      "birthDate" : "1970-01-01",
      // further properties as per the Patient schema
    },
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "mimetype": "application/json",
      // further properties as per MSC3551
  }
}
```

## Potential issues

FHIR includes generic resources such as [`Bundle`] which wrap other resources. The `canonical_url`
will not help clients understand the wrapped content without downloading it in these cases.
Dedicated event types may be introduced in future to cater to these situations.

## Alternatives

A dedicated MIME type such as `application/fhir+xml` would allow clients to recognise an uploaded
file as FHIR ahead of the download. It would not provide clients with information about the types of
contained resources, however. Since FHIR supports a vast number of resources it doesn't appear
practical to introduce dedicated mimetypes per resource, version and serialisation format

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable, the event type `m.fhir.resource` should be referred to as
`de.gematik.msc4302.fhir.resource`.

## Dependencies

None.

  [FHIR]: https://hl7.org/fhir/
  [`Patient`]: http://hl7.org/fhir/R4/patient.html
  [`m.file`]: https://spec.matrix.org/v1.14/client-server-api/#mfile
  [canonical URL]: https://build.fhir.org/references.html#canonical
  [64 KiB event size limit]: https://spec.matrix.org/v1.14/client-server-api/#size-limits
  [MSC3551]: https://github.com/matrix-org/matrix-spec-proposals/pull/3551
  [`Bundle`]: http://hl7.org/fhir/StructureDefinition/Bundle
