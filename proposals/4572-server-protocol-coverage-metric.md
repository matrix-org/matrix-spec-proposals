# MSC4572: Metric for server protocol coverage

The [Governing Board](https://matrix.org/foundation/governing-board/) via a combination of the
[Website and Content](https://matrix.org/foundation/working-groups/#website-content) and 
[Governance](https://matrix.org/foundation/working-groups/#governance) working groups intends to 
modernize the [server ecosystem page](https://matrix.org/ecosystem/servers/) on the website. This
effort will make it clearer to prospective server operators which project may be a better fit for 
their needs. 

Server projects are expected to be measured by a few different metrics. One of those metrics is 
protocol coverage: how well does it speak Matrix? This proposal outlines a broad metric using 
[Complement](https://github.com/matrix-org/complement) test coverage, refining it further with 
manual intervention from the Spec Core Team and modern spec release support in the project.

**Note**: The spec process's implementation requirements are modified by this proposal to better 
support the metric. Specifically, Complement tests are made mandatory prior to acceptance of a 
proposal.


----

**Process note**: This proposal MAY be implemented in part or whole before being accepted in order
to evaluate it. Adjustments will be made based on that implementation. For example, the matrix.org
website in the immediate term might simply look at the Complement test coverage portion of this 
proposal and ignore the remainder regarding latest spec release, re-evaluation timelines, etc. Which
parts of this proposal are implemented by the website maintainers is a decision left to those 
maintainers in collaboration with the Governance Working Group.

----


## Proposal

In short, protocol coverage is defined as the percentage of *qualifying* [Complement](https://github.com/matrix-org/complement)
tests which pass. Tests which aren't in the main Complement repo, test unstable/unprefixed functionality,
or are for a specific server project do not qualify. All other tests do qualify.

When a server project is first submitted to the matrix.org website, or wants to update its protocol
coverage metric, it MUST include a reproducible Complement test result in the website PR. That result 
MUST use the latest `HEAD` of Complement at the time of submission (+/- 3 days), and MUST use the 
latest release of the server project at the time of submission (no leeway).

If a server project puts out a new release while the PR is open, it MUST update its PR accordingly.

"Reproducible result" does not mean the Website & Content Working Group needs to run Complement tests.
It means that the GitHub Action logs, for example, clearly show that the test suites and software 
versions are in line with the above policy. Anyone on the Website & Content Working Group or Spec
Core Team (SCT) MAY manually verify a result, when possible to do so. 

**Note**: The Website & Content Working Group is discouraged from accepting text-only results. For
example, those in a code block in the PR description or as a text file. Links to *public* CI builds
are strongly encouraged for transparency.

**Note**: Proprietary or closed source server projects are not required to give the SCT or Website &
Content Working Group access to their software for test verification purposes. However, per above, 
the submitted test results cannot be a text file-like dump. A project could, for example, create a
repo which has the sole purpose of running the test suite publicly by authenticating with the distribution
platform, but not disclosing the source code in the process. 

**Note**: Suspected "cheating" by projects (open source or otherwise) is investigated by the Foundation's
Trust & Safety (T&S) team. The T&S team will determine what actions to take, if any. Potential actions 
include pinning, adjusting, or removing a project's protocol coverage metric by any amount, and removing 
the project from the website. 

**Note**: The Foundation's Standards Development team (which includes the SCT) will contribute a test
tag to Complement to make verifying the test list easier. This should mean that the PR reviewer only
needs to look for `-tags="protocol_coverage"` (for example).

The protocol coverage is then `(number_passing_tests / total_qualifying_tests) * 100`% (nearest integer).

At any time, the SCT MAY decrease a project's result by up to 25% to account for test inadequacies. 
All rationale for such a decrease MUST be publicly disclosed in an accessible way (ie: in the GitHub 
PR description making the adjustment, not a chat room somewhere). For example: "This project
knowingly throws 500 errors to all `/event/$whatever` requests, which is not covered by a Complement
test. The metric is reduced by N%".

The latest release of a server project MUST support at least one of the spec releases in the last 2
years on the [`/versions`](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientversions)
endpoint. With the spec's current quarterly release schedule, this is roughly 8 spec releases. If a 
server project doesn't support at least one of those spec releases, its protocol coverage is 
`not measured` (instead of 0% or anything like that).

**Note**: Projects update all the time, including servers, Complement, and the spec itself. To account
for this, the metric can and does change as those projects update. For example:

* If Complement adds 30 more qualifying tests, `total_qualifying_tests` increases by 30 for all projects.
  The website isn't required to update immediately upon those tests being added, but should update
  approximately once a quarter (ie: around spec releases). The `number_passing_tests` for each project
  is not updated automatically - the project's maintainers should contribute that change.

* If a server project isn't updated for 2 years, it will fall behind on spec releases. During the above
  quarterly-ish check, projects which no longer support a qualifying spec version SHOULD have their 
  coverage metric changed to `not measured`. 

* If a server project puts out a release with better protocol coverage, they can submit a PR to the 
  website with updated (reproducible) results. 
  
* Server projects with an Long-Term Stable (LTS) release channel alongside a "bleeding edge" or community
  channel will have that non-LTS channel evaulated instead. 

In order to ensure the fullest possible set of Complement tests, the proposal process is modified to
require a Complement test PR be opened as an implementation requirement on all MSCs (unless the proposal
doesn't modify the functionality of the protocol itself, like this one). The PR is not required to be
reviewed or merged in the general case, though the SCT MAY ask for such conditions depending on the
proposal itself.


## Potential issues

Most issues are already covered in the above proposal text. There are a few which aren't explicitly
covered, though:

* Server projects which don't re-test themselves periodically will see their protocol coverage *decrease*
  over time. This is an expected consequence of the protocol coverage metric - the website maintainers 
  will update all projects against the latest number of Complement tests, current spec release support, 
  and adjust according to SCT decisions. The server project itself is responsible for updating the
  number of passing tests, not the website maintainers. 

  Projects which update their coverage too frequently might face moderation action separate to this
  proposal. 

* Projects might be unwilling (or unable) to engage in the protocol coverage process. Those projects
  receive a `not measured` protocol coverage score rather than 0% or similar.

* Verifying that `/versions` has a modern spec release listed might be challenging for each and every
  project. Instead of having website maintainers jump into code or test representative publicly available
  instances, they can rely on the project's maintainers being honest regarding their spec release
  support. T&S will investigate claims of lying/cheating. 

* As of writing, Complement is not in the greatest shape, but it is the best the Foundation has at 
  the moment. The Foundation's Standards Development team intends to ensure maintenance of the repo
  picks back up, including moving project- (Synapse-) specific tests to their respective projects,
  adding the `protocol_coverage` test tag mentioned in the proposal, and generally increasing the 
  base number of tests for overall protocol coverage. Contributions towards this effort are very 
  appreciated (though may take some time to get landed while maintenance picks back up). 


## Alternatives

Measuring protocol coverage is a distinctly hard problem to do fairly. We could allow projects to
self-describe their coverage (similar to today), though that would result in questions like "how did
you determine you have 154% coverage?". We could similarly develop a list of (verifiable?) checkboxes
for each and every MUST/SHOULD/MAY in the spec, however at that point it starts to look eerily similar
to a `✅ Can send events` Complement test result. 


## Security considerations

For this proposal, security considerations largely amount to ensuring the metric is fair and transparent.
This includes handling projects which attempt to cheat the system and providing receipts where claims
are made regarding a project's protocol coverage. 


## Unstable prefix

Mentioned in the introduction, this proposal MAY be implemented in part or in whole ahead of formal
acceptance. No unstable prefix is required due to no technical changes being introduced.


## Dependencies

This proposal has no proposal dependencies, but will require review from the Governance Working Group,
Trust & Safety team, and Website & Content Working Group at a minimum. 
