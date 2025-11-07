# MSC4302: Exchanging FHIR resources via Matrix events

## A brief abstract of FHIR, resources and profiles

[FHIR] (pronounced "fire") is a globally established standard for the digital exchange of
healthcare-related information. The base building block of FHIR are so-called *resources*. Resources
have a type that defines their base schema. This schema can be further customised through one or
more *profiles*.

As an example, [`Questionnaire`] is the resource type for medical forms that can be used for various
purposes. This type defines several fields such as an *optional* `title` property containing a human
friendly name for the form. [`ISiKFormularDefinition`], in turn, is a profile on `Questionnaire`
created by Germany's national health agency, gematik, for use within hospitals. It customises the
schema of `Questionnaire` in several ways, such as making `title` required rather than optional.

Both resource types and profiles can be uniquely identified by their [canonical URL].

## The problems of using FHIR resources in Matrix

FHIR resources can be serialised into JSON or XML which can be transmitted via the [`m.file`]
message type with a MIME type of `application/fhir+json` or `application/fhir+xml`. However, the
generic MIME type doesn't let clients understand what resource is contained in the file without
downloading it. This is suboptimal because clients may want to apply special display logic for
certain resource types and profiles. Using the example of `Questionnaire`s, clients may want to
render the resource as an interactive form for the user to fill out and send back a
[`QuestionnaireResponse`] resource.

Similarly, clients that connect external systems to Matrix may want to automatically process certain
resources. For instance, an anamnesis bot may want to export received `QuestionnaireResponse`s into
a surgery's patient management system. Again, the generic MIME type forces such a client to download
the file to determine if it is indeed a `QuestionnaireResponse`.

These problems would be obliterated if FHIR resources were inlined into Matrix events. However, this
isn't always possible due to the [64 KiB event size limit]. Additionally, no suitable event type or
content block exists, as of writing.

## Proposal

To enable the efficient exchange of FHIR resources in either inline or file form, a new event type
`m.fhir.resource` is introduced. This type mandates the following properties in `content`:

- `canonical_url` (string, required): The resource's [canonical URL], that is the globally unique
  identifier defining its base schema. MAY contain a version suffix separated by `|` as per the FHIR
  specification.
- `profiles`: (array of strings): The canonical URLs of the profiles the resource conforms to (if
  any). The order of elements in the array is arbitrary, similar to FHIR's own [`Meta.profile`]
  property.
- `m.fhir.resource` (object, required if `m.file` is missing): The serialised JSON if it fits within
  the [64 KiB event size limit].
- `m.file` (object, required if `m.fhir.resource` is missing): An [MSC3551] content block describing
  an uploaded JSON or XML serialisation of the resource if it is too large to be inlined.

``` json5
{
  "type": "m.fhir.resource",
  "content": {
    // Metadata to help identify the resource
    "canonical_url": "http://hl7.org/fhir/StructureDefinition/Questionnaire|4.0.1",
    "profiles": [
      "https://gematik.de/fhir/isik/StructureDefinition/ISiKFormularDefinition|5.0.0"
    ],
    // Either: The resource in inline form
    "m.fhir.resource": {
      "resourceType": "Questionnaire",
      "title": "Dr. Dre's anamnesis questionnaire for new patients",
      // further properties as per the questionnaire's schema
    },
    // Or: A file representing the resource
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

Malicious clients could attempt to trick other clients into automatically downloading files by
faking the metadata in `m.fhir.resource` events. As a minimal defense, clients SHOULD sanity-check
the size of the downloaded file by issuing a HEAD request and refuse to download large files without
explicit user consent.

## Unstable prefix

While this MSC is not considered stable, the event type `m.fhir.resource` should be referred to as
`de.gematik.msc4302.fhir.resource`.

## Dependencies

None.

[^1]: This could also be done by reusing the `profile` parameter from [RFC 6906]. Since the term
    "profile" already has a specific meaning within the FHIR standard, this could be confusing,
    however.

  [FHIR]: https://hl7.org/fhir/
  [`Questionnaire`]: http://hl7.org/fhir/StructureDefinition/Questionnaire
  [`ISiKFormularDefinition`]: https://gematik.de/fhir/isik/StructureDefinition/ISiKFormularDefinition
  [canonical URL]: https://build.fhir.org/references.html#canonical
  [`m.file`]: https://spec.matrix.org/v1.14/client-server-api/#mfile
  [`QuestionnaireResponse`]: http://hl7.org/fhir/StructureDefinition/QuestionnaireResponse
  [64 KiB event size limit]: https://spec.matrix.org/v1.16/client-server-api/#size-limits
  [`Meta.profile`]: http://hl7.org/fhir/resource-definitions.html#Meta.profile
  [MSC3551]: https://github.com/matrix-org/matrix-spec-proposals/pull/3551
  [`Bundle`]: http://hl7.org/fhir/StructureDefinition/Bundle
  [RFC 2045]: https://datatracker.ietf.org/doc/html/rfc2045#section-5
  [`POST /_matrix/media/v3/upload`]: https://spec.matrix.org/v1.14/client-server-api/#post_matrixmediav3upload
  [RFC 6906]: https://datatracker.ietf.org/doc/html/rfc6906
