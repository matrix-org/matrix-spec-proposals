#!/usr/bin/env python3
#
# Validates the Python canonicaljson encoder implementation, https://pypi.org/project/canonicaljson/.
#
# To run:
#   python -m venv env
#   . env/bin/activate
#   pip install canonicaljson
#   ./test.py

import sys
from typing import Any

import canonicaljson
import os
import json

TEST_DATA_DIR: str = os.path.join(os.path.dirname(__file__), "testcases")


def encode_canonical_json(data: Any) -> bytes:
    """This is the function under test. It should encode the given data as Canonical JSON.

    If the data cannot be legally represented as Canonical JSON, it should throw an exception.

    Ideally, we would simply call `canonicaljson.encode_canonical_json`; however,
    the python canonicaljson encoder doesn't actually confirm to the spec unless
    you first verify that there aren't any unsupported types, so we have to implement a separate validation step.
    """
    validate_canonicaljson(data)
    return canonicaljson.encode_canonical_json(data)


def validate_canonicaljson(value: Any) -> None:
    """
    Ensure that the JSON object is valid according to the rules of canonical JSON.

    This rejects JSON that has:
    * An integer outside the range of [-2 ^ 53 + 1, 2 ^ 53 - 1]
    * Floats
    * NaN, Infinity, -Infinity

    From synapse: https://github.com/element-hq/synapse/blob/3622579e7bc9fe70d3682bc20bb4955fbb0c9e82/synapse/events/utils.py#L487-L516
    """
    # Max/min size of ints in canonical JSON
    CANONICALJSON_MAX_INT = (2**53) - 1
    CANONICALJSON_MIN_INT = -CANONICALJSON_MAX_INT

    if type(value) is int:  # noqa: E721
        if value < CANONICALJSON_MIN_INT or CANONICALJSON_MAX_INT < value:
            raise Exception("JSON integer out of range")

    elif isinstance(value, float):
        # Note that Infinity, -Infinity, and NaN are also considered floats.
        raise Exception("Bad JSON value: float")

    elif isinstance(value, dict):
        for v in value.values():
            validate_canonicaljson(v)

    elif isinstance(value, (list, tuple)):
        for i in value:
            validate_canonicaljson(i)

    elif not isinstance(value, (bool, str)) and value is not None:
        # Other potential JSON values (bool, None, str) are safe.
        raise Exception("Unknown JSON value")


def verify_testcase(filename: str) -> None:
    # Break the file into sections at the "---" boundary.
    # The first section is the input; the second half lists acceptable outputs, one per line
    with open(filename, "rb") as f:
        content = f.read()

    sections = content.split(b"---\n", 1)

    # In the input, lines beginning '#' are comments and should be removed
    input_json = b"".join(
        filter(
            lambda line: not line.startswith(b"#"),
            sections[0].splitlines(keepends=True),
        )
    )

    acceptable_outputs = sections[1].splitlines()

    parsed = json.loads(input_json)
    try:
        canonical_json = encode_canonical_json(parsed)
    except Exception as e:
        canonical_json = b"REJECT"

    if canonical_json not in acceptable_outputs:
        print(
            f"""\
Testcase {filename} failed
--------------------------

Input:
{input_json.decode(errors="replace")}

Parsed input:
{parsed}

Canonicalised output:
{canonical_json.decode()}

Acceptable outputs:
{"\n".join(map(lambda o: o.decode(), acceptable_outputs))}\
""",
            file=sys.stderr,
        )
        sys.exit(1)


for file in os.listdir(TEST_DATA_DIR):
    verify_testcase(os.path.join(TEST_DATA_DIR, file))

print("OK")
