.. contents:: Table of Contents
.. sectnum::

Proposals for Spec Changes to Matrix
------------------------------------

The process for submitting a Matrix Spec Change (MSC) Proposal is as follows:

- produce a publicly-accessible proposal describing your change:
  - Please use Google Docs, or an equivalent system capable of collaborative editing, with versioned history and threaded comments.
  - We do not use Github issues (or Etherpad) for the design process of the proposal, as the document review/commenting capabilities aren't good enough.
  - We also don't jump straight to PRing against the spec itself, as it's much faster to iterate on a proposal in freeform document form than in the terse and formal structure of the spec.
  - In the proposal, please clearly state the problem being solved, and the possible solutions being proposed for solving it and their respective trade-offs.
  - Proposal documents are intended to be as lightweight and flexible as the author desires; there is no formal template; the intention is to iterate as quickly as possible to get to a good design.
- make a new issue at https://github.com/matrix-org/matrix-doc/issues (or modify an existing one), whose description should list the metadata as per below.
- Gather feedback as widely as possible from the community and core team on the proposal.
  - The aim is to get maximum consensus on the trade-offs chosen to get an optimal solution.
  - Iterating on the proposal and gathering consensus can sometimes be time-consuming; an impartial 'shepherd' can be assigned to help guide the proposal through this process.
- Once the proposal has sufficient consensus and passed review, you **must** show an implementation to prove that it works well in practice, before before a spec PR will be accepted.  Iterate on the proposal if needed.
- Finally, please make a new spec PR which includes the proposed changes against https://github.com/matrix-org/matrix-doc/tree/master/specification.  This will then be reviewed and hopefully merged!

Final decisions on review are made by the +matrix:matrix.org community (i.e. the core team), acting on behalf of the whole Matrix community.

The process for handling proposals is described in the following diagram. Note that the lifetime of a proposal is tracked through the corresponding labels for each stage in the `matrix-doc issue tracker <https://github.com/matrix-org/matrix-doc/issues>`_.

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
Spec PR Missing             A proposal which has been implemented and is being used in the wild but hasn't yet been added to the spec
Spec PR Ready for Review    A proposal which has been PR'd against the spec and is awaiting review
Spec PR In Review           A proposal which has been PR'd against the spec and is in review
Merged                      A proposal whose PR has merged into the spec!
Blocked                     A proposal which is temporarily blocked on some external factor (e.g. being blocked on another proposal first being approved)
Abandoned                   A proposal where the author/shepherd is not responsive
Obsolete                    A proposal which has been overtaken by other proposals
Rejected                    A proposal which is not going to be incorporated into Matrix
=========================== =======================================================


Proposal Tracking
-----------------

This is a living document generated from the list of proposals at `matrix-doc/issues <https://github.com/matrix-org/matrix-doc/issues>`_ on GitHub.

We use labels and some metadata in the issue's description to generate this page.  Labels are assigned by the core team whilst triaging the issues based on those which exist in the matrix-doc repo already.

Other metadata:

- the MSC (Matrix Spec Change) number is taken from the github issue ID. This is carried for the lifetime of the proposal, including the PR creation phase.  N.B. They are not in chronological order!
- Please use the github issue title to set the title.
- Please link to the proposal document by adding a "Documentation: <url>" line in the issue description.
- The creation date is taken from the github issue, but can be overriden by adding a "Date: yyyy-mm-dd" line in the issue description.
- Updated Date is taken from github.
- Author is the creator of the github issue, but can be overriden by adding a "Author: @username" line in the body of the issue description. Please make sure @username is a github user (include the @!)
- A shepherd can be assigned by adding a "Shepherd: @username" line in the issue description. Again, make sure this is a real Github user.
