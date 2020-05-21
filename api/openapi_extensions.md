# OpenAPI Extensions

For some functionality that is not directly provided by the OpenAPI v2
specification, some extensions have been added that are to be consistent
across the specification. The defined extensions are listed below. Extensions
should not break parsers, however if extra functionality is required, aware
parsers should be able to take advantage of the added syntax.

## Extensible Query Parameters

<!-- TODO: Remove and change instances to 'explode' after OpenAPI/Swagger v3 update -->

If a unknown amount of query parameters can be added to a request, the `name`
must be `fields...`, with the trailing ellipses representing the possibility
of more fields.

Example:

```
  - in: query
    name: fields...
    type: string
```

## Using oneOf to provide type alternatives

<!-- TODO: Remove this section after upgrading to OpenAPI v3 -->

`oneOf` (available in JSON Schema and Swagger/OpenAPI v3 but not in v2)
is used in cases when a simpler type specification as a list of types
doesn't work, as in the following example:
```
  properties:
    old: # compliant with old Swagger
      type:
        - string
        - object # Cannot specify a schema here
    new: # uses oneOf extension
      oneOf:
        - type: string
        - type: object
          title: CustomSchemaForTheWin
          properties:
            ...
```

## OpenAPI 3's "2xx" format for response codes

<!-- TODO: Remove this section after upgrading to OpenAPI v3 -->

In some cases, the schema will have HTTP response code definitions like
`2xx`, `3xx`, and `4xx`. These indicate that a response code within those
ranges (`2xx` = `200` to `299`) is valid for the schema.
