# MSC3087: Standardised extensions

Currently, there is a Matrix specification, which comprises of two main 
documents and many supplemental addenda. The protocol itself is designed
to be easily extensible, however, there is currently a gap between spec
and implementation defined extensions. This defines a new RFC process
akin to the one we have on MSCs, with a few differences:

* Standardised extensions are named MX-EXT-# (EXT-# in short) instead of
MSC#.
* Standardised extensions are entirely optional.
* The reserved prefix for standardised extersions is `m.ext#`.
* As extensions are entirely optional, there is no requirement of unstable
prefix.

Extensions may be promoted for full standardisation, and MSCs can be demoted
to MX-EXTs likewise. Extension-to-RFC process works like follows:

* A standardised extension is eligible for conversion if it is implemented
by at least two clients or two servers or one client and one server.
* An extension with a conversion proposal earns an extended FCP after its
language and property namespace is adjusted accordingly.
* `m.ext` cannot be used as a stable prefix of a feature introduced in an MSC.

Standardised extensions are intended to be standalone and not a part of the
spec.
