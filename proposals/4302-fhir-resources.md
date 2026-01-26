# MSC4302: Exchanging FHIR resources via Matrix events

## A brief abstract of FHIR, resources and profiles

[FHIR] (pronounced "fire") is a globally established standard for the digital exchange of
healthcare-related information. The base building block of FHIR are so-called *resources*. Resources
have a type that defines their base schema. This schema can be further customised through one or
more *profiles*.

As an example, [`Questionnaire`] is the resource type for generic medical forms. This type defines
several fields such as an *optional* `title` property containing a human readable name for the form.
[`ISiKFormularDefinition`], in turn, is a profile on `Questionnaire` created by Germany's national
health agency, gematik, for use within hospitals. It customises the schema of `Questionnaire` in
several ways, such as making `title` required rather than optional.

Profiles can extend either resource types or other profiles, meaning it is possible to build chains
of profiles. Both resource types and profiles are described via [`StructureDefinition`]s which are
uniquely identified by their [canonical URL].

``` json5
{
  // This is the profile ISiKFormularDefinition v5.0.0, created by gematik GmbH
  "resourceType": "StructureDefinition",
  "id": "ISiKFormularDefinition",
  "url": "https://gematik.de/fhir/isik/StructureDefinition/ISiKFormularDefinition",
  "version": "5.0.0",
  "publisher": "gematik GmbH",
  // It extends the base type Questionnaire from FHIR v4.0.1
  "type": "Questionnaire",
  "fhirVersion": "4.0.1",
  // It is based directly on the base type without intermediary profiles
  "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Questionnaire",
  // It changes the base type, among others, by making the title field mandatory
  "differential": {
    "element": [{
      "id": "Questionnaire.title",
      "min": 1,
      "mustSupport": true,
      ...
    }, ...]},
  ...
}
```

While the above example is trivial, the customisations achievable via profiling can be extensive. As
a result, it is crucial for implementations to understand what profiles are being used when
exchanging data.

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
a hospital's patient management system. Again, the generic MIME type forces such a client to
download the file to determine if it is indeed a `QuestionnaireResponse`.

These problems would be mitigated to some extent if FHIR resources were inlined into Matrix events.
However, serialized resources contain only limited information about the underlying
`StructureDefinition`. Most importantly the base resource type is missing, making it difficult for
implementations that support a base type but not a specific profile to fall back in a reasonable
way. Furthermore, inlining isn't always possible due to the [64 KiB event size limit] and no
suitable event type or content block exists, as of writing.

## Proposal

To enable the compatible and efficient exchange of FHIR resources in either inline or file form, a
new event type `m.fhir` is introduced. This type mandates the following properties in `content`:

- `m.fhir.structure_definition` (object, required): Information about the resource's
  `StructureDefinition`.
  - `url` (string, required): The [canonical URL] of the most specific `StructureDefinition`
    describing the resource. This is equivalent to [`StructureDefinition.url`].
  - `version` (string, required): The version of the `StructureDefinition`. This is equivalent to
    [`StructureDefinition.version`].
  - `type` (string, required): The `StructureDefinition`'s base type. This is equivalent to
    [`StructureDefinition.type`].
  - `fhir_version` (string, required): The version of the FHIR specification on which the
    `StructureDefinition` is based. This is equivalent to [`StructureDefinition.fhirVersion`].
- `m.fhir.resource` (object, required if `m.file` is missing): The serialised JSON if it fits within
  the [64 KiB event size limit].
- `m.fhir.file` (object, required if `m.fhir.resource` is missing): An [MSC3551] content block describing
  an uploaded JSON or XML serialisation of the resource if it is too large to be inlined.
- `m.text` (object, required): Alternativ textual information that shall be displayed in case the client is not able
  to render the fhir content.
- `m.file` (object, optional): A downloadable alternative for the content of the fhir structure
  for example an editable pdf file represanting the same information

