.. contents:: Table of Contents
.. sectnum::

Proposals for Spec Changes to Matrix
------------------------------------

The process for submitting a Matrix Spec Change (MSC) Proposal is as follows:

- produce a publicly-accessible proposal describing your change:

  - Please use Google Docs, or an equivalent system capable of collaborative
    editing, with versioned history, suggestions ('track changes'), threaded
    comments, and good mobile support.  Please ensure the document is
    world-commentable or -editable.
  - We do not use Github issues (or Etherpad) for the design process of the
    proposal, as the document review/commenting capabilities aren't good
    enough.
  - We also don't jump straight to PRing against the spec itself, as it's much
    faster to iterate on a proposal in freeform document form than in the
    terse and formal structure of the spec.
  - In the proposal, please clearly state the problem being solved, and the
    possible solutions being proposed for solving it and their respective
    trade-offs.
  - Proposal documents are intended to be as lightweight and flexible as the 
    author desires; there is no formal template; the intention is to iterate
    as quickly as possible to get to a good design.
  - A `template with suggested headers
    <https://docs.google.com/document/d/1CoLCPTcRFvD4PqjvbUl3ZIWgGLpmRNbqxsT2Tu7lCzI/>`_
    is available.

- make a new issue at https://github.com/matrix-org/matrix-doc/issues (or
  modify an existing one), whose description should list the metadata as per
  below.
- Gather feedback as widely as possible from the community and core team on
  the proposal.

  - The aim is to get maximum consensus on the trade-offs chosen to get an
    optimal solution.
  - A good place to ask for feedback on a specific proposal is
    `#matrix-spec:matrix.org <https://matrix.to/#/#matrix-spec:matrix.org>`_.
    However, authors/shepherds are welcome to use an alternative room if they
    prefer - please advertise it in #matrix-spec:matrix.org though and link
    to it on the github issue.  N.B. that #matrix-dev:matrix.org is for
    developers using existing Matrix APIs, #matrix:matrix.org is for users
    trying to run matrix apps (clients & servers);
    #matrix-architecture:matrix.org is for cross-cutting discussion of
    Matrix's architectural design.
  - The point of the spec proposal process is to be collaborative rather than
    competitive, and to try to solve the problem in question with the optimal
    set of trade-offs.  Ideally the author would neutrally gather the various
    viewpoints and get consensus, but this can sometimes be time-consuming (or
    the author may be biased), in which case an impartial 'shepherd' can be
    assigned to help guide the proposal through this process.  A shepherd is
    typically a neutral party from the core team or an experienced member of
    the community.
  
- Once the proposal has sufficient consensus and passed review, you **must**
  show an implementation to prove that it works well in practice, before a
  spec PR will be accepted.  Iterate on the proposal if needed.
- Finally, please make a new spec PR which includes the changes as
  implemented against
  https://github.com/matrix-org/matrix-doc/tree/master/specification.  This
  will then be reviewed and hopefully merged!  Please sign off the spec PR as
  per the `CONTRIBUTING.rst
  <https://github.com/matrix-org/matrix-doc/blob/master/CONTRIBUTING.rst>`_
  guidelines.

Final decisions on review are made by the Matrix core team
(+matrix:matrix.org), acting on behalf of the whole Matrix community.

Proposals **must** act to the greater benefit of the entire Matrix ecosystem,
rather than benefiting or privileging any single player or subset of players
- and must not contain any patent encumbered IP.  The Matrix core team pledges
to act as a neutral custodian for Matrix on behalf of the whole ecosystem,
just as it has since Matrix's inception in May 2014.

For clarity: the Matrix ecosystem is anyone who uses the Matrix protocol. That
includes client users, server admins, client developers, bot developers,
bridge and AS developers, users and admins who are indirectly using Matrix via
3rd party networks which happen to be bridged, server developers, room
moderators and admins, companies/projects building products or services on
Matrix, spec contributors, translators, and the core team who created it in
the first place.

"Greater benefit" could include maximising:

 * the number of end-users reachable on the open Matrix network.
 * the number of regular users on the Matrix network (e.g. 30-day retained
   federated users)
 * the number of online servers in the open federation.
 * the number of developers building on Matrix.
 * the number of independent implementations which use Matrix
 * the quality and utility of the Matrix spec.

The guiding principles of the overall project are being worked on as part of
the upcoming governance proposal, but could be something like:

 * Supporting the whole long-term ecosystem rather than individual stakeholder gain
 * Openness rather than proprietariness
 * Collaboration rather than competition
 * Accessibility rather than elitism
 * Transparency rather than stealth
 * Empathy rather than contrariness
 * Pragmatism rather than perfection
 * Proof rather than conjecture

