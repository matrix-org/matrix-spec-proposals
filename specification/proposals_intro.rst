.. title:: Proposals for Spec Changes to Matrix

.. contents:: Table of Contents
.. sectnum::

Proposals for Spec Changes to Matrix
------------------------------------

If you are interested in submitting a change to the Matrix Specification,
please take note of the following guidelines.

All changes to Specification content require a formal proposal process. This
involves writing a proposal, having it reviewed by everyone, having the
proposal being accepted, then actually having your ideas implemented as
committed changes to the `Specification repository
<https://github.com/matrix-org/matrix-doc>`_.

Meet the `members of the Core Team
<https://github.com/orgs/matrix-org/teams/spec-core-team/members>`_, a group of
individuals tasked with ensuring the spec process is as smooth and painless as
possible. Members of the Core Team will do their best to participate in
discussion, summarise when things become long-winded, and generally try to act
towards the benefit of everyone. As a majority, team members have the ability
to change the state of a proposal, and individually have the final say in
proposal discussion.

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
    <https://github.com/matrix-org/matrix-doc/blob/master/proposals/proposals_template.md>`_
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

- Gather feedback as widely as possible from everyone.

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
    assigned to help guide the proposal through this process. A shepherd is
    typically a neutral party from the Core Team or an experienced member of
    the community. Having a shepherd is not a requirement for proposal
    acceptance.

  
- Members of the Core Team and community will review and discuss the PR in the
  comments and in relevant rooms on Matrix. Discussion outside of GitHub should
  be summarised in a comment on the PR.
- At some point a member of the Core Team will propose a motion for a final
  comment period (FCP) with a *disposition* of merge, close or postpone. This
  is usually preceded with a comment summarising the current state of the
  discussion, along with reasoning for the motion.
- A concern can be raised by a Core Team member at any time, which will block
  the FCP from beginning. An FCP will only be begin when a **majority** of core
  team members agree on its outcome, and all existing concerns have been
  resolved.
- The FCP will then begin and last for 5 days, giving anyone else some time to
  speak up before it concludes. On its conclusion, the disposition of the FCP
  will be carried out. If sufficient reasoning against the disposition is is
  raised, the FCP can be cancelled and the MSC will continue to evolve
  accordingly.
- Once the proposal has been accepted and merged, it is time to submit the
  actual change to the Specification that your proposal reasoned about. This is
  known as a spec PR. However in order for the spec PR to be accepted, an
  implementation **must** be shown to prove that it works well in practice. A
  link to the implementation should be included in the PR description. In
  addition, any significant unforeseen changes to the original idea found
  during this process will warrant another MSC.

  - Please sign off the spec PR as per the `CONTRIBUTING.rst 
  <https://github.com/matrix-org/matrix-doc/blob/master/CONTRIBUTING.rst>`_
  guidelines.

- Your PR will then be reviewed and hopefully merged on the grounds it is
  implemented sufficiently. If so, then give yourself a pat on the back knowing
  you've contributed to the Matrix protocol for the benefit of users and
  developers alike :)

Please also read the separate document on `proposal etiquette <proposal_etiquette.html>`_.

The process for handling proposals is shown visually in the following diagram.
Note that the lifetime of a proposal is tracked through the corresponding
labels for each stage in the `matrix-doc issue tracker
<https://github.com/matrix-org/matrix-doc/issues>`_.

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
  |    Created and    |    |  |  |                 |  |  
  |     In Review     |    |  |  +--------+--------+  |   
  |                   |    |  |           |           |
  +---------+---------+    |  |           v           |   
            |              |  |     +-----------+     |   
            v              |  |     |           |     |   
 +----------------------+  |  |     |  Spec PR  |     |   
 |                      |  |  |     |  Merged!  |     |   
 | Final Comment Period |  |  |     |           |     |
 |                      |  |  |     +-----------+     |
 +----------+-----------+  |  |                       |
            |              |  |                       |
            v              |  |                       |
     +-------------+       |  |                       |
     |             |       |  |                       |
     | Proposal PR |       |  |                       |
     |   Merged!   |       |  |                       |
     |             |       |  |                       |
     +------|------+       |  |                       |
            |              |  |                       |
            +-----------------+                       |
                           |                          |
                           +                          +

Lifetime States
---------------

===============================  =============================  ====================================
Name                             GitHub Label                   Description
===============================  =============================  ====================================
Proposal Drafting and Feedback   N/A                            A proposal document which is still work-in-progress but is being shared to incorporate feedback
Proposal In Review               proposal-in-review             A proposal document which is now ready and waiting for review by the Core Team and community
Proposal Final Comment Period    proposal-final-comment-period  A proposal document which has reached final comment period either for merge, closure or postponement
Proposal Merged/Spec PR Missing  proposal-passed-review         A proposal document which has passed review. Waiting for a PR against the Spec
Spec PR In Review                spec-pr                        A proposal that has been PR'd against the spec and is currently under review
Spec PR Merged                   merged (on proposal pr)        A proposal with a sufficient working implementation and whose Spec PR has been merged!
Postponed                        proposal-postponed             A proposal that is temporarily blocked or a feature that may not be useful currently but perhaps 
                                                                sometime in the future
Closed                           proposal-closed                A proposal which has been reviewed and deemed unsuitable for acceptance
===============================  =============================  ====================================


Proposal Tracking
-----------------

This is a living document generated from the list of proposals at
`matrix-doc/issues <https://github.com/matrix-org/matrix-doc/issues>`_ on
GitHub.

We use labels and some metadata in MSC PR descriptions to generate this page.
Labels are assigned by the Core Team whilst triaging the issues based on those
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
