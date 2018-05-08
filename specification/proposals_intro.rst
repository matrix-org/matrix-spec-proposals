.. contents:: Table of Contents
.. sectnum::

Proposals for Spec Changes to Matrix
------------------------------------


Proposal Tracking
-----------------

This is a living document generated from the list of proposals at `matrix-doc/issues <https://github.com/matrix-org/matrix-doc/issues?page=1&q=is%3Aissue+is%3Aopen>`_ on GitHub.

We use labels and some metadata in the issue text to generate this page. When adding or updating an issue, make sure you specify the current status as a label:

- WIP
- Ready for review
- In review
- Merged
- Rejected
- Stalled

::

      +----------+     +-------------------+     +-----------+     +---------------+
      |          |     |                   |     |           |     |               |
      | Proposal +----->      Proposal     +-----> Proposal  +----->   Proposal    +------+
      |   WIP    |     |  Ready for Review |     | In Review |     | Passed Review |      |
      |          |     |                   |     |           |     |               |      |
      +----------+     +-------------------+     +-----------+     +---------------+      |
                                                                                          |
  +---------------------------------------------------------------------------------------+
  |
  |  +---------------------+     +-----------+                      +-----------+
  |  |                     |     |           |                      |-----------|
  +-->       Spec          +----->  Spec PR  |                      ||         ||
     | PR Ready for Review |     | In Review +-----------------------> Merged  ||
     |                     |     |           |                      ||         ||
     +---------------------+     +-+-------+-+                      |-----------|
                                   |       |                        +-----------+
                           +-------+       +--------+
                           |                        |
                     +-----v----+             +-----v----+
                     |          |             |          |
                     | Stalled  |             | Rejected |
                     |          |             |          |
                     +----------+             +----------+
