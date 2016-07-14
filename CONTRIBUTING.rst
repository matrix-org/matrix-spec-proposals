Contributing to matrix-doc
==========================

Everyone is welcome to contribute to the ``matrix-doc`` project, provided that they
are willing to license their contributions under the same license as the
project itself. We follow a simple 'inbound=outbound' model for contributions:
the act of submitting an 'inbound' contribution means that the contributor
agrees to license the code under the same terms as the project's overall
'outbound' license - in our case, this is Apache Software License
v2 (see LICENSE).

Specification changes
~~~~~~~~~~~~~~~~~~~~~

The Matrix specification documents the APIs which Matrix clients can use. For
this to be effective, the APIs need to be present and working correctly in a
server before they can be documented in the specification. This process can
take some time to complete.

For this reason, we have not found the github pull-request model effective for
discussing changes to the specification. Instead, we have adopted the following
workflow:

1. Create a discussion document outlining the proposed change. The document
   should include details such as the HTTP endpoint being changed (or the
   suggested URL for a new endpoint), any new or changed parameters and response
   fields, and generally as much detail about edge-cases and error handling as
   is practical at this stage.

   The Matrix Core Team's preferred tool for such discussion documents is
   `Google Docs <https://docs.google.com>`_ thanks to its support for comment
   threads. Works in progress are kept in a folder at
   https://drive.google.com/drive/folders/0B4wHq8qP86r2ck15MHEwMmlNVUk.

2. Seek feedback on the proposal. `#matrix-dev:matrix.org
   <http://matrix.to/#/#matrix-dev:matrix.org>`_ is a good place to reach the
   core team and others who may be interested in your proposal.

3. Implement the changes in servers and clients. Refer to the CONTRIBUTING files
   of the relevant projects for details of how best to do this.

   In general we will be unable to publish specification updates until the
   reference server implements them, and they have been proven by a working
   client implementation.

4. Iterate steps 1-3 as necessary.

5. Write the specification for the change, and create a `pull request`_ for
   it. It may be that much of the text of the change can be taken directly from
   the discussion document, though typically some effort will be needed to
   change to the ReST syntax and to ensure that the text is as clear as
   possible.


Other changes
~~~~~~~~~~~~~

The above process is unnecessary for smaller changes, and those which do not
put new requirements on servers. This category of changes includes the
following:

* changes to supporting documentation

* changes to the scripts used to generate the specification

* clarifications to the specification which do not change the behaviour of
  Matrix servers or clients in a way which might introduce compatibility
  problems for existing deployments. For example, recommendations for UI
  behaviour do not require a proposal document. On the other hand, changes to
  event contents would be best discussed in a proposal document even though no
  changes would be necessary to server implementations.

For such changes, please do just open a `pull request`_.


Pull requests
~~~~~~~~~~~~~
.. _pull request: `Pull requests`_

The preferred and easiest way to contribute changes to the ``matrix-doc`` project
is to fork it on github, and then create a pull request to ask us to pull your
changes into our repo (https://help.github.com/articles/using-pull-requests/).

(Note that, unlike most of the other matrix.org projects, pull requests for
matrix-doc should be based on the ``master`` branch.)

Code style
~~~~~~~~~~

The documentation style is described at
https://github.com/matrix-org/matrix-doc/blob/master/meta/documentation_style.rst.

Python code within the ``matrix-doc`` project should follow the same style as
synapse, which is documented at
https://github.com/matrix-org/synapse/tree/master/docs/code_style.rst.

Sign off
~~~~~~~~

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
