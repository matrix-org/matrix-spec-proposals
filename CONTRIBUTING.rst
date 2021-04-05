Contributing to matrix-doc
==========================

Everyone is welcome to contribute to the Matrix specification!

Please ensure that you sign off your contributions. See `Sign off`_ below.

Code style
----------

The documentation style is described at
https://github.com/matrix-org/matrix-doc/blob/master/meta/documentation_style.rst.

Python code within the ``matrix-doc`` project should follow the same style as
synapse, which is documented at
https://github.com/matrix-org/synapse/tree/master/docs/code_style.md.

Matrix-doc workflows
--------------------

Specification changes
~~~~~~~~~~~~~~~~~~~~~

The Matrix specification documents the APIs which Matrix clients and servers use.
For this to be effective, the APIs need to be present and working correctly in a
server before they can be documented in the specification. This process can take
some time to complete.

Changes to the protocol (new endpoints, ideas, etc) need to go through the
`proposals process <https://matrix.org/docs/spec/proposals>`_. Other changes,
such as fixing bugs, typos, or clarifying existing behaviour do not need a proposal.
If you're not sure, visit us at `#matrix-spec:matrix.org`_ and ask.

Other changes
~~~~~~~~~~~~~

The above process is unnecessary for smaller changes, and those which do not
put new requirements on servers. This category of changes includes the
following:

* Changes to the scripts used to generate the specification.

* Addition of features which have been in use in practice for some time, but
  have never made it into the spec (including anything with the `spec-omission
  <https://github.com/matrix-org/matrix-doc/labels/spec-omission>`_ label).

* Likewise, corrections to the specification, to fix situations where, in
  practice, servers and clients behave differently to the specification,
  including anything with the `spec-bug
  <https://github.com/matrix-org/matrix-doc/labels/spec-bug>`_ label.

  (If there is any doubt about whether it is the spec or the implementations
  that need fixing, please discuss it with us first in `#matrix-spec:matrix.org`_.)

* Clarifications to the specification which do not change the behaviour of
  Matrix servers or clients in a way which might introduce compatibility
  problems for existing deployments. This includes anything with the
  `clarification <https://github.com/matrix-org/matrix-doc/labels/clarification>`_
  label.

  For example, areas where the specification is unclear do not require a proposal
  to fix. On the other hand, introducing new behaviour is best represented by a
  proposal.

* Design or aesthetic changes, such as improving accessibility, colour schemes,
  etc. Please check in with us at `#matrix-docs:matrix.org`_ with your proposed
  design change before opening a PR so we can work with you on it.

For such changes, please do just open a `pull request`_. If you're not sure if
your change is covered by the above, please visit `#matrix-spec:matrix.org` and
ask.

.. _`pull request`: https://help.github.com/articles/about-pull-requests
.. _`#matrix-spec:matrix.org`: https://matrix.to/#/#matrix-spec:matrix.org
.. _`#matrix-docs:matrix.org`: https://matrix.to/#/#matrix-docs:matrix.org


Adding to the changelog
~~~~~~~~~~~~~~~~~~~~~~~

All API specifications require a changelog entry. Adding to the changelog can only
be done after you've opened your pull request, so be sure to do that first.

The changelog is managed by Towncrier (https://github.com/hawkowl/towncrier) in the
form of "news fragments". The news fragments for the client-server API are stored
under ``changelogs/client_server/newsfragments``.

To create a changelog entry, create a file named in the format ``prNumber.type`` in
the ``newsfragments`` directory. The ``type`` can be one of the following:

* ``new`` - Used when adding new endpoints. Please have the file contents be the
  method and route being added, surrounded in RST code tags. For example: ``POST
  /accounts/whoami``

* ``feature`` - Used when adding backwards-compatible changes to the API.

* ``clarification`` - Used when an area of the spec is being improved upon and does
  not change or introduce any functionality.

* ``breaking`` - Used when the change is not backwards compatible.

* ``deprecation`` - Used when deprecating something.

All news fragments must have a brief summary explaining the change in the
contents of the file. The summary must end in a full stop to be in line with
the style guide and and formatting must be done using Markdown.

Changes that do not change the spec, such as changes to the build script, formatting,
CSS, etc should not get a news fragment.

Sign off
--------

We ask that everybody who contributes to their project signs off their
contributions, as explained below.

We follow a simple 'inbound=outbound' model for contributions: the act of
submitting an 'inbound' contribution means that the contributor agrees to
license their contribution under the same terms as the project's overall 'outbound'
license - in our case, this is Apache Software License v2 (see LICENSE).

In order to have a concrete record that your contribution is intentional
and you agree to license it under the same terms as the project's license, we've adopted the
same lightweight approach that the Linux Kernel
(https://www.kernel.org/doc/Documentation/SubmittingPatches), Docker
(https://github.com/docker/docker/blob/master/CONTRIBUTING.md), and many other
projects use: the DCO (Developer Certificate of Origin:
http://developercertificate.org/). This is a simple declaration that you wrote
the contribution or otherwise have the right to contribute it to Matrix::

    Developer Certificate of Origin
    Version 1.1

    Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
    660 York Street, Suite 102,
    San Francisco, CA 94110 USA

    Everyone is permitted to copy and distribute verbatim copies of this
    license document, but changing it is not allowed.

    Developer's Certificate of Origin 1.1

    By making a contribution to this project, I certify that:

    (a) The contribution was created in whole or in part by me and I
        have the right to submit it under the open source license
        indicated in the file; or

    (b) The contribution is based upon previous work that, to the best
        of my knowledge, is covered under an appropriate open source
        license and I have the right under that license to submit that
        work with modifications, whether created in whole or in part
        by me, under the same open source license (unless I am
        permitted to submit under a different license), as indicated
        in the file; or

    (c) The contribution was provided directly to me by some other
        person who certified (a), (b) or (c) and I have not modified
        it.

    (d) I understand and agree that this project and the contribution
        are public and that a record of the contribution (including all
        personal information I submit with it, including my sign-off) is
        maintained indefinitely and may be redistributed consistent with
        this project or the open source license(s) involved.

If you agree to this for your contribution, then all that's needed is to
include the line in your commit or pull request comment::

    Signed-off-by: Your Name <your@email.example.org>

...using your real name; unfortunately pseudonyms and anonymous contributions
can't be accepted. Git makes this trivial - just use the -s flag when you do
``git commit``, having first set ``user.name`` and ``user.email`` git configs
(which you should have done anyway :)