The above directions are intended to be simple and pragmatic rather than
exhaustive, and aim to provide guidelines until we have a formal spec
governance process in place that covers the whole Matrix community.  In order
to get Matrix out of beta as quickly as possible, as of May 2018 we are
prioritising spec and reference implementation development over writing formal
governance, but a formal governance document will follow as rapidly as
possible.

The process for handling proposals is described in the following diagram. Note
that the lifetime of a proposal is tracked through the corresponding labels for
each stage in the `matrix-doc issue tracker
<https://github.com/matrix-org/matrix-doc/issues>`_.

::

                         +                            +
       Proposals         |          Spec PRs          |   Other States
       +-------+         |          +------+          |   +----------+
                         |                            |
                         |                            |
      +----------+       |         +---------+        |    +---------+
      |          |       |         |         |        |    |         |
      | Proposal |       |  +------> Spec PR |        |    | Blocked |
      |   WIP    |       |  |      | Missing |        |    |         |
      |          |       |  |      |         |        |    +---------+
      +----+-----+       |  |      +----+----+        |
           |             |  |           |             |
           |             |  |           |             |  +-----------+
  +--------v----------+  |  |           |             |  |           |
  |                   |  |  | +---------v--------+    |  | Abandoned |
  |      Proposal     |  |  | |                  |    |  |           |
  |  Ready for Review |  |  | |     Spec PR      |    |  +-----------+
  |                   |  |  | | Ready for Review |    |
  +----------+--------+  |  | |                  |    |  +-----------+
             |           |  | +---------+--------+    |  |           |
             |           |  |           |             |  | Obsolete  |
      +------v----+      |  |           |             |  |           |
      |           |      |  |     +-----v-----+       |  +-----------+
      | Proposal  |      |  |     |           |       |
      | In Review |      |  |     |  Spec PR  |       |
      |           |      |  |     | In Review |       |   +----------+
      +----+------+      |  |     |           |       |   |          |
           |             |  |     +-----+-----+       |   | Rejected |
           |             |  |           |             |   |          |
    +------v--------+    |  |           |             |   +----------+
    |               |    |  |           |             |
    |   Proposal    |    |  |      +----v----+        |
    | Passed Review |    |  |      |         |        |
    |               |    |  |      | Merged! |        |
    +-------+-------+    |  |      |         |        |
            |            |  |      +---------+        |
            |            |  |                         |
            +---------------+                         |
                         |                            |
                         +                            +

Lifetime States
---------------

=========================== =======================================================
Proposal WIP                A proposal document which is still work-in-progress but is being shared to incorporate feedback
Proposal Ready for Review   A proposal document which is now ready and waiting for review by the core team and community
Proposal In Review          A proposal document which is currently in review
Proposal Passed Review      A proposal document which has passed review as worth implementing and then being added to the spec
Spec PR Missing             A proposal which has been implemented and has been used in the wild for a few months but hasn't yet been added to the spec
Spec PR Ready for Review    A proposal which has been PR'd against the spec and is awaiting review
Spec PR In Review           A proposal which has been PR'd against the spec and is in review
Merged                      A proposal whose PR has merged into the spec!
Blocked                     A proposal which is temporarily blocked on some external factor (e.g. being blocked on another proposal first being approved)
Abandoned                   A proposal where the author/shepherd has not been responsive for a few months
Obsolete                    A proposal which has been overtaken by other proposals
Rejected                    A proposal which is not going to be incorporated into Matrix
=========================== =======================================================


Proposal Tracking
-----------------

This is a living document generated from the list of proposals at
`matrix-doc/issues <https://github.com/matrix-org/matrix-doc/issues>`_ on
GitHub.

We use labels and some metadata in the issues' descriptions to generate this
page.  Labels are assigned by the core team whilst triaging the issues based
on those which exist in the matrix-doc repo already.

Other metadata:

- the MSC (Matrix Spec Change) number is taken from the github issue ID. This
  is carried for the lifetime of the proposal, including the PR creation
  phase. N.B. They are not in chronological order!
- Please use the github issue title to set the title.
- Please link to the proposal document by adding a "Documentation: <url>" line
  in the issue description.
- Please link to the spec PR (if any) by adding a "PRs: #1234" line in the
  issue description.
- The creation date is taken from the github issue, but can be overriden by
  adding a "Date: yyyy-mm-dd" line in the issue description.
- Updated Date is taken from github.
- Author is the creator of the github issue, but can be overriden by adding a
  "Author: @username" line in the body of the issue description. Please make
  sure @username is a github user (include the @!)
- A shepherd can be assigned by adding a "Shepherd: @username" line in the
  issue description. Again, make sure this is a real Github user.
