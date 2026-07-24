# MSC4456: Harms taxonomy

> [!WARNING]
> **Content Warning**: This proposal discuses and identifies harmful content, but does not attempt
> to describe the harm posed in detail. This includes identifiers for child safety, sexual abuse,
> self-harm, and other types of harm a user may encounter on the open internet.

*This MSC is part of "Reporting v2" - a project led by the Foundation’s T&S team to improve communication
and effectiveness of reports on Matrix.*

When a user reports something, they ideally are able to express their opinion for what kind of harm
they believe is caused by that something. Safety teams use this information to guide their initial
investigation, and can reclassify a report as needed to better match the harm actually caused. This
is in contrast to an (often blank) free-form report reason where the safety team needs to guess at
the harm caused.

Identified harms are also helpful when events or searches are rejected due to backend safety tooling,
like in [MSC4387](https://github.com/matrix-org/matrix-spec-proposals/pull/4387).

This proposal introduces a new [appendix](https://spec.matrix.org/v1.18/appendices/)-like document to
list out harms common to safety legislation across the world. Other proposals are expected to actually
use this taxonomy - this proposal simply introduces them as a dependency for other MSCs.


## Proposal

The following standardized harm identifiers are expected to be used by Matrix safety tooling and features.
For example, when reporting something, the user can express their opinion of what kind of harm is caused
by the thing they're reporting. Similarly, a (policy) server might reject an event due to a common
harm.

A [MSC4518](https://github.com/matrix-org/matrix-spec-proposals/pull/4518)-style registry is created
to contain the identifiers. The registry lists the identifier, a suggested name, and supported spec
versions where server support is required. Additions/changes/removals are managed by the normal MSC
process, though are expected to receive significant review from the Foundation's T&S team.

Where harm identifiers are used in an endpoint's request schema, servers MUST support the identifiers
which overlap the server's own supported spec versions. Where harm identifiers are used in a response
schema, servers SHOULD NOT use harm identifiers outside of their supported spec versions. For example,
if a server supports spec versions v1.12 through v1.15, it MUST accept harm identifiers supported in
versions v1.12 through v1.15 as well, but SHOULD NOT return any identifiers from v1.16+ or v1.11 and
older.

**Note**: For editorial ease, this proposal SHOULD be implemented as an [appendix](https://spec.matrix.org/v1.19/appendices/)
rather than as an explicit registry. Later, when more proposals require registries, this proposal's
registry can be formally created. Note that by using the appendices means that "supported spec versions"
requirements are implied through the spec's global versioning system - the appendices would only list
the identifiers supported in that spec version.

Categories are used to organize the identifiers - they are non-normative.

The identifiers chosen represent the similarities between various safety legislations (UK, Australia,
Canada, EU, etc) and what other services offer to their users in reporting flows, especially Bluesky. The identifiers use
the [Common Namespaced Identifier Grammar](https://spec.matrix.org/v1.18/appendices/#common-namespaced-identifier-grammar),
and therefore allow custom harms to be represented. When a proposal uses harm identifiers, it SHOULD
ensure that custom identifiers are accompanied by a specified identifier for added clarity/compatibility.

The harms, their categories, and suggested names are:

**Spam**

* `m.spam` - General/Other
* `m.spam.fraud` - Fraud/Phishing
* `m.spam.impersonation` - Impersonation
* `m.spam.election_interference` - Election Interference
* `m.spam.flooding` - Flooding

**Adult Content & Safety**

* `m.adult` - General/Other
* `m.adult.sexual_abuse` - Sexual Abuse
* `m.adult.ncii` - Non-Consensual Intimate Imagery
  * Recognizing that these links deal with sexual abuse topics, more information about NCII can be
    found at [StopNCII](https://stopncii.org/), [INHOPE](https://inhope.org/EN/articles/what-is-ncii),
    and [Meta's Safety Center](https://www.meta.com/safety/topics/bullying-harassment/ncii/).
* `m.adult.deepfake` - Deepfake
* `m.adult.animal_sexual_abuse` - Animal Sexual Abuse
* `m.adult.sexual_violence` - Sexual Violence

**Harassment**

* `m.harassment` - General/Other
* `m.harassment.trolling` - Trolling
* `m.harassment.targeted` - Targeted
* `m.harassment.hate` - Hate
* `m.harassment.doxxing` - Doxxing/Personal Information

**Violence**

* `m.violence` - General/Other
* `m.violence.animal_welfare` - Animal Welfare
* `m.violence.threats` - Threatening/Threats
* `m.violence.graphic` - Graphic/Gore
* `m.violence.glorification` - Glorification/Promotion
* `m.violence.extremist` - Extremism
* `m.violence.human_trafficking` - Human Trafficking
* `m.violence.domestic` - Domestic/Intimate Partner

**Child Safety**

* `m.child_safety` - General/Other
* `m.child_safety.csam` - Child Sexual Abuse Material (CSAM)
* `m.child_safety.grooming` - Grooming
* `m.child_safety.privacy_violation` - Privacy
* `m.child_safety.harassment` - Harassment

**Dangers**

* `m.danger` - General/Other
* `m.danger.self_harm` - Self Harm
* `m.danger.eating_disorder` - Eating Disorder
* `m.danger.challenges` - Challenges, including Social Media Challenges
* `m.danger.substance_abuse` - Substance Abuse

**Terms of Service**

* `m.tos` - General/Other
* `m.tos.hacking` - Hacking/Computer Misuse
* `m.tos.prohibited` - Prohibited Items (Drugs, Weapons, etc)
* `m.tos.ban_evasion` - Ban Evasion

**Other**

* `m.other` - Other Concern

## Implementation considerations

* A reporting dialog using these harms might have a two-tier dropdown: one for the category (spam,
  harassment, etc) and another for the specific harm caused (defaulting to "General/Other").

  * Because `m.other` is the only harm under the "Other" category, a two-tier dropdown might skip the
    second dropdown for this category.

* Clients should generally aim to keep definitions/titles of the harms brief to be as broadly applicable
  as possible.

* Future MSCs are encouraged to explore using the harms list *safely*. [MSC4204](https://github.com/matrix-org/matrix-spec-proposals/pull/4204)
  and [MSC4205](https://github.com/matrix-org/matrix-spec-proposals/pull/4205) both discuss challenges
  related to classifying content against users.


## Potential issues

* The specified harms list might not be extensive enough to encompass all possible harms in the online
  world. It's expected that custom identifiers for commonly used harms will become MSCs to expand the
  list as needed, per the registry process. Different, future, MSCs are expected to make custom harm
  identifiers usable in specific environments. Custom identifiers would enable localized optionality
  where the standard list is insufficient for regional requirements.


## Alternatives

No significant alternatives. Having a standard taxonomy of harms is important for safety teams to
better handle reports and for safety tooling to express why it has rejected content.


## Security considerations

None relevant. Proposals which build upon the specified harm identifiers may have their own security
considerations.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4456` in place
of `m` in the identifiers. For example, `m.spam` becomes `org.matrix.msc4456.spam`. This prefix change
is done to mitigate possible changes to the final identifiers list ahead of acceptance.


## Dependencies

No direct dependencies. Several other MSCs are expected to build upon this proposal, however.

This proposal has improved utility with [MSC4518](https://github.com/matrix-org/matrix-spec-proposals/pull/4518),
but is capable of being added (temporarily) to the spec via the appendices. If MSC4518 were to progress
slowly through the spec process or ultimately be rejected, this proposal can remain in the appendices
comfortably. A future MSC might find a more suitable long-term home, however.
