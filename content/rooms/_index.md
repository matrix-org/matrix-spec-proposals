---
title: Room Versions
type: docs
weight: 60
---

Rooms are central to how Matrix operates, and have strict rules for what
is allowed to be contained within them. Rooms can also have various
algorithms that handle different tasks, such as what to do when two or
more events collide in the underlying DAG. To allow rooms to be improved
upon through new algorithms or rules, "room versions" are employed to
manage a set of expectations for each room. New room versions are
assigned as needed.

There is no implicit ordering or hierarchy to room versions, and their
principles are immutable once placed in the specification. Although
there is a recommended set of versions, some rooms may benefit from
features introduced by other versions. Rooms move between different
versions by "upgrading" to the desired version. Due to versions not
being ordered or hierarchical, this means a room can "upgrade" from
version 2 to version 1, if it is so desired.

## Feature matrix

Some functionality is only available in specific room versions, such
as knocking. The table below shows which versions support which features
from a client's perspective. Server implementations are still welcome
to reference the following table, however the detailed per-version
specifications are more likely to be of interest.

<!--
Dev note: When the room version columns get overwhelming, merge versions
1 through 6 as "1 ... 6" or similar given they don't add any features.

Alternatively, consider flipping the column/row organization to be features
up top and versions on the left.
-->

| Feature \ Version | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|-------------------|---|---|---|---|---|---|---|---|---|
| **Knocking**      | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✔ | ✔ | ✔ |
| **Restricted join rules** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✔ | ✔ |

## Complete list of room versions

Room versions are divided into two distinct groups: stable and unstable.
Stable room versions may be used by rooms safely. Unstable room versions
are everything else which is either not listed in the specification or
flagged as unstable for some other reason. Versions can switch between
stable and unstable periodically for a variety of reasons, including
discovered security vulnerabilities and age.

Clients should not ask room administrators to upgrade their rooms if the
room is running a stable version. Servers SHOULD use **room version 6** as
the default room version when creating new rooms.

The available room versions are:

-   [Version 1](/rooms/v1) - **Stable**. The current version of most
    rooms.
-   [Version 2](/rooms/v2) - **Stable**. Implements State Resolution
    Version 2.
-   [Version 3](/rooms/v3) - **Stable**. Introduces events whose IDs
    are the event's hash.
-   [Version 4](/rooms/v4) - **Stable**. Builds on v3 by using
    URL-safe base64 for event IDs.
-   [Version 5](/rooms/v5) - **Stable**. Introduces enforcement of
    signing key validity periods.
-   [Version 6](/rooms/v6) - **Stable**. Alters several
    authorization rules for events.
-   [Version 7](/rooms/v7) - **Stable**. Introduces knocking.
-   [Version 8](/rooms/v8) - **Stable**. Adds a join rule to allow members
    of another room to join without invite.
-   [Version 9](/rooms/v9) - **Stable**. Builds on v8 to fix issues when
    redacting some membership events.

## Room version grammar

Room versions are used to change properties of rooms that may not be
compatible with other servers. For example, changing the rules for event
authorization would cause older servers to potentially end up in a
split-brain situation due to not understanding the new rules.

A room version is defined as a string of characters which MUST NOT
exceed 32 codepoints in length. Room versions MUST NOT be empty and
SHOULD contain only the characters `a-z`, `0-9`, `.`, and `-`.

Room versions are not intended to be parsed and should be treated as
opaque identifiers. Room versions consisting only of the characters
`0-9` and `.` are reserved for future versions of the Matrix protocol.

The complete grammar for a legal room version is:

    room_version = 1*room_version_char
    room_version_char = DIGIT
                      / %x61-7A         ; a-z
                      / "-" / "."

Examples of valid room versions are:

-   `1` (would be reserved by the Matrix protocol)
-   `1.2` (would be reserved by the Matrix protocol)
-   `1.2-beta`
-   `com.example.version`

