.. raw:: html

 %proposalscssinjection%

.. title:: Proposals for Spec Changes to Matrix

.. contents:: Table of Contents
.. sectnum::

Proposals for Spec Changes to Matrix
------------------------------------

If you are interested in submitting a change to the Matrix Specification,
please take note of the following guidelines.

Most changes to the Specification require a formal proposal. Bug fixes, typos,
and clarifications to existing behaviour do not need proposals - see the
`contributing guide <https://github.com/matrix-org/matrix-doc/blob/master/CONTRIBUTING.rst>`_
for more information on what does and does not need a proposal.

The proposal process involves some technical writing, having it reviewed by
everyone, having the proposal being accepted, then actually having your ideas
implemented as committed changes to the `Specification repository
<https://github.com/matrix-org/matrix-doc>`_.

Meet the `members of the Core Team
<https://matrix.org/foundation>`_, a group of
individuals tasked with ensuring the spec process is as smooth and painless as
possible. Members of the Spec Core Team will do their best to participate in
discussion, summarise when things become long-winded, and generally try to act
towards the benefit of everyone. As a majority, team members have the ability
to change the state of a proposal, and individually have the final say in
proposal discussion.

Guiding Principles
------------------

Proposals **must** act to the greater benefit of the entire Matrix ecosystem,
rather than benefiting or privileging any single player or subset of players -
and must not contain any patent encumbered intellectual property. Members of
the Core Team pledge to act as a neutral custodian for Matrix on behalf of the
whole ecosystem.

For clarity: the Matrix ecosystem is anyone who uses the Matrix protocol. That
includes client users, server admins, client developers, bot developers,
bridge and application service developers, users and admins who are indirectly
using Matrix via 3rd party networks which happen to be bridged, server developers,
room moderators and admins, companies/projects building products or services on
Matrix, spec contributors, translators, and those who created it in
the first place.

"Greater benefit" could include maximising:

* the number of end-users reachable on the open Matrix network
* the number of regular users on the Matrix network (e.g. 30-day retained
  federated users)
* the number of online servers in the open federation
* the number of developers building on Matrix
* the number of independent implementations which use Matrix
* the number of bridged end-users reachable on the open Matrix network
* the signal-to-noise ratio of the content on the open Matrix network (i.e. minimising spam)
* the ability for users to discover content on their terms (empowering them to select what to see and what not to see)
* the quality and utility of the Matrix spec (as defined by ease and ability
  with which a developer can implement spec-compliant clients, servers, bots,
  bridges, and other integrations without needing to refer to any other
  external material)

In addition, proposal authors are expected to uphold the following values in
their proposed changes to the Matrix protocol:

* Supporting the whole long-term ecosystem rather than individual stakeholder gain
* Openness rather than proprietary lock-in
* Interoperability rather than fragmentation
* Cross-platform rather than platform-specific
* Collaboration rather than competition
* Accessibility rather than elitism
* Transparency rather than stealth
* Empathy rather than contrariness
* Pragmatism rather than perfection
* Proof rather than conjecture

Please `see MSC1779 <https://github.com/matrix-org/matrix-doc/blob/master/proposals/1779-open-governance.md>`_
for full details of the project's Guiding Principles.

Technical notes
---------------

Proposals **must** develop Matrix as a layered protocol: with new features
building on layers of shared abstractions rather than introducing tight vertical
coupling within the stack.  This ensures that new features can evolve rapidly by
building on existing layers and swapping out old features without impacting the
rest of the stack or requiring substantial upgrades to the whole ecosystem.
This is critical for Matrix to rapidly evolve and compete effectively with
centralised systems, despite being a federated protocol.

