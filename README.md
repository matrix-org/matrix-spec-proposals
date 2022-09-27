# Matrix Specification Proposals

This repository contains proposals for changes to the [Matrix
Protocol](http://spec.matrix.org), aka "Matrix Spec Changes" (MSCs). The
[`proposals`](./proposals) directory contains MSCs which have been accepted.

See below for instructions for creating new
proposals. See also https://spec.matrix.org/proposals/ for more
information on the MSC process, in particular
https://spec.matrix.org/proposals/#process.

The source of the Matrix specification itself is maintained at
https://github.com/matrix-org/matrix-spec.

## The Matrix Spec Process

An MSC is meant to be a **technical document that unambiguously describes a
change to the Matrix Spec**, while also justifying _why_ the change should be
made.

The document is used both to judge whether the change should be made as
described *and* by developers to actually implement the changes. This is why
it's important for an MSC to be fully fleshed out in technical detail, as once
merged it's immediately part of the formal spec (even though it still needs to
be transcribed into the actual spec itself).

### What changes need to follow this process?

In most cases a change to [the Matrix protocol](https://spec.matrix.org) will
require an MSC. Changes that would not require an MSC are typically small and
uncontentious, or are simply clarifications to the spec. Fixing typos in the
spec do not require an MSC. In most cases, removing ambiguities do not either.
The exception may be if implementations in the ecosystem have differing views
on clarifying the ambiguity. In that case, an MSC is typically the best place
to reach consensus.

Ultimately, the [Spec Core Team](https://matrix.org/foundation) have the final
say on this, but generally if the change would require updates to a
non-insignificant portion of the Matrix implementation ecosystem or would be
met with contention, an MSC is the best route to take. You can also ask in the
[Matrix Spec](https://matrix.to/#/#matrix-spec:matrix.org) or [Office of the
Spec Core Team](https://matrix.to/#/#sct-office:matrix.org) Matrix rooms for
clarification.

### Summary of the process

The MSC process consists of five basic steps:

1. **Write up the proposal** in a
   [markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#GitHub-flavored-markdown)
   document. (There's a [proposal
   template](proposals/0000-proposal-template.md), but don't feel bound by it.)
2. **Submit it as a Pull Request** to this repo, adding "WIP" to the title if
   it's still a work in progress.
3. **Seek review** from the community. Once people are happy
   with it, ask the [Spec Core Team](https://matrix.org/foundation) to
   look at it in
   [the Office of the SCT Matrix room](https://matrix.to/#/#sct-office:matrix.org).
4. When the SCT are happy with the proposal, they'll vote for its acceptance.
   The proposal will go into a **Final Comment Period (FCP)**, which gives
   everyone the chance to raise any concerns.
5. After 5 days has passed, assuming no major issues have arisen, your pull
   request is merged and the **MSC is now officially accepted** as part of the
   Matrix Spec and can be used 🎉

For simple changes this is really all you need to know. For larger or more
controversial changes, getting an MSC merged can take more time and effort, but
the overall process remains the same.

Below is various guidance to try and help make the experience smoother.

### Guidance on the process

#### Step 1: Writing the proposal

Come up with an idea. The idea can be for anything, but the solution (MSC)
needs to benefit the Matrix ecosystem rather than yourself (or your company)
specifically. Sometimes this means that the solution needs to be more generic
than the specific itch that you are trying to scratch.

Remember that an MSC is a formal technical document which will be used by
others in the wider community to judge if the proposal should be accepted *and*
to actually implement the changes in clients and servers. This means that for
an MSC to be accepted it should include justifications and describe the
technical changes unambiguously, including specifying what happens in any and
all edge cases.

There's a [proposal template](proposals/0000-proposal-template.md) under
`docs/0000-proposal.md`, but you don't necessarily need to use it. Covering the
same major points is fine.
  * Note: At this stage, you won't have an MSC number, so feel free to use
    `0000`, `XXXX`, or whatever other placeholder you feel comfortable with.

Some tips for MSC writing:

* Please wrap your lines to 80 characters maximum (some small leeway is OK).
  This allows readers to review your markdown without needing to horizontally
  scroll back and forth. Many markdown text editors have this a feature.
* If you are referencing an existing endpoint in the spec, or another MSC, it
  is very helpful to add a link to them so the reader does not need to search
  themselves. Examples:
    * "This MSC proposals an alternative to
      [MSC3030](https://github.com/matrix-org/matrix-spec-proposals/pull/3030)."
    * "A new field will be added to the response body of
      [`/_matrix/client/v3/sync`](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3sync)".
        * Note: it is best to link to the latest stable version of the spec
          (e.g. /v1.3, not /latest) - failing that,
          [/unstable](https://spec.matrix.org/unstable/) if the change is not
          yet in a released spec version.
* GitHub supports rendering fancy diagrams from text with very little
  effort using [Mermaid](https://mermaid-js.github.io/mermaid/#/). See [this
  guide](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/)
  for more information.

#### Step 2: Submitting a Pull Request

1. Open a [Pull
   Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request)
   to add your proposal document to the [`proposals`](proposals) directory.
   Note that this will require a GitHub account.
      * [Mark your Pull Request as a
        draft](https://github.blog/2019-02-14-introducing-draft-pull-requests/)
        for now.
2. The MSC number is the number of the pull request that is automatically
   assigned by GitHub. Go back through and edit the document accordingly. Don't
   forget the file name itself!
3. Edit the pull request title to fit the format "MSC1234: Your proposal
   title".
4. Once your proposal is correctly formatted and ready for review from the
   wider ecosystem, [take your Pull Request out of draft
   status](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/changing-the-stage-of-a-pull-request#marking-a-pull-request-as-ready-for-review).

The Spec Core Team will notice this and apply various labels/status tracking to
your MSC, which will announce it to the wider world.

#### Step 3: Seeking review

Seek review from the Matrix community. Generally this will happen naturally,
but if you feel that your proposal is lacking review then ask for people's
opinion in the [Matrix Spec room on
Matrix](https://matrix.to/#/#matrix-spec:matrix.org).

Reviews can take many forms, and do not need to be done solely by members of
the Spec Core Team. Getting other people who are familiar with the area of
Matrix you are proposing changes to is a great first step; especially those who
may be implementing these changes in clients and/or homeservers.

While the proposal is a work in progress, it's fine for it to be high level
and hand-wavy in places, but remember that before it can be accepted it needs
to be expanded to fully flesh out all the technical detail and edge cases.

At this stage the proposal should also be implemented as a proof of concept
somewhere to show that it _actually_ works in practice. This can be done on any
client or server and doesn't need to be merged or released.

#### Step 4: Entering Final Comment Period

After the MSC has been implemented, fully fleshed out, and generally feels
ready for final review, you should ask a member of the Spec Core Team to review it in
the public [Spec Core Team Office room on
Matrix](https://matrix.to/#/#sct-office:matrix.org). Someone from the SCT will
then review it, and if all looks well will propose FCP
to start.

At this point, other members of the SCT will look at the proposal and consider
it for inclusion in the spec.

After enough SCT members have approved the proposal, the MSC will enter
something called _Final Comment Period_. This is a 5 calendar day countdown to
give anyone one last chance to raise any blockers or concerns about the
proposed change. Typically MSCs pass this stage without incident, but it
nevertheless serves as a safeguard.

#### Step 5: MSC is accepted

Once FCP has end and the MSC pull request merged, the proposed change
is considered officially part of the spec. Congratulations!

Clients and servers can now start using the change, even though at this stage
it still needs to be transcribed into the spec document. This happens over in
https://github.com/matrix-org/matrix-spec/ and is typically handled by the Spec
Core Team themselves.

### Other useful information

#### Unstable prefixes

*Unstable* prefixes are the namespaces which are used before an MSC has
completed FCP (see above). While the MSC might propose that a `m.space` or
`/_matrix/client/v1/account/whoami` endpoint should exist, the implementation
cannot use a *stable* identifier such as `/v1/` or `m.space` prior to the MSC
being accepted: it needs unstable prefixes.

Typically for MSCs, one will use `org.matrix.msc0000` (using the real MSC
number once known) as a prefix. For the above examples, this would mean
`org.matrix.msc0000.space` and
`/_matrix/client/unstable/org.matrix.msc0000/account/whoami` to allow for
breaking compatibility changes between edits of the MSC itself, or indeed
another competing MSC that's attempting to add the same identifiers.


#### Room versions

To summarize [the spec](https://spec.matrix.org/latest/rooms/) on room
versions: they are how servers agree upon algorithms in a decentralized world
like ours. Examples of changes that require a new room version include anything that changes:
 * the format of the core event structure (such as renaming a top-level field),
   as this will change the [reference
   hash](https://spec.matrix.org/latest/server-server-api/#calculating-the-reference-hash-for-an-event)
   of an event.
 * [the authorisation of
   events](https://spec.matrix.org/latest/server-server-api/#authorization-rules)
   (such as changes to power levels).
 * [the redaction
   algorithm](https://spec.matrix.org/latest/client-server-api/#redactions).

See [an example of an MSC](https://github.com/matrix-org/matrix-spec-proposals/pull/3667) that proposes a new room version.

Unstable prefixes (see above) for room versions work the same as they do for
other identifiers; your unstable room version may be called
"org.matrix.msc1234".

In order for the changes to end up in a "real" room version (the ones listed in
the spec), it will need a second MSC which aggregates a bunch of functionality
from varying MSCs into a single room version. Typically these sorts of curating
MSCs are written by the Spec Core Team given the complexity in wording, but
you're more than welcome to bring an MSC forward which makes the version real.

Note that your MSC *should not* declare the stable room version it gets
included in - it should simply specify the need for a new room version as well
as the unstable identifier. Even after your MSC is accepted, your change will
remain as part of a prefixed room version until a second room version MSC is
accepted.

For a relatively simple example of what introducing a new room version-required
feature can look like, see
[MSC3613](https://github.com/matrix-org/matrix-doc/pull/3613). For an example
of what making a new "real" room version looks like, see
[MSC3604](https://github.com/matrix-org/matrix-doc/pull/3604).

#### Ownership of MSCs and closing them

If an author decides that they would no longer like to pursue their MSC, they
can either pass ownership of it off to someone else, or close it themselves.

* The author of an MSC can close their MSC at any time before FCP by simply
  closing the pull request.
* To appoint another user as an author of the MSC (either to replace the author
  entirely or to provide additional help), make a note in the MSC's PR
  description by writing the following on its own line:

  ```
  Author: @username
  ```

  where `@username` is a valid GitHub username. Multiple such lines can be
  added.

  Finally, [give that user access to write to your fork of
  matrix-spec-proposals on
  GitHub](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/inviting-collaborators-to-a-personal-repository),
  which your PR originates from. This will allow them to change the text of
  your MSC.

Similar to accepting an MSC, the Spec Core Team may propose a Final Comment
Period with a disposition of "close". This can happen if the MSC appears
abandoned by its author, or the idea is widely rejected by the community. A
vote and final comment period will still be required for the motion to pass.

Additionally, FCP can be also proposed with a disposition of "postpone". This
may be done for MSCs for which the proposed changes do not make sense for the
current state of the ecosystem, but may make sense further down the road.

## Asking for help

The Matrix community and members of the Spec Core Team are here to help guide
you through the process!

If you'd just like to get initial feedback about an idea that's not fully
fleshed out yet, creating an issue at
https://github.com/matrix-org/matrix-spec/issues is a great place to start. Be
sure to search for any existing issues first to see if someone has already had
the same idea!

A few official rooms exist on Matrix where your questions can be answered, or
feedback on your proposal can be requested:

* [#matrix-spec:matrix.org](https://matrix.to/#/#matrix-spec:matrix.org) -
  General chat for MSCs, the spec, and pretty much anything in that sphere.
* [#sct-office:matrix.org](https://matrix.to/#/#sct-office:matrix.org) - Where
  the Spec Core Team hangs out and is available. This room is intended to have
  extremely high signal and low noise, primarily to ensure that MSCs are not
  falling through the cracks. If an MSC requires attention or comment from Spec
  Core Team members, bring it up here.
* [#matrix-spec-process:matrix.org](https://matrix.to/#/#matrix-spec-process:matrix.org) - A
  room dedicated to [the spec process
  itself](https://spec.matrix.org/proposals/#process). If you have any
  questions about or suggestions to improve the Matrix Spec process, ask them
  here.
* [#matrix-docs:matrix.org](https://matrix.to/#/#matrix-docs:matrix.org) - A
  quieter room for discussion of the [formal spec
  text](https://spec.matrix.org) and [matrix.org](https://matrix.org) website.