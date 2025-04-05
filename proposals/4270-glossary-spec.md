# MSC4270: Matrix Glossary

As the Matrix specification continues to grow, it becomes increasingly important to maintain consistent
terms and phrases across clients, servers, and other implementations. Without this consistency, users
may become confused when switching between implementations or potentially be unable to use another
implementation entirely if the terminology is different enough.

The specification already has some terminology contained in the [Appendices](https://spec.matrix.org/v1.13/appendices/),
though the formal recommendation that users are called "users" is missing, for example. This proposal
defines these historical terms in a new specification document on spec.matrix.org, called the Glossary.

The new Glossary document may be further expanded through MSCs to include words or phrases which are
critically needed for cross-implementation consistency. Translations to other languages are maintained
through the MSC process, and published with the specification.

## Proposal

A new specification document titled "Glossary" is established, residing next to or near the existing
[Appendices](https://spec.matrix.org/v1.13/appendices/) document. This new document has the following
purpose/scope:

* To define words, phrases, and terminology that implementations SHOULD use to provide consistent
  user experience, especially when users are switching between implementations.
* To affect clients, servers, and any other implementations of the Matrix Protocol.
* To be accessible to the widest possible set of languages.

The structure of the document is left as an editorial concern after this MSC is accepted. This MSC
suggests sections covering broad categories with definitions contained within, as later represented
by this proposal.

Removing definitions from the specification requires an MSC, per normal [spec process](https://spec.matrix.org/proposals/).

Adding or updating definitions MUST at minimum affect English definitions, and SHOULD include
translations to the specification's accepted language list (defined later in this proposal). Both
operations require an MSC, again per normal process, though the non-English translations MAY be
affected by one or more follow-on MSCs after the English definitions are added. This is to say that
an MSC which introduces new definitions might first land the English terms, and a future, second,
MSC adds the French definitions for those English words, for example.

The Spec Core Team (SCT) SHOULD consider how well definitions may translate to other languages before
accepting English definitions into the spec, or seek professional external opinion on whether intent
can be maintained through translations.

### Initial definitions

These definitions may be incorporated in a "General" section of the new Glossary document, and are
normative (acceptance of this MSC means accepting the definitions).

**TODO**: Re-add definitions once the remainder of the MSC has been reviewed. 😇

### Initial language support

The SCT does not have expertise in every language, and may be unable to reliably audit translations
for a given language. To support the maximum possible set, within the bounds of professional translation
services, the initial set of supported languages is as follows. A future MSC may add/remove/change this
list. Contributions outside the supported languages list MAY be accepted on a case-by-case basis.

* UK English
* US English (where different from UK English)
* French
* German

## Potential issues

Some terms may not be easily translated or represented by non-English languages. The SCT is encouraged
to request initial translations (where possible) on MSCs which introduce new English terms to the
glossary.

It's also possible that translations could change rapidly if there's disagreement about a given term's
translation. The SCT is encouraged to review the source of translations for authenticity and trust
before accepting an MSC.

## Alternatives

No notable alternatives.

## Security considerations

Translations may be from untrusted sources and could falsely represent the terms they claim to be
translations for. As noted in the Potential Issues section, the SCT is encouraged to review the source
of translations to avoid "trojan horse" contributions.

## Unstable prefix

Not applicable - this MSC covers text, not implementation.

## Dependencies

This MSC has no direct dependencies, but may be depended upon by other MSCs.

[MSC4161](https://github.com/matrix-org/matrix-spec-proposals/pull/4161) is expected to make use of
this MSC.
