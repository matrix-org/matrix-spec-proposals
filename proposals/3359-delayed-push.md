# MSC3359: Delayed Push

Mobile applications usually have to rely on a proprietary push provider for delivering messages to the phone they run on. These providers don't allow self-hosting, and aren't exactly known to respect the privacy of their users.

MSC3013 lays the groundwork for reducing the amount of information that the push provider sees, by hiding the room and event IDs from the push providers. While that is already a good step towards preventing profiling on the push provider side, they can still build social graphs based on timing analysis.

To further reduce the ability of profiling that the push providers continue to have, I propose that clients can configure a randomized delay when setting up the push provider, which is automatically added to pushes. This will not completely prevent profiling, but with enough traffic it will at least make it quite a bit harder and less accurate.

## Proposal


## Potential issues


## Alternatives


## Security considerations


## Unstable prefix

