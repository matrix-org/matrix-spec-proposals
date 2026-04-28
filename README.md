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

The MSC process consists of three basic steps:

1. **Write up the proposal** in a
   [markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#GitHub-flavored-markdown)
   document. (There's a [proposal
   template](proposals/0000-proposal-template.md), but don't feel bound by it.)
2. **Submit it as a Pull Request** to this repo, marking it as a draft until
   it's ready for wider review.
3. **Seek review** from the community. Once people are generally happy with it,
   ask the [Spec Core Team](https://matrix.org/foundation/about/#the-spec-core-team) to look at it in
   [the Office of the SCT Matrix
   room](https://matrix.to/#/#sct-office:matrix.org). When the SCT are happy
   with the proposal, and after a successful voting process, your pull request
   is merged and the **MSC is now officially accepted** as part of the Matrix
   Spec and can be used 🎉

For simple changes this is really all you need to know. For larger or more
controversial changes, getting an MSC merged can take more time and effort, but
the overall process remains the same.

Below is various guidance to try and help make the experience smoother.

### Guidance on the process

#### 1. Writing the proposal

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

* Please wrap your lines to 120 characters maximum.
  This allows readers to review your markdown without needing to horizontally
  scroll back and forth. Many markdown text editors have this feature.
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
* Take a look at the [MSC Checklist](MSC_CHECKLIST.md). When it comes time for
  the Spec Core Team to review your MSC for acceptance, they'll use the items
  on this checklist as a guide.

#### 2. Submitting a Pull Request

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

#### 3. Seeking review

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

#### 4. Entering Final Comment Period

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

#### 5. The MSC is accepted

Once FCP has ended and the MSC pull request is merged, the proposed change is
considered officially part of the spec. Congratulations!

Clients and servers can now start using the change, even though at this stage
it still needs to be transcribed into the spec document. This happens over in
https://github.com/matrix-org/matrix-spec/ and you are very welcome to do it
yourself! Otherwise it will be handled by a Spec Core Team member. If you would
like help with writing spec PRs, feel free to join and ask questions in the
[Matrix Spec and Docs Authoring Room on Matrix](https://matrix.to/#/#matrix-docs:matrix.org).

### Other useful information

#### Unstable prefixes

"Unstable prefixes" are the namespaces which are used by implementations while
an MSC is not yet accepted.

For instance, an MSC might propose that a `m.space`
event type or an `/_matrix/client/v1/account/whoami` endpoint should exist.
However, implementations cannot use these *stable* identifiers until the MSC
has been accepted, as the underlying design may change at any time; the design is
*unstable*.

Instead, an MSC can define a namespace such as `org.matrix.msc1234` (using the real
MSC number once known) which is added to the stable identifier, allowing for
breaking changes between edits of the MSC itself, and preventing clashes with other
MSCs that might attempt to add the same stable identifiers.

For the above examples, this would mean using `org.matrix.msc1234.space` and
`/_matrix/client/unstable/org.matrix.msc1234/account/whoami`. It is also fine to
use more traditional forms of namespace prefixes, such as `com.example.*` (e.g.
`com.example.space`).

Note: not all MSCs need to make use of unstable prefixes. They are only needed if
implementations of your MSC need to exist in the wild before your MSC is accepted,
*and* the MSC defines new endpoints, field names, etc.

#### Unstable feature flags

It is common when implementing support for an MSC that a client may wish to check
if the homeserver it is communicating with supports an MSC.
Typically, this is handled by the MSC defining an
entry in the `unstable_features` dictionary of the
[`/_matrix/client/versions`](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientversions)
endpoint, in the form of a new entry:

```json5
{
  "unstable_features": {
    "org.matrix.msc1234": true
  }
}
```

... with a value of `true` indicating that the feature is supported, and `false`
or lack of the field altogether indicating the feature is not supported.

#### When can I use stable identifiers?

[According to the spec
process](https://spec.matrix.org/proposals/#early-release-of-an-mscidea): once
an MSC has been accepted, implementations are allowed to switch to *stable*
identifiers. However, the MSC is still not yet part of a released spec version.

In most cases, this is not an issue. For instance, if your MSC specifies a new
event type, you can now start sending events with those types!

Some MSCs introduce functionality where coordination between implementations is
needed. For instance, a client may want to know whether a homeserver supports
the stable version of a new endpoint before actually attempting to request it.
Or perhaps the new event type you're trying to send relies on the homeserver
recognising that new event type, and doing some work when it sees it.

At this point, it may be best to wait until a new spec version is released with
your changes. Homeservers that support the changes will eventually advertise
that spec version under `/versions`, and your client can check for that.

But if you really can't wait, then there is another option: the homeserver can
tell clients that it supports *stable* identifiers for your MSC before it
enters a spec version, using yet another `unstable_features` flag:

```json5
{
  "unstable_features": {
    "org.matrix.msc1234": true,
    "org.matrix.msc1234.stable": true
  }
}
```

If a client sees that `org.matrix.msc1234.stable` is `true`, it knows that it
can start using stable identifiers for the new MSC, and the homeserver will
accept and act on them accordingly.

Note: While the general pattern of using the text ".stable" has emerged from
previous MSCs, you can pick any name you like. You need only to clearly state
their meaning, usually under an "Unstable prefixes" header in your MSC.

See
[MSC3827](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3827-space-explore.md#unstable-prefix)
for a good example of an MSC that wanted to use such a flag to speed up
implementation rollout, and how it did so.

#### Room versions

To summarize [the spec](https://spec.matrix.org/latest/rooms/) on room
versions: they are how servers agree upon algorithms in a decentralized world
like ours. Examples of changes that require a new room version include anything that changes:
 * The format of the core event structure (such as renaming a top-level field,
   or modifying [the redaction
   algorithm](https://spec.matrix.org/latest/client-server-api/#redactions)),
   therefore altering the [reference
   hash](https://spec.matrix.org/latest/server-server-api/#calculating-the-reference-hash-for-an-event)
   of an event.
 * [The authorisation of
   events](https://spec.matrix.org/latest/server-server-api/#authorization-rules)
   (such as changes to power levels).

Unstable prefixes (see above) for room versions work the same as they do for
other identifiers; your unstable room version may be called
"org.matrix.msc1234".

In order for the changes to end up in a "real" room version (the ones listed in
the spec), it will need a second MSC which aggregates a bunch of functionality
from various MSCs into a single room version. Typically these sorts of curating
MSCs are written by the Spec Core Team given the complexity in wording, but
you're more than welcome to bring an MSC forward which makes the version real.

For an example of what introducing a new room version-required feature can look
like, see [MSC3667](https://github.com/matrix-org/matrix-doc/pull/3667). For an
example of what making a new "real" room version looks like, see
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
