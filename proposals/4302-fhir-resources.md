# MSC4302: Exchanging FHIR resources via Matrix events

## A brief abstract of FHIR, resources and profiles

[FHIR] (pronounced "fire") is a globally established standard for exchanging healthcare information
electronically. The base building blocks of FHIR are so-called *resources*. Resources have a type
that defines their base schema. This schema can be further customised through one or more
*profiles*.

As an example, [`Patient`] is the resource type for patients which defines several fields. Among
these are the *optional* property `birthDate` for the person's date of birth and `photo` for any
number of pictures of the person.

[`TIPatient`] is a profile on `Patient` defined by Germany's national health agency, gematik, for
use within their own network (TI). It customises the schema of `Patient` in several ways, such as
making `birthDate` required rather than optional.

[`EPAPatient`], in turn, is another profile on `Patient` defined by gematik, specifically for use in
Germany's digital patient file (EPA). `EPAPatient` builds on top of `TIPatient` and adds furhter
customisations like, for instance, the requirement for the elements of `photo` to include the field
`contentType` if the picture is supplied inline as Base64.

As a result, the valid schema of a FHIR resource for a patient within Germany's digital patient file
is determined by the combination of the resource type `Patient` and the profiles `TIPatient` and
`EPAPatient`.

Both resource types and profiles can be uniquely identified by their [canonical URL].

## The problems of using FHIR resources in Matrix

FHIR resources can be serialised into JSON or XML which can be transmitted via the [`m.file`]
message type with a MIME type of `application/fhir+json` or `application/fhir+xml`. However, the
generic MIME type doesn't let clients understand what resource is contained in the file without
downloading it. This is suboptimal because clients may want to render a rich UI for certain resource
types and profiles. An example of this is the [`Questionnaire`] resource which represents a form
that can be filled out by the recipient and responded to with a [`QuestionnaireResponse`] resource.

Similarly, clients that connect external systems to Matrix may want to automatically process certain
resources. For instance, an anamnesis bot may want to export received `QuestionnaireResponse`s into
a surgery's patient management system. Again, the generic MIME type forces such clients to download
the file to determine if it is indeed a `QuestionnaireResponse`.

These problems would be obliterated if FHIR resources were inlined into Matrix events. However, this
isn't always possible due to the [64 KiB event size limit]. Additionally, no suitable event type or
content block exists, as of writing.

## Proposal

A new event type `m.fhir.resource` is introduced with the following properties in `content`:

- `canonical_url` (string, required): The resource's [canonical URL], that is the globally unique
  identifier defining its base schema. MAY contain a version suffix separated by `|` as per the FHIR
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
  [`TIPatient`]: https://simplifier.net/packages/de.gematik.ti/1.1.1/files/2968490
  [`EPAPatient`]: https://simplifier.net/packages/de.gematik.epa/1.2.0/files/2968520/~overview
  [canonical URL]: https://build.fhir.org/references.html#canonical
  [`m.file`]: https://spec.matrix.org/v1.14/client-server-api/#mfile
  [`Questionnaire`]: https://www.hl7.org/fhir/questionnaire.html
  [`QuestionnaireResponse`]: https://build.fhir.org/questionnaireresponse.html
  [64 KiB event size limit]: https://spec.matrix.org/v1.16/client-server-api/#size-limits
  [MSC3551]: https://github.com/matrix-org/matrix-spec-proposals/pull/3551
  [`Bundle`]: http://hl7.org/fhir/StructureDefinition/Bundle
  [RFC 2045]: https://datatracker.ietf.org/doc/html/rfc2045#section-5
  [`POST /_matrix/media/v3/upload`]: https://spec.matrix.org/v1.14/client-server-api/#post_matrixmediav3upload
  [RFC 6906]: https://datatracker.ietf.org/doc/html/rfc6906
