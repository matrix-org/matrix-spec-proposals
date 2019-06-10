# Proposal for Open Governance of Matrix.org 

This whole document is the proposed constitution proposal for Matrix.org, and
will form the basis of the first full Articles of Association (AoA) for [The
Matrix.org Foundation
C.I.C.](https://beta.companieshouse.gov.uk/company/11648710) - a non-profit
legal entity incorporated to act as the neutral guardian of the Matrix
decentralised communication standard on behalf of the whole Matrix community.

See https://matrix.org/blog/2018/10/29/introducing-the-matrix-org-foundation-part-1-of-2/
for more context.

This obsoletes [MSC1318](https://github.com/matrix-org/matrix-doc/issues/1318).

**This MSC is now formalised in the official Rules of the Matrix.org Foundation,
maintained at https://docs.google.com/document/d/1MhqsuIUxPc7Vf_y8D250mKZlLeQS6E39DPY6Azpc2NY**

## Introduction

Historically the core team of Matrix has been paid to work on it by the same
employer (currently New Vector; the startup incorporated to hire the core
team in Aug 2017).  Whilst convenient in initially getting Matrix built, we
recognise that this could create a potential conflict of interest between the
core team’s responsibilities to neutrally support the wider Matrix.org ecosystem
versus the need for New Vector to be able to support the team, and it has always
been the plan to set up a completely neutral custodian for the standard once it
had reached sufficient maturity.

This proposal seeks to establish a new open governance process for Matrix.org,
such that once the specification has finally been ‘born’ and reached an initial
‘r0’ release across all APIs, control of Matrix.org can be decoupled from New
Vector and better support contributions from the whole ecosystem.

The concepts here are somewhat inspired by [Rust’s Governance
Model](https://github.com/rust-lang/rfcs/blob/master/text/1068-rust-governance.md);
a highly regarded solution to a similar problem: an ambitious
open-source project which has been too many years in the making, incubated at
first by a single company (Mozilla Corporation), which also enjoys a very
enthusiastic community!

## Overview

Governance of the project is split into two teams: the Spec Core Team and the
Guardians of the Foundation.  In brief:

The Spec Core Team are the technical experts who curate and edit the Matrix
Specification from day to day, and so steer the evolution of the protocol by
having final review over which Matrix Spec Changes (MSCs) are merged into the
core spec.

The Guardians are the legal directors of the non-profit Foundation, and are
responsible for ensuring that the Foundation (and by extension the Spec Core
Team) keeps on mission and neutrally protects the development of Matrix.
Guardians are typically independent of the commercial Matrix ecosystem and may
even not be members of today’s Matrix community, but are deeply aligned with the
mission of the project.  Guardians are selected to be respected and trusted by
the wider community to uphold the guiding principles of the Foundation and keep
the other Guardians honest.

In other words; the Spec Core Team builds the spec, and the Guardians provide an
independent backstop to ensure the spec evolves in line with the Foundation's
mission.

## Guiding Principles

The guiding principles define the core philosophy of the project, and will be a
formal part of the final Articles of Association of the Matrix.org Foundation.

### Matrix Manifesto

We believe:

 * People should have full control over their own communication.

 * People should not be locked into centralised communication silos, but instead
   be free to pick who they choose to host their communication without limiting
   who they can reach.

 * The ability to converse securely and privately is a basic human right.

 * Communication should be available to everyone as a free and open,
   unencumbered, standard and global network.

### Mission

The Matrix.org Foundation exists to act as a neutral custodian for Matrix and to
nurture it as efficiently as possible as a single unfragmented standard, for the
greater benefit of the whole ecosystem, not benefiting or privileging any single
player or subset of players.

For clarity: the Matrix ecosystem is defined as anyone who uses the Matrix
protocol. This includes (non-exhaustively):

 * End-users of Matrix clients.
 * Matrix client developers and testers.
 * Spec developers.
 * Server admins.
 * Matrix packagers & maintainers.
 * Companies building products or services on Matrix.
 * Bridge developers.
 * Bot developers.
 * Widget developers.
 * Server developers.
 * Matrix room and community moderators.
 * End-users who are using Matrix indirectly via bridges.
 * External systems which are bridged into Matrix.
 * Anyone using Matrix for data communications.

"Greater benefit" is defined as maximising:

 * the number of Matrix-native end-users reachable on the open Matrix network.
 * the number of regular users on the Matrix network (e.g. 30-day retained federated users).
 * the number of online servers in the open federation.
 * the number of developers building on Matrix.
 * the number of independent implementations which use Matrix.
 * the number of bridged end-users reachable on the open Matrix network.
 * the signal-to-noise ratio of the content on the open Matrix network (i.e. minimising spam).
 * the ability for users to discover content on their terms (empowering them to select what to see and what not to see).
 * the quality and utility of the Matrix spec (as defined by ease and ability
   with which a developer can implement spec-compliant clients, servers, bots,
   bridges, and other integrations without needing to refer to any other
   external material).

N.B. that we consider success to be the growth of the open federated network
rather than closed deployments. For example, if WhatsApp adopted Matrix it
wouldn’t be a complete win unless they openly federated with the rest of the
Matrix network.

### Values

As Matrix evolves, it's critical that the Spec Core Team and Guardians are
aligned on the overall philosophy of the project, particularly in more
subjective areas.  The values we follow are:

 * Supporting the whole long-term ecosystem rather than individual stakeholder gain.
 * Openness rather than proprietary lock-in.
 * Interoperability rather than fragmentation.
 * Cross-platform rather than platform-specific.
 * Collaboration rather than competition.
 * Accessibility rather than elitism.
 * Transparency rather than stealth.
 * Empathy rather than contrariness.
 * Pragmatism rather than perfection.
 * Proof rather than conjecture.

Patent encumbered IP is strictly prohibited from being added to the standard.

Making the specification rely on non-standard/unspecified behaviour of other
systems or actors (such as SaaS services, even open-sourced, not governed by a
standard protocol) shall not be accepted, either.

## The Spec Core Team

The contents and direction of the Matrix Spec is governed by the Spec Core Team;
a set of experts from across the whole Matrix community, representing all
aspects of the Matrix ecosystem.  The Spec Core Team acts as a subcommittee of
the Foundation.

Members of the Spec Core Team pledge to act as a neutral custodian for Matrix on
behalf of the whole ecosystem and uphold the Guiding Principles of the project
as outlined above.  In particular, they agree to drive the adoption of Matrix as
a single global federation, an open standard unencumbered from any proprietary
IP or software patents, minimising fragmentation (whilst encouraging
experimentation), evolving rapidly, and prioritising the long-term success and
growth of the overall network over individual commercial concerns.

Spec Core Team members need to have significant proven domain experience/skill
and have had clear dedication and commitment to the project and community for >6
months. (In future, once we have subteams a la Rust, folks need to have proven
themselves there first).

Members need to demonstrate ability to work constructively with the rest of the
team; we want participation in the Spec Core Team to be an efficient, pleasant and
productive place, even in the face of inevitable disagreement. We do not want a
toxic culture of bullying or competitive infighting.  Folks need to be able to
compromise; we are not building a culture of folks pushing their personal
agendas at the expense of the overall project.

The team should be particularly vigilant against 'trojan horse' additions to the
spec - features which only benefit particular players, or are designed to
somehow cripple or fragment the open protocol and ecosystem in favour of
competitive advantage. Commercial players are of course free to build
proprietary implementations, or use custom event types, or even custom API
extensions (e.g. more efficient network transports) - but implementations must
fall back to interoperating correctly with the rest of the ecosystem.

### Spec Core Team logistics

The Spec Core Team itself will be made up of roughly 8 members + 1 project lead.
Roughly half the members are expected to be from the historical core team
(similar to Rust).  The team must have 5 members to be able to function, with
the aim of generally having between 7 and 9 members.

In future we may also have sub-teams (like Rust - e.g. CS/AS/Push API; SS API;
IS API; Crypto), but as a starting point we are beginning with a single core
team in the interests of not over-engineering it and scaling up elastically.

Spec Core Team members need to be able to commit to at least 1 hour a week of
availability to work on the spec and (where relevant) reference implementations.
Members must arrange their own funding for their time.

Responsibilities include:

 * Reviewing Matrix Spec Change proposals and Spec PRs.

 * Contributing to and reviewing reference implementations of Matrix Spec Change
   proposals.

 * Shepherding Matrix Spec Changes on behalf of authors where needed.

 * Triaging Matrix Spec issues.

 * Coordinating reference implementations.

 * Ensuring the code of conduct for +matrix:matrix.org community rooms is
   maintained and applied.

If members are absent (uncontactable) for more than 8 weeks without prior
agreement, they will be assumed to have left the project.

Spec Core Team members can resign whenever they want, but must notify the rest
of the team and the Guardians on doing so.

New additions to the team must be approved by all current members of the team.
Membership has to be formally proposed by someone already on the Spec Core Team.

Members can be removed from the team if 75% of the current members approves and
agrees they are no longer following the goals and guiding principles of the
project.  (The 75% is measured of the whole team, including the member in
question).

Guardians act as a safety net, and can appoint or remove Spec Core Team members
(requiring approval by 75% of the current Guardians) if the Spec Core Team is
unable to function or is failing to align with the Foundation's mission.

It's suggested that one of the Spec Core Team members should also be a Guardian,
to facilitate information exchange between the Guardians and the Spec Core Team,
and to represent the technical angle of the project to the other Guardians.

The project lead role acts to coordinate the team and to help steer the team to
consensus in the event of failing to get agreement on a Matrix Spec Change.
Every 12 months, a vote of confidence is held in the project lead, requiring the
approval of 75% of the current Spec Core Team members for the lead to be
renewed.  There is no maximum term for the project lead.  The lead may be
removed by the core team at any point (requiring 75% approval of current
members), and may resign the role at any point (notifying the team and the
Guardians).  The lead automatically resigns the role if they resign from the
Spec Core Team. Resignation automatically triggers selection of a new lead, who
must be selected from the existing Spec Core Team with 75% approval from current
members within 14 days.

It is vital that the core spec team has strong domain expertise covering all
different domains of the spec (e.g. we don't want to end up with a core spec
team where nobody has strong experience in cryptography)

The initial Spec Core Team (and their domain areas) is:

 * Matthew Hodgson (Lead, Guardian)
 * Erik Johnston (Servers)
 * Richard van der Hoff (Servers, Cryptography)
 * David Baker (Clients, IS API, Push API, Media)
 * Hubert Chathi (Cryptography, General)
 * Andrew Morgan (Servers, AS API, Spec Process)
 * Travis Ralston (Bots and Bridges & AS API, Media, acting with Dimension hat on)
 * Alexey Rusakov (Clients on behalf of Community)
 * TBD

MSCs require approval by 75% of the current members of the Spec Core Team to
proceed to Final Comment Period (see https://matrix.org/docs/spec/proposals for
the rest of the MSC process).

Even though a threshold of only 75% is required for approval, the Spec Core Team
is expected to seek consensus on MSCs.

The above governance process for the Spec Core Team is considered as part of the
spec and is updated using the Matrix Spec Change process.  However, changes to
the governance process also require approval by 75% of the current Guardians
(acting as a formal decision of the Foundation's Directors), in order to ensure
changes are aligned with the Foundation's mission.  For avoidance of doubt, Spec
Core Team votes and Guardians' votes are distinct and a person having both hats
has to vote independently on both forums with the respective hat on.

Spec Core Team decisions (e.g. appointing/removing members and lead)
should be published openly and transparently for the public.

## The Guardians

*This section will be used as the basis for the legal responsibilities of
Directors in the Articles of Association of the Foundation.*

The Guardians form the legal Board of Directors of The Matrix.org Foundation CIC
(Community Interest Company).  They are responsible for ensuring the Foundation
is following its guiding principles, and provide a safety mechanism if the
structure of the Spec Core Team runs into trouble.

In practice, this means that:

 * Guardians are responsible for ensuring the Spec Core Team continues to
   function, and have the power to appoint/dismiss members of the spec core team
   (with the agreement of 75% of the Guardians) to address issues with the Spec
   Core Team.
 * Guardians must keep each other honest, providing a ‘checks and balances’.
   mechanism between each other to ensure that all Guardians and the Spec Core
   Team act in the best interests of the protocol and ecosystem.
 * Guardians may dismiss members of the Spec Core Team who are in serious
   breach of the guiding principles.
 * Guardians may appoint members of the Spec Core Team to break deadlocks in the
   unanimous consent requirement for the Spec Core Team when appointing new
   members.
 * Guardians may also override deadlocks when appointing a Spec Core Team leader
   (with approval of 75% of the current Guardians).
 * Guardians must approve changes to the above Guiding Principles (with approval
   of 75% of the current Guardians)
 * Guardians are responsible for approving use of the Foundation's assets
   (e.g. redistributing donations).
 * In future, Guardians may also be responsible for ensuring staff are hired by
   the Foundation to support administrative functions and other roles required
   to facilitate the Foundation's mission.
 * As well as the Spec Core Team committee, they may also oversee committees for
   other areas such as marketing Matrix.org, registering custom event types,
   or "Made for Matrix" certification.
 * Guardians are responsible for choosing if, when and how staff are located by
   the Foundation to fill administrative and other functions required to
   facilitate the Foundations' mission.
 * Guardians are responsible for choosing if and when additional committees are
   formed, and to oversee those committees.
 * Guardians are not required to be involved on a day-to-day basis, however
   those not taking a hands on approach are required to monitor to ensure a
   suitable balance is kept by those that do.

Guardians are chosen typically to be independent of the commercial Matrix
ecosystem (and especially independent from New Vector), and may even not be
members of today’s Matrix community. However, they should be deeply aligned with
the mission of the project, and respected and trusted by the wider community to
uphold the guiding principles of the Foundation and keep the other Guardians
honest.

Guardians are responsible for maintaining and updating the Guiding Principles
and Articles of Association of the Foundation if/when necessary. Changes to the
Guiding Principles require approval from 75% of the current Guardians and are
passed as a 'special resolution' of the board.

New Guardians may be appointed with approval from 75% of the current Guardians.

Guardians may resign at any time, with notification to the board.

Guardians may be removed due to serious breach of the guiding principles with
approval by 75% of the other current Guardians, or if absent from 3 consecutive
board meetings, or if they are legally disqualified from acting as a Director.

We aim to recruit roughly 5 Guardians.  The initial Guardians are:

 * Matthew Hodgson (CEO/CTO, New Vector)
 * Amandine Le Pape (COO, New Vector)
 * TBA (agreed, needs paperwork)
 * TBD
 * TBD

The intention is for Matthew & Amandine (the original founders of Matrix) to
form a minority of the Guardians, in order to ensure the neutrality of the
Foundation relative to Matthew & Amandine’s day jobs at New Vector.

Guardians must arrange their own funding for their time.

Guardian decisions (e.g. appointing/removing guardians; changes to the spec core
team; etc) should be published openly and transparently for the public.

## The Code Core Team (aka The Core Team)

The "Core Team" (or the "Code Core Team", to disambiguate from the Spec Core
Team) is a loose term that describes the set of people with access to commit
code to the public https://github.com/matrix-org repositories, who are either
working on matrix.org's reference implementations or the spec itself. Commit
access is decided by those responsible for the projects in question, much like
any other open source project.  Anyone is eligible for commit access if they
have proved themselves a valuable long-term contributor, uphold the guiding
principles and mission of the project and have proved themselves able to
collaborate constructively with the existing core team. Active participation in
the core team is also signified by membership of the +matrix:matrix.org Matrix
community.

Responsibilities include:
 * Helping ensure the quality of the projects' code repositories.
 * Ensuring all commits are reviewed.
 * Ensuring that all projects follow the Matrix spec.
 * Helping architect the implementations.
 * Contributing code to the implementations.
 * Fostering contributions and engaging with contributors constructively in a
   way that fosters a healthy and happy community.
 * Following the Guiding Principles and promoting them within the community.

Code Core Team members must arrange their own funding for their time.

## Functions of the Foundation

 * Independent legal entity which acts as neutral custodian of Matrix.
 * Gathers donations.
 * Owns the core Matrix IP in an asset lock, which shall be transferred from New Vector:
   * Owns the matrix.org domain and branding.
   * Owns the copyright of the reference implementations of Matrix (i.e. everything in https://github.com/matrix-org).
     By assigning copyright to the Foundation, it’s protected against New Vector ever being tempted to relicense it.
   * Owns the IP of the website.
   * Owns the Matrix.org marketing swag (t-shirts, stickers, exhibition stands etc).
 * Responsible for finding someone to run the Matrix.org homeserver (currently New Vector).
 * Publishes the spec.
 * Responsible for tools and documentation that support the spec.
 * Responsible for ensuring reference implementations and test suite exists for the spec.
 * Publishes the website (including ensuring This Week In Matrix and similar exist to promote independent projects).
 * Manages any future IANA-style allocations for Matrix, such as:
   * mx:// URI scheme.
   * TCP port 8448.
   * .well-known URIs
* Ensures that Matrix promotion is happening (e.g. ensuring that meetups &
  events & community activity is supported).

In future:

 * Contracts entities to work on Matrix if such contracts help the Foundation to
   fulfil its mission and obey the Guiding Principles (e.g. redistributing
   donations back to fund development of reference implementations or compliance
   kits).
 * Manages a "Made for Matrix" certification process? (to confirm that products
   are actually compatible with Matrix).

## Timings

The Foundation was incorporated in October 2018 as a UK limited by guarantee
private company, using generic non-profit articles of association combined with
a high-level mission lock aligned with the above:

> 4. The objects of the Foundation are for the benefit of the community as a whole
> to:

> 4.1.1  empower users to control their communication data and have freedom over
> their communications infrastructure by creating, maintaining and promoting
> Matrix as an openly standardised secure decentralised communication protocol and
> network, open to all, and available to the public for no charge;

> 4.1.2  build and develop an appropriate governance model for Matrix through the
> Foundation, in order to drive the adoption of Matrix as a single global
> federation, an open standard unencumbered from any proprietary intellectual
> property and/or software patents, minimising fragmentation (whilst encouraging
> experimentation), maximising speed of development, and prioritising the long-
> term success and growth of the overall network over the commercial concerns of
> an individual person or persons.

The foundation was then converted into a Community Interest Company, formalising
its non-profit status under the approval of the independent [Community Interest
Companies Regulator](https://www.gov.uk/government/organisations/office-of-the-regulator-of-community-interest-companies), 
which took effect Jan 2019.

We are currently planning to release r0 of the Matrix Spec at the end of Jan 2019, and
finalise the Foundation's articles of association shortly afterwards based on the
contents of this MSC once passed FCP.

This will coincide with the formal asset transfer of Matrix.org's assets from
New Vector Ltd, and the appointment of the remaining Guardians.
