.. contents:: Table of Contents
.. sectnum::

Proposals for Spec Changes to Matrix
------------------------------------


Proposal Tracking
-----------------

This is a living document generated from the list of proposals at `matrix-doc/issues <https://github.com/matrix-org/matrix-doc/issues?page=1&q=is%3Aissue+is%3Aopen>`_ on GitHub.

We use labels and some metadata in the issue text to generate this page. When adding or updating an issue, make sure you specify the current status as a label per the diagram below, these labels already exist in the matrix-doc repo.

Other metadata:

- the MSC (Matrix Spec Change) number is taken from the github issue ID. This is carried for the lifetime of the proposal, including the PR creation phase.
- Please use the github issue title to set the title.
-  The created date is taken from the github issue, but can be overriden by adding a "Date: yyyy-mm-dd" line in the body of the issue text.
- Updated Date is taken from github.
- Author is the creator of the github issue, but can be overriden by adding a "Author: @username" line in the body of the issue text. Please make sure @username is a github user (include the @!)
- Shepherd is set by adding a "Shepherd: @username" line in the body of the issue text. Again, make sure this is a real Github user.


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