For instance, new features should be implemented using the highest layer
abstractions possible (e.g. new event types, which layer on top of the existing
room semantics, and so don't even require any API changes). Failing that, the
next recourse would be backwards-compatible changes to the next layer down (e.g.
room APIs); failing that, considering changes to the format of events or the
DAG; etc.  It would be a very unusual feature which doesn't build on the
existing infrastructure provided by the spec and instead created new primitives
or low level APIs.

Backwards compatibility is very important for Matrix, but not at the expense of
hindering the protocol's evolution.  Backwards incompatible changes to endpoints
are allowed when no other alternative exists, and must be versioned under a new
major release of the API.  Backwards incompatible changes to the room algorithm
are also allowed when no other alternative exists, and must be versioned under a
new version of the room algorithm.

There is sometimes a dilemma over where to include higher level features: for
instance, should video conferencing be formalised in the spec, or should it be
implemented via widgets? Should reputation systems be specified? Should search
engine behaviour be specified?

There is no universal answer to this, but the following guidelines should be
applied:

1. If the feature would benefit the whole Matrix ecosystem and is aligned with
   the guiding principles above, then it should be supported by the spec.
2. If the spec already makes the feature possible without changing any of the
   implementations and spec, then it may not need to be added to the spec.
3. However, if the best user experience for a feature does require custom
   implementation behaviour then the behaviour should be defined in the spec
   such that all implementations may implement it.
4. However, the spec must never add dependencies on unspecified/nonstandardised
   3rd party behaviour.

As a worked example:

1. Video conferencing is clearly a feature which would benefit
   the whole ecosystem, and so the spec should find a way to make it happen.
2. Video conferencing can be achieved by widgets without requiring any
   compulsory changes to changes to clients nor servers to work, and so could be
   omitted from the spec.
3. A better experience could be achieved by embedding Jitsi natively into clients
   rather than using a widget...
4. ...except that would add a dependency on unspecified/nonstandardised 3rd party
   behaviour, so must not be added to the spec.

Therefore, our two options in the specific case of video conferencing are
either to spec SFU conferencing semantics for WebRTC (or refer to an existing spec
for doing so), or to keep it as a widget-based approach (optionally with widget
extensions specific for more deeply integrating video conferencing use cases).

As an alternative example: it's very unlikely that "how to visualise Magnetic
Resonsance Imaging data over Matrix" would ever be added to the Matrix spec
(other than perhaps a custom event type in a wider standardised Matrix event
registry) given that the spec's existing primitives of file transfer and
extensible events (MSC1767) give excellent tools for transfering and
visualising arbitrary rich data.

Supporting public search engines are likely to not require custom spec features
(other than possibly better bulk access APIs), given they can be implemented as
clients using the existing CS API.  An exception could be API features required
by decentralised search infrastructure (avoiding centralisation of power by
a centralised search engine).

Features such as reactions, threaded messages, editable messages,
spam/abuse/content filtering (and reputation systems), are all features which
would clearly benefit the whole Matrix ecosystem, and cannot be implemented in an
interoperable way using the current spec; so they necessitate a spec change.

Process
-------

The process for submitting a Matrix Spec Change (MSC) Proposal in detail is as
follows:

- Create a first draft of your proposal using `GitHub-flavored markdown
  <https://help.github.com/articles/basic-writing-and-formatting-syntax/>`_

  - In the document, clearly state the problem being solved, and the possible
    solutions being proposed for solving it and their respective trade-offs.
  - Proposal documents are intended to be as lightweight and flexible as the
    author desires; there is no formal template; the intention is to iterate
    as quickly as possible to get to a good design.
  - However, a `template with suggested headers
    <https://github.com/matrix-org/matrix-doc/blob/master/proposals/0000-proposal-template.md>`_
    is available to get you started if necessary.
  - Take care in creating your proposal. Specify your intended changes, and
    give reasoning to back them up. Changes without justification will likely
    be poorly received by the community.

- Fork and make a PR to the `matrix-doc
  <https://github.com/matrix-org/matrix-doc>`_ repository. The ID of your PR
  will become the MSC ID for the lifetime of your proposal.

  - The proposal must live in the ``proposals/`` directory with a filename that
    follows the format ``1234-my-new-proposal.md`` where ``1234`` is the MSC
    ID.
  - Your PR description must include a link to the rendered markdown document
    and a summary of the proposal.
  - It is often very helpful to link any related MSCs or `matrix-doc issues
    <https://github.com/matrix-org/matrix-doc/issues>`_ to give context
    for the proposal.
  - Additionally, please be sure to sign off your proposal PR as per the
    guidelines listed on `CONTRIBUTING.rst
    <https://github.com/matrix-org/matrix-doc/blob/master/CONTRIBUTING.rst>`_.

- Gather feedback as widely as possible.

  - The aim is to get maximum consensus towards an optimal solution. Sometimes
    trade-offs are required to meet this goal. Decisions should be made to the
    benefit of all major use cases.
  - A good place to ask for feedback on a specific proposal is
    `#matrix-spec:matrix.org <https://matrix.to/#/#matrix-spec:matrix.org>`_.
    If preferred, an alternative room can be created and advertised in
    #matrix-spec:matrix.org. Please also link to the room in your PR
    description.
  - For additional discussion areas, know that that #matrix-dev:matrix.org is
    for developers using existing Matrix APIs, #matrix:matrix.org is for users
    trying to run Matrix apps (clients & servers) and
    #matrix-architecture:matrix.org is for cross-cutting discussion of matrix's
    architectural design.
  - The point of the spec proposal process is to be collaborative rather than
    competitive, and to try to solve the problem in question with the optimal
    set of trade-offs. The author should neutrally gather the various
    viewpoints and get consensus, but this can sometimes be time-consuming (or
    the author may be biased), in which case an impartial 'shepherd' can be
    assigned to help guide the proposal through this process instead. A shepherd is
    typically a neutral party from the Spec Core Team or an experienced member of
    the community. There is no formal process for assignment. Simply ask for a
    shepherd to help get your proposal through and one will be assigned based
    on availability. Having a shepherd is not a requirement for proposal
    acceptance.

- Members of the Spec Core Team and community will review and discuss the PR in the
  comments and in relevant rooms on Matrix. Discussion outside of GitHub should
  be summarised in a comment on the PR.
- When a member of the Spec Core Team believes that no new discussion points are
  being made, they will propose a motion for a final comment period (FCP),
  along with a *disposition* of either merge, close or postpone. This FCP is
  provided to allow a short period of time for any invested party to provide a
  final objection before a major decision is made. If sufficient reasoning is
  given, an FCP can be cancelled. It is often preceded by a comment summarising
  the current state of the discussion, along with reasoning for its occurrence.
- A concern can be raised by a Spec Core Team member at any time, which will block
  an FCP from beginning. An FCP will only begin when 75% of the members of the
  Spec Core Team team agree on its outcome, and all existing concerns have been
  resolved.
- The FCP will then begin and last for 5 days, giving anyone else some time to
  speak up before it concludes. On its conclusion, the disposition of the FCP
  will be carried out. If sufficient reasoning against the disposition is
  raised, the FCP can be cancelled and the MSC will continue to evolve
  accordingly.
- Once the proposal has been accepted and merged, it is time to submit the
  actual change to the Specification that your proposal reasoned about. This is
  known as a spec PR. However in order for the spec PR to be accepted, an
  implementation **must** be shown to prove that it works well in practice. A
  link to the implementation should be included in the PR description. In
  addition, any significant unforeseen changes to the original idea found
  during this process will warrant another MSC. Any minor, non-fundamental
  changes are allowed but **must** be documented in the original proposal
  document. This ensures that someone reading a proposal in the future doesn't
  assume old information wasn't merged into the spec.

  - Similar to the proposal PR, please sign off the spec PR as per the
    guidelines on `CONTRIBUTING.rst
    <https://github.com/matrix-org/matrix-doc/blob/master/CONTRIBUTING.rst>`_.

- Your PR will then be reviewed and hopefully merged on the grounds it is
  implemented sufficiently. If so, then give yourself a pat on the back knowing
  you've contributed to the Matrix protocol for the benefit of users and
  developers alike :)

