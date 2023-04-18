# Contributing to `matrix-spec-proposals`

Thank you for taking the time to contribute to Matrix!

This repository is for proposals for changes to the Matrix protocol. The process
for submitting a proposal is described in
[this repository's README](README.md#the-matrix-spec-process) or in further detail at
https://spec.matrix.org/proposals/#process.

## Sign off

We ask that everybody who contributes to this project signs off their
contributions, as explained below.

We follow a simple 'inbound=outbound' model for contributions: the act of
submitting an 'inbound' contribution means that the contributor agrees to
license their contribution under the same terms as the project's overall
'outbound' license - in our case, this is Apache Software License v2 (see
[LICENSE](./LICENSE)).

In order to have a concrete record that your contribution is intentional and
you agree to license it under the same terms as the project's license, we've
adopted the same lightweight approach used by the [Linux
Kernel](https://www.kernel.org/doc/html/latest/process/submitting-patches.html),
[Docker](https://github.com/docker/docker/blob/master/CONTRIBUTING.md), and
many other projects: the [Developer Certificate of
Origin](http://developercertificate.org/) (DCO). This is a simple declaration
that you wrote the contribution or otherwise have the right to contribute it to
Matrix:

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
include the line in your commit or pull request comment:

    Signed-off-by: Your Name <your@email.example.org>

...using your real name; unfortunately pseudonyms and anonymous contributions
can't be accepted. Git makes this trivial - just use the -s flag when you do
``git commit``, having first set ``user.name`` and ``user.email`` git configs
(which you should have done anyway :)

### Private sign off

If you would like to provide your legal name privately to the Matrix.org
Foundation (instead of in a public commit or comment), you can do so by emailing
your legal name and a link to the pull request to dco@matrix.org. It helps to
include "sign off" or similar in the subject line. You will then be instructed
further.

Once private sign off is complete, doing so for future contributions will not be required.

[1]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
