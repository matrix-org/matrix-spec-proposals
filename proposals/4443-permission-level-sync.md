# MSC0000: Permission Level Sync

Managing permissions across many rooms in a Matrix Space is currently a manual and error-prone process. 
If a community or organisation has a Space containing dozens of rooms, and an administrator wants to
promote a user to moderator across all of those rooms, they must visit each room individually and update
that user's power level by hand. This proposal adds a setting to the a room which allows the user to 
define a secondary room to sync permission level's with.

## Proposal

*Here is where you'll reinforce your position from the introduction in more detail, as well as cover
the technical points of your proposal. Including rationale for your proposed solution and detailing
why parts are important helps reviewers understand the problem at hand. Not including enough detail
can result in people guessing, leading to confusing arguments in the comments section. The example
here covers why templates are important again, giving a stronger argument as to why we should have
a template. Afterwards, it goes on to cover the specifics of what the template could look like.*

Having a default template that everyone can use is important. Without a template, proposals would be
all over the place and the minimum amount of detail may be left out. Introducing a template to the
proposal process helps ensure that some amount of consistency is present across multiple proposals,
even if each author decides to abandon the template.

The default template should be a markdown document because the MSC process requires authors to write
a proposal in markdown. Using other formats wouldn't make much sense because that would prevent authors
from copy/pasting the template.

The template should have the following sections:

* **Introduction** - This should cover the primary problem and broad description of the solution.
* **Proposal** - The gory details of the proposal.
* **Potential issues** - This is where problems with the proposal would be listed, such as changes
  that are not backwards compatible.
* **Alternatives** - This section lists alternative solutions to the same
  problem which have been considered and dismsissed.
* **Security considerations** - Discussion of what steps were taken to avoid security issues in the
  future and any potential risks in the proposal.

Furthermore, the template should not be required to be followed. However it is strongly recommended to
maintain some sense of consistency between proposals.


## Potential issues
Homeserver might not be in both rooms, creating a mismatch between power levels. This can be
solved by allowing another homeserver to update the permissions on the other rooms provided
that there is a user on that server with sufficient permissions.

## Alternatives

Using bots is an option however this is "clunky" as the bot would need to be added to all the rooms,
with spesific permissions


## Security considerations
None that I can think of, though there are certainly going to be some

## Unstable prefix


## Dependencies

This MSC builds on [MSC1772](https://github.com/matrix-org/matrix-spec-proposals/pull/1772)

Implementation is required on the homeserver, with client support for configuring the settings.
Client support is not required once setup.