The process for handling proposals is shown visually in the following diagram.
Note that the lifetime of a proposal is tracked through the corresponding
labels for each stage on the `matrix-doc
<https://github.com/matrix-org/matrix-doc>`_ issue and pull request trackers.

::

                           +                          +
         Proposals         |          Spec PRs        |  Additional States
         +-------+         |          +------+        |  +---------------+
                           |                          |
 +----------------------+  |         +---------+      |    +-----------+
 |                      |  |         |         |      |    |           |
 |      Proposal        |  |  +------= Spec PR |      |    | Postponed |
 | Drafting and Initial |  |  |      | Missing |      |    |           |
 |  Feedback Gathering  |  |  |      |         |      |    +-----------+
 |                      |  |  |      +----+----+      |
 +----------+-----------+  |  |           |           |    +----------+
            |              |  |           v           |    |          |
            v              |  |  +-----------------+  |    |  Closed  |
  +-------------------+    |  |  |                 |  |    |          |
  |                   |    |  |  | Spec PR Created |  |    +----------+
  |    Proposal PR    |    |  |  |  and In Review  |  |
  |     In Review     |    |  |  |                 |  |
  |                   |    |  |  +--------+--------+  |
  +---------+---------+    |  |           |           |
            |              |  |           v           |
            v              |  |     +-----------+     |
 +----------------------+  |  |     |           |     |
 |                      |  |  |     |  Spec PR  |     |
 |    Proposed Final    |  |  |     |  Merged!  |     |
 |    Comment Period    |  |  |     |           |     |
 |                      |  |  |     +-----------+     |
 +----------+-----------+  |  |                       |
            |              |  |                       |
            v              |  |                       |
 +----------------------+  |  |                       |
 |                      |  |  |                       |
 | Final Comment Period |  |  |                       |
 |                      |  |  |                       |
 +----------+-----------+  |  |                       |
            |              |  |                       |
            v              |  |                       |
 +----------------------+  |  |                       |
 |                      |  |  |                       |
 | Final Comment Period |  |  |                       |
 |       Complete       |  |  |                       |
 |                      |  |  |                       |
 +----------+-----------+  |  |                       |
            |              |  |                       |
            +-----------------+                       |
                           |                          |
                           +                          +

