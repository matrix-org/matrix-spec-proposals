# MSC4265: Data Protection Officer contact in `/.well-known/matrix/support`

[GDPR] Article 37 Nr. 1 requires data controllers and processors to designate a
Data Protection Officer (DPO). Furthermore, Article 37 Nr. 7 requires that the
DPO's contact details be publicised. This is most commonly done via the privacy
policy document.

In Matrix, a homeserver's privacy policy is currently only made accessible via
APIs during [account registration]. This prevents clients from easily displaying
the contact information at later times and adds to the user's burden in finding
them.

Additionally, homeservers themselves can have a similar need to get in touch
with another server's DPO, for instance to inform them about requests for
erasure as required by [GDPR] Article 17 Nr. 2.

While a server's support document under [/.well-known/matrix/support] can expose
an "admin" contact, this might not be specific enough for the purposes outlined
above – especially since server administrators and data protection officers are
usually different roles in companies.

The present proposal attempts to address these problems by exposing a dedicated
DPO contact in the server's support document.

## Proposal

A new role `m.role.dpo` is introduced for `Contact`s in
[/.well-known/matrix/support]

``` json5
{
  "contacts": [
    {
      "email_address": "dpo@pizza.org",
      "matrix_id": "@dpo:pizza.org",
      "role": "m.role.dpo"
    },
    ...
  ],
  "support_page": "https://www.pizza.org/support"
}
```

Servers are *not* required to provide an `m.role.dpo` contact.

## Potential issues

The DPO contact details being duplicated in two places introduces the
possibility that they get out of sync. Given that these contacts should rarely
change, this seems like a small problem, however.

## Alternatives

Rather than exposing the DPO's contact details, the support document could
publish the privacy policy URL, for instance via [MSC4266]. This could also be
considered an additional feature rather than a replacement, however.

## Security considerations

None.

## Unstable prefix

While this proposal is unstable, `m.role.dpo` should be referred to as
`org.matrix.msc4265.role.dpo`.

## Dependencies

None.

  [GDPR]: https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
  [account registration]: https://spec.matrix.org/v1.13/client-server-api/#terms-of-service-at-registration
  [/.well-known/matrix/support]: https://spec.matrix.org/v1.13/client-server-api/#getwell-knownmatrixsupport
  [MSC4266]: https://github.com/matrix-org/matrix-spec-proposals/pull/4266