``` json5
{
  "type": "m.fhir",
  "content": {
    // Metadata to help identify the resource
    "m.fhir.structure_definition": {
      "url": "https://gematik.de/fhir/isik/StructureDefinition/ISiKFormularDefinition",
      "version": "5.0.0",
      "type": "Questionnaire",
      "fhir_version": "4.0.1",
    },
    // Either: The resource in inline form
    "m.fhir.resource": {
      "resourceType": "Questionnaire",
      "title": "Dr. Dre's anamnesis questionnaire for new patients",
      // further properties as per the questionnaire's schema
    },
    // Or: A file representing the resource
    "m.fhir.file": {
      "url": "mxc://example.org/abcd1234",
      "mimetype": "application/fhir+json",
      // further properties as per MSC3551
    }
    // alternativ text in case the client does not support the fhir content
    "m.text": [
      { "body": "<b>Please complete the anamnesis question and send it back.<b>", "mimetype": "text/html" },
      { "body": "Please complete the anamnesis question and send it back." }
      ]
    }
    // optional downloadable file representation of the fhir content
    "m.file": {
      "url": "mxc://example.org/abcd5678",
      "mimetype": "application/pdf",
      // further properties as per MSC3551
    }
  }
}
```

The `url` and `version` properties, on the one hand, allow implementations with support for the
particular profile to activate dedicated display or processing logic. The `type` and `fhir_version`
properties, on the other hand, enable implementations *without* support for the specific profile to
offer fallback behaviour if they have generic support for the resource's base type.

## Potential issues

FHIR includes generic resources such as [`Bundle`] which wrap other resources. The metadata in
`m.fhir.structure_definition` will not help clients understand the wrapped content without
downloading it in these cases. Dedicated event types or further metadata fields may be introduced in
future to cater to these situations.

## Alternatives

Dedicated MIME types per resource, version and serialisation format could be introduced. Since FHIR
supports a vast number of resources and profiles this doesn't appear practical, however.

[RFC 2045] allows MIME types to include modifying parameters. The contents of
`m.fhir.structure_definition` could, therefore, be included alongside the media type[^1].

``` http
Content-type: application/fhir+json; url="https://gematik.de/fhir/isik/StructureDefinition/ISiKFormularDefinition"; ...
```

This would allow reusing the `m.file` message type but leaks metadata to the home server in
[`POST /_matrix/media/v3/upload`].

## Security considerations

Malicious clients could attempt to trick other clients into automatically downloading files by
faking the metadata in `m.fhir.structure_definition`. As a minimal defense, clients SHOULD
sanity-check the size of the downloaded file by issuing a HEAD request and refuse to automatically
download large files without explicit user consent.

## Unstable prefix

While this MSC is not considered stable, the following identifiers should be used:

- `m.fhir` → `de.gematik.msc4302.fhir`
- `m.fhir.structure_definition` → `de.gematik.msc4302.fhir.structure_definition`
- `m.fhir.resource` → `de.gematik.msc4302.fhir.resource`

Note that `m.file` has its own prefixing requirements as per [MSC3551].

## Dependencies

None.

[^1]: This could also be done by reusing the `profile` parameter from [RFC 6906]. Since the term
    "profile" already has a specific meaning within the FHIR standard, this could be confusing,
    however.

  [FHIR]: https://hl7.org/fhir/
  [`Questionnaire`]: http://hl7.org/fhir/StructureDefinition/Questionnaire
  [`ISiKFormularDefinition`]: https://gematik.de/fhir/isik/StructureDefinition/ISiKFormularDefinition
  [`StructureDefinition`]: https://build.fhir.org/structuredefinition.html
  [canonical URL]: https://build.fhir.org/references.html#canonical
  [`m.file`]: https://spec.matrix.org/v1.14/client-server-api/#mfile
  [`QuestionnaireResponse`]: http://hl7.org/fhir/StructureDefinition/QuestionnaireResponse
  [64 KiB event size limit]: https://spec.matrix.org/v1.16/client-server-api/#size-limits
  [`StructureDefinition.url`]: https://build.fhir.org/structuredefinition-definitions.html#StructureDefinition.url
  [`StructureDefinition.version`]: https://build.fhir.org/structuredefinition-definitions.html#StructureDefinition.version
  [`StructureDefinition.type`]: https://build.fhir.org/structuredefinition-definitions.html#StructureDefinition.type
  [`StructureDefinition.fhirVersion`]: https://build.fhir.org/structuredefinition-definitions.html#StructureDefinition.fhirVersion
  [MSC3551]: https://github.com/matrix-org/matrix-spec-proposals/pull/3551
  [`Bundle`]: http://hl7.org/fhir/StructureDefinition/Bundle
  [RFC 2045]: https://datatracker.ietf.org/doc/html/rfc2045#section-5
  [`POST /_matrix/media/v3/upload`]: https://spec.matrix.org/v1.14/client-server-api/#post_matrixmediav3upload
  [RFC 6906]: https://datatracker.ietf.org/doc/html/rfc6906