Lifetime States
---------------

**Note:** All labels are to be placed on the proposal PR.

===============================  =============================  ====================================
Name                             GitHub Label                   Description
===============================  =============================  ====================================
Proposal Drafting and Feedback   N/A                            A proposal document which is still work-in-progress but is being shared to incorporate feedback. Please prefix your proposal's title with ``[WIP]`` to make it easier for reviewers to skim their notifications list.
Proposal In Review               proposal-in-review             A proposal document which is now ready and waiting for review by the Spec Core Team and community
Proposed Final Comment Period    proposed-final-comment-period  Currently awaiting signoff of a 75% majority of team members in order to enter the final comment period
Final Comment Period             final-comment-period           A proposal document which has reached final comment period either for merge, closure or postponement
Final Commment Period Complete   finished-final-comment-period  The final comment period has been completed. Waiting for a demonstration implementation
Spec PR Missing                  spec-pr-missing                The proposal has been agreed, and proven with a demonstration implementation. Waiting for a PR against the Spec
Spec PR In Review                spec-pr-in-review              The spec PR has been written, and is currently under review
Spec PR Merged                   merged                         A proposal with a sufficient working implementation and whose Spec PR has been merged!
Postponed                        proposal-postponed             A proposal that is temporarily blocked or a feature that may not be useful currently but perhaps
                                                                sometime in the future
Closed                           proposal-closed                A proposal which has been reviewed and deemed unsuitable for acceptance
Obsolete                         obsolete                       A proposal which has been made obsolete by another proposal or decision elsewhere.
===============================  =============================  ====================================

Categories
----------

We use category labels on MSCs to place them into a track of work. The spec core team
decides which of the tracks they are focusing on for the next while and generally makes
an effort to pull MSCs out of that category when possible.

The current categories are:

============ ================= ======================================
Name         Github Label      Description
============ ================= ======================================
Core         kind:core         Important for the protocol's success.
Feature      kind:feature      Nice to have additions to the spec.
Maintenance  kind:maintenance  Fixes or clarifies existing spec.
============ ================= ======================================

Some examples of core MSCs would be aggregations, cross-signing, and groups/communities.
These are the sorts of things that if not implemented could cause the protocol to
fail or become second-class. Features would be areas like enhanced media APIs,
new transports, and bookmarks in comparison. Finally, maintenance MSCs would include
improving error codes, clarifying what is required of an API, and adding properties
to an API which makes it easier to use.

The spec core team assigns a category to each MSC based on the descriptions above.
This can mean that new MSCs get categorized into an area the team isn't focused on,
though that can always change as priorities evolve. We still encourage that MSCs be
opened, even if not the focus for the time being, as they can still make progress and
even be merged without the spec core team focusing on them specifically.

Proposal Tracking
-----------------

This is a living document generated from the list of proposals on the issue and
pull request trackers of the `matrix-doc
<https://github.com/matrix-org/matrix-doc>`_ repo.

We use labels and some metadata in MSC PR descriptions to generate this page.
Labels are assigned by the Spec Core Team whilst triaging the proposals based on those
which exist in the `matrix-doc <https://github.com/matrix-org/matrix-doc>`_
repo already.

It is worth mentioning that a previous version of the MSC process used a
mixture of GitHub issues and PRs, leading to some MSC numbers deriving from
GitHub issue IDs instead. A useful feature of GitHub is that it does
automatically resolve to an issue, if an issue ID is placed in a pull URL. This
means that https://github.com/matrix-org/matrix-doc/pull/$MSCID will correctly
resolve to the desired MSC, whether it started as an issue or a PR.

Other metadata:

- The MSC number is taken from the GitHub Pull Request ID. This is carried for
  the lifetime of the proposal. These IDs do not necessary represent a
  chronological order.
- The GitHub PR title will act as the MSC's title.
- Please link to the spec PR (if any) by adding a "PRs: #1234" line in the
  issue description.
- The creation date is taken from the GitHub PR, but can be overridden by
  adding a "Date: yyyy-mm-dd" line in the PR description.
- Updated Date is taken from GitHub.
- Author is the creator of the MSC PR, but can be overridden by adding a
  "Author: @username" line in the body of the issue description. Please make
  sure @username is a GitHub user (include the @!)
- A shepherd can be assigned by adding a "Shepherd: @username" line in the
  issue description. Again, make sure this is a real GitHub user.
