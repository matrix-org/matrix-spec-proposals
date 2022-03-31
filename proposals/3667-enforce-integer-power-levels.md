# MSC3667: Enforce integer power levels

The spec defines power levels in `m.room.power_levels` events as integers, but due to legacy
behaviour in Synapse, string power levels are also accepted and parsed. The string parsing itself
is problematic because it is done using Python's [int()](https://docs.python.org/3/library/functions.html#int)
function, which has all sorts of associated behaviours:

> If x is not a number or if base is given, then x must be a string, bytes, or bytearray instance
> representing an integer literal in radix base. Optionally, the literal can be preceded by + or -
> (with no space in between) and surrounded by whitespace. A base-n literal consists of the digits 0
> to n-1, with a to z (or A to Z) having values 10 to 35. The default base is 10. The allowed values
> are 0 and 2–36. Base-2, -8, and -16 literals can be optionally prefixed with 0b/0B, 0o/0O, or 0x/0X,
> as with integer literals in code. Base 0 means to interpret exactly as a code literal, so that the
> actual base is 2, 8, 10, or 16, and so that int('010', 0) is not legal, while int('010') is, as
> well as int('010', 8).

All of this behaviour is exceptionally difficult for non-Python implementations to reproduce
accurately. 

## Proposal

In a future room version, we should enforce the letter of the spec and only allow power levels
as integers within the range defined by canonical JSON and reject events which try to define them as any other type. This removes all of the
associated headaches with string parsing.

## Potential issues

We can't avoid the string parsing behaviour altogether because we need to continue to do so for
existing room versions so that we do not break existing rooms. However, there are already documented
cases of this causing problems across implementations. For example, Synapse will accept `"  +2  "` as
a power level but Dendrite will outright fail to parse it.

## Alternatives

Event schema enforcement for all event types used in event auth could solve this problem and
more but is a significantly bigger task.

## Unstable prefix

An implementation exists in Dendrite using the `org.matrix.msc3667` room version identifier. The
experimental room version is based on room version 7, with the additional requirement that power
levels must be integers or the power level content will fail to unmarshal altogether.
