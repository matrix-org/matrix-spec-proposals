# Proposal for Open Governance of Matrix.org 

This whole document is a **work in progress** draft of a constitution proposal
for open governance for Matrix.org, and forms the basis of the first full
Articles of Association (AoA) for [The Matrix.org Foundation
C.I.C.](https://beta.companieshouse.gov.uk/company/11648710) - a non-profit legal
entity incorporated to act as the neutral guardian of the Matrix decentralised
communication standard on behalf of the whole Matrix community.

See https://matrix.org/blog/2018/10/29/introducing-the-matrix-org-foundation-part-1-of-2/
for more context.

This obsoletes [MSC1318](https://github.com/matrix-org/matrix-doc/issues/1318).

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
mission of the project, and who are respected and trusted by the wider community
to uphold the guiding principles of the Foundation and keep the other Guardians
honest.

In other words; the Spec Core Team builds the spec, and the Guardians provide an
independent backstop to ensure the spec evolves in line with the Foundation's
mission.

## Guiding Principles

The guiding principles define the core philosophy of the project, and will be a
formal part of the final Articles of Association of the Matrix.org Foundation.

### Matrix Manifesto

We believe:

 * People should have full control over their own communication.

 * People should not be locked into centralised communication silos, but free to
   pick who they choose to host their communication without limiting who they
   can reach.

 * The ability to converse securely and privately is a basic human right.

 * Communication should be available to everyone as an free and open,
   unencumbered, standard and global network.

### Mission

The Matrix.org Foundation exists to act as a neutral custodian for Matrix and
nurture it as efficiently as possible as a single unfragmented standard, for the
greater benefit of the whole ecosystem; not benefiting or privileging any single
player or subset of players.

For clarity: the Matrix ecosystem is defined as anyone who uses the Matrix
protocol. This includes (non-exhaustively):

 * End-users of Matrix clients
 * Matrix client developers and testers
 * Spec developers
 * Server admins
 * Matrix packagers & maintainers
 * Companies building products or services on Matrix
 * Bridge developers
 * Bot developers
 * Widget developers
 * Server developers
 * Matrix room and community moderators
 * End-users who are using Matrix indirectly via bridges
 * External systems which are bridged into Matrix
 * Anyone using Matrix for data communications

"Greater benefit" is defined as maximising:

 * the number of end-users reachable on the open Matrix network
 * the number of regular users on the Matrix network (e.g. 30-day retained federated users)
 * the number of end-users reachable by Matrix (natively or via bridges)
 * the number of online servers in the open federation
 * the number of developers building on Matrix
 * the number of independent implementations which use Matrix
 * the quality and utility of the Matrix spec (as defined by ease and ability
   with which a developer can implement spec-compliant clients, servers, bots,
   bridges, and other integrations without needing to refer to any other
   external material)

N.B. that we consider success to be the growth of the open federated network
rather than closed deployments. For example, if WhatsApp adopted Matrix it
wouldn’t be a complete win unless they openly federated with the rest of the
Matrix network.

TODO: spell out when features should land in the spec, versus via
integration/widget or other non-core extension. e.g. should video conferencing
be in the spec itself, or done via Jitsi?

### Values

As Matrix evolves, it's critical that the Spec Core Team and Guardians are
aligned on the overall philosophy of the project, particularly in more
subjective areas.  The values we follow are:

 * Supporting the whole long-term ecosystem rather than individual stakeholder gain
 * Openness rather than proprietariness
 * Collaboration rather than competition
 * Accessibility rather than elitism
 * Transparency rather than stealth
 * Empathy rather than contrariness
 * Pragmatism rather than perfection
 * Proof rather than conjecture

Patent encumbered IP is strictly prohibited from being added to the standard.

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

We are particularly vigilant against 'trojan horse' additions to the spec -
features which only benefit particular players, or are designed to somehow
cripple or fragment the open protocol and ecosystem in favour of competitive
advantage. Commercial players are of course encouraged to build proprietary
implementations, or use custom event types, or even custom API extensions (e.g.
more efficient network transports) - but implementations must fall back to
interoperating correctly with the rest of the ecosystem.

### Spec Core Team logistics

The Spec Core Team itself will be made up of roughly 8 members + 1 project lead.
Roughly half the members are expected to be from the historical core team
(similar to Rust).

In future we may also have sub-teams (like Rust - e.g. CS/AS/Push API; SS API;
IS API; Crypto), but as a starting point we are beginning with a single core
team in the interests of not over-engineering it and scaling up elastically.

Spec Core Team members need to be able to commit to at least 1 hour a week of
availability to work on the spec and (where relevant) reference implementations.
Members of the team volunteer their time for free to work on the project.

Responsibilities include:

 * Reviewing Matrix Spec Change proposals and Spec PRs

 * Contributing to and reviewing reference implementations of Matrix Spec Change
   proposals

 * Shepherding Matrix Spec Changes on behalf of authors where needed

 * Triaging Matrix Spec issues

 * Coordinating reference implementations

 * Ensuring the code of conduct for +matrix:matrix.org community rooms is
   maintained and applied

If members are absent for more than 8 weeks without prior agreement, they will
be assumed to have left the project.

Spec Core Team members can resign whenever they want, but must notify the rest
of the team and the Guardians on doing so.

New additions to the team require 100% consent from the current team members.
Membership has to be formally proposed by someone already on the Spec Core Team.

Members can be removed from the team if >= 75% of the team agrees they are no
longer following the goals and guiding principles of the project.

Guardians act as a backstop, and can appoint or remove Spec Core Team members
(requiring a 75% consensus threshold between the Guardians) if the Spec Core
Team is unable to reach consensus or is failing to align with the Foundation's
mission.

It's suggested that one of the Spec Core Team members should also be a Guardian,
to facilitate information between the Guardians and the Spec Core Team and
represent the technical angle of the project to the other Guardians.

The project lead role acts to coordinate the team and to help tie-break in the
event of failing to get acceptance on a Matrix Spec Change. The project lead is
reviewed every 12 months and requires the confidence of 75% of the team to be
renewed. There is no maximum term for the project lead.  The lead may be removed
by the core team at any point (with 75% majority), and may resign the role at
any point (notifying the team and the Guardians).  The lead automatically resigns
the role if they resign from the Spec Core Team.

The initial Spec Core Team (and their domain areas) is:

 * Matthew Hodgson (Lead)
 * Erik Johnston (Servers)
 * Richard van der Hoff (Servers, Cryptography)
 * David Baker (Clients, IS API, Push API, Media)
 * Hubert Chathi (Cryptography, General)
 * Andrew Morgan (Servers, AS API, Spec Process)
 * Travis Ralston (Bots and Bridges & AS API, Media, acting with Dimension hat on)
 * kitsune (Clients on behalf of Community)
 * TBD

MSCs require >= 75% approval from the Spec Core Team to proceed to Final Comment
Period (see https://matrix.org/docs/spec/proposals for the rest of the MSC
process).

The above governance process for the Spec Core Team is considered as part of the
spec and is updated using the Matrix Spec Change process.  However, changes to
the governance process also require a 75% positive approval from the Guardians
(acting as a formal decision of the Foundation's Directors), in order to ensure
changes are aligned with the Foundation's mission.

## The Guardians

*This section will be used as the basis for the legal responsibilities of
Directors in the Articles of Association of the Foundation.*

The Guardians form the legal Board of Directors of The Matrix.org Foundation CIC
(Community Interest Company).  They are responsible for ensuring the Foundation
is following its guiding principles, and provide a safety mechanism if the
structure of the Spec Core Team runs into trouble.

In practice, this means that:
 * Guardians must approve changes to the Spec Core Team
 * Guardians must keep each other honest, providing a ‘checks and balances’
   mechanism between each other to ensure that all Guardians and the Spec Core
   Team act in the best interests of the protocol and ecosystem.
 * Guardians may appoint/dismiss members of the Spec Core Team who are in serious
   breach of the guiding principles. This overrides the unanimous consent
   requirement for the Spec Core Team when appointing new members.
 * Guardians must approve changes to the Guiding Principles (above)
 * Guardians are responsible for approving use of the Foundation's assets
   (e.g. redistributing donations)
 * In future, Guardians may also be responsible for ensuring staff are hired by
   the Foundation to support administrative functions
 * As well as the Spec Core Team committee, they may also oversee committees for
   other areas such as marketing Matrix.org, registering custom event types,
   or "Made for Matrix" certification.
 * It's likely a subset of Guardians will be hands-on for day-to-day
   administrative purposes, whilst the others act to keep them in balance.

Guardians are chosen typically to be independent of the commercial Matrix
ecosystem (and especially independent from New Vector), and may even not be
members of today’s Matrix community. However, they should be deeply aligned with
the mission of the project, and respected and trusted by the wider community to
uphold the guiding principles of the Foundation and keep the other Guardians
honest.

Guardians are responsible for maintaining and updating the Guiding
Principles and Articles of Association of the Foundation if/when
necessary. Changes to the Guiding Principles require a 75% majority from the
Guardians and are passed as a 'special resolution' of the board.

New Guardians may be appointed with a 75% majority by the board.

Guardians may resign at any time, with notification to the board.

Guardians may be removed due to serious breach of the guiding principles with a
75% majority of the other Guardians, or if absent from 3 consecutive board
meetings, or if they are legally disqualified from acting as a Director.

We aim to recruit roughly 5 Guardians.  The initial Guardians are:

 * Matthew Hodgson (CEO/CTO, New Vector)
 * Amandine Le Pape (COO, New Vector)
 * TBA (agreed, needs paperwork)
 * TBD
 * TBD

The intention is for Matthew & Amandine (the original founders of Matrix) to
form a minority of the Guardians, in order to ensure the neutrality of the
Foundation relative to Matthew & Amandine’s day jobs at New Vector.

Guardians volunteer their time for free to work on the project.

## The Core Team

"The Core Team" is a loose term that describes the set of people with access to
commit code to the public https://github.com/matrix-org repositories, who are
either working on matrix.org's reference implementations or the spec itself.
Commit access is decided by those responsible for the projects in question, much
like any other open source project.  Anyone is eligible for commit access if
they have proved themselves a valuable long-term contributor, upholds the
guiding principles and mission of the project and have proved themselves able to
collaborate constructively with the existing core team.

## Responsibilities for the Foundation

 * Independent legal entity to act as neutral custodian of Matrix
 * Gathering donations
 * Owns the core Matrix IP in an asset lock, which shall be transferred from New Vector:
   * Owns the matrix.org domain and branding
   * Owns the copyright of the reference implementations of Matrix (i.e. everything in https://github.com/matrix-org).
     By assigning copyright to the Foundation, it’s protected against New Vector ever being tempted to relicense it.
   * Owns the IP of the website
   * Owns the Matrix.org marketing swag (t-shirts, stickers, exhibition stands etc)
 * It's responsible for finding someone to run the Matrix.org homeserver (currently New Vector)
 * Publishing the spec
 * Responsible for tools and documentation that supports the spec
 * Responsible for ensuring reference implementations and test suite exists for the spec
 * Publishing the website (including ensuring This Week In Matrix and similar exist to promote independent projects)
 * Manages IANA-style allocations for Matrix
   * mx:// URI scheme?
   * TCP port 8448
   * .well-known URIs…?

In future:

 * contract entities to work on Matrix? (e.g. redistributing donations back to fund development)
 * manage a "Made for Matrix" certification process? (to confirm that products are actually compatible with Matrix)
 * promote Matrix (e.g. organise meetups & events & fund community activity)?

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
