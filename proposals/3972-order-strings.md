# MSC3972: Lexicographical strings as an ordering mechanism

This MSC relates to [MSC1772](https://github.com/matrix-org/matrix-spec-proposals/pull/1772) and [MSC3230](https://github.com/matrix-org/matrix-spec-proposals/pull/3230).

There are places in the spec where clients need to allow users to provide their own ordering of entities.
Spaces are an example of this.

The existing MSCs currently specify a string consisting of no more than 50 characters
and ascii characters in the range \x20 (space) to \x7E (~).
This is very easy to consume but non trivial to generate.
The existing implementations take the obvious route of converting the lexicographical strings to numbers,
performing the generative operation with the numbers, then converting the numbers back to strings.

The particurlarly non-trival part of this process is the conversion and the existing implementations are correct enough to
work most of the time but not 100%. The incorrectness shows up in the form of gaps and/or collisions.

This MSC provides an algorithm to correctly convert between lexicographical strings and numbers.

## Proposal

For the sake of simplicity, I will be limiting the range of characters to be just A, B and C with a limit of 3 characters.
The important conditions are that the range of characters are continguous in the ascii table and that there is a limit.
These conditions will be defined as a "Dictionary" for the rest of this MSC.

The mapping this algorithm aims to provide is shown in the dictionary below.
Note: The table is truncated and the first row represents an empty (but non-null) string.

| Word | Index in dictionary |
|------|------|
|      | 0    |
|A     | 1    |
|AA    | 2    |
|AAA   | 3    |
|AAB   | 4    |
|AAC   | 5    |
|AB    | 6    |
|ABA   | 7    |
|ABB   | 8    |
|ABC   | 9    |
|AC    | 10   |
|ACA   | 11   |
|ACB   | 12   |
|ACC   | 13   |
|B     | 14   |
|BA    | 15   |
|BAA   | 16   |
|BAB   | 17   |
|BAC   | 18   |
|BB    | 19   |
|BBA   | 20   |
|BBB   | 21   |
|BBC   | 22   |
|...   | ...  |
|CCC   | ...  |

The algorithm will be base on geometric sums.
i.e. `(2^0) + (2^1) + (2^2) + (2^3) + (2^4) + ....`

To convert the string `"BAC"` to an index this formula can be used.

`length("BAC") + (idx('B') * geoSum(R, L - 0)) + (idx('A') * geoSum(R, L - 1)) + (idx('C') * geoSum(R, L - 2))`

where:
- `idx(c)` is the number of characters between `c` and the first character in the dictionary. i.e. `c - 'A'`.
- `R` is the number of possible characters. Using just A, B and C make `R = 3`.
- `L` is the maximum possible length of strings in the dictionary. For this example `L = 3`.
- `geoSum(P1, P2)` is the sum of the first `P2` powers of `P1`. i.e. `geoSum(3, 4) = (3^0) + (3^1) + (3^2) + (3^3)`

To convert an index to a string this algrorithm can be used.

```
function convertToString(index, range, limit, firstChar) {
    result = ""
    scopedIndex = index - 1
    for (i = 0; i < limit; i++) {
        if scopedIndex < 0 {
            break
        }
        scale = geoSum(range, limit - i)
        charIndex = scopedIndex / scale
        if charIndex >= range {
            return null // Index out of bounds
        }
        scopedIndex -= (charIndex * scale)
        scopedIndex -= 1
        result += firstChar + charIndex
    }
    return result
}
```

## Potential issues

When using these algorithms for the spec defined dictionary, the numbers can get very large,
much greater than the 64 bit integers that programming languages provide.
Implementations should be careful to appriopriatly handle these big numbers.

### Performance
The algorithms as represented above are about `O(n^2)` (where `n` is the length of the word in the dictionary)
but with some dynamic programming optimizations they can be written in `O(n)`.

## Alternatives

None
