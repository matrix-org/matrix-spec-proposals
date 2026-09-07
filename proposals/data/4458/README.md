Test vectors for Canonical JSON encoders
----------------------------------------

This is supporting data for [MSC4458](https://github.com/matrix-org/matrix-spec-proposals/pull/4458): it contains an
extended set of test vectors for Canonical JSON encoders.

The test data itself is contained in the `testcases` directory. Each file is a single testcase, and has the format
described below.

A script which goes through the test vectors and verifies the Python canonicaljson implementation is provided as 
`test.py`.

## Testcase file format

Each testcase file has two parts, separated by a line containing (only) `---`.

The first part is the input data: it is data that might be received in the body of a federation request or response:
in other words, it is JSON-encoded data. Within this section, lines starting with `#` are comments and should be
ignored.

The second part lists acceptable encodings of the input data as Canonical JSON, one per line. In some cases
(such as objects with duplicate keys), there are multiple acceptable encodings of the given data. The special value
`REJECT` is used to indicate rejection of the input data (either during initial parsing, or during canonicalisation).
