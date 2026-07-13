# MSC4004: Unified view of identity service

Centralized chat platforms are able to automatically detect which entries of
the phone address book are known by the platform, then automatically propose
those names when user clicks on "new discussion".

The Matrix-Identity-Service has already a secured mechanism able to be used
for this _(lookup)_. However, the identity service is only able to answer
with data it knows _(ie submitted lookups)_.

## Proposal

The goal of this proposal is to add a mechanism to provide an unified
view of identity service without centralizating user's data.

### Changes

All of this changes affects [identity-service-api.md](https://github.com/matrix-org/matrix-spec/blob/main/content/identity-service-api.md)

#### Association lookup

##### GET `/_matrix/identity/v2/hash_details`

To ensure continuity of asociations when the pepper changes, it is required
to have more than one pepper available. To avoid breaking changes, the current
format is kept and an optional additional filed is provided:

```json
{
  "algorithms": [
    "none",
    "sha256"
  ],
  "lookup_pepper": "matrixrocks",
  "alt_lookup_peppers": ["oldmatrixrocks"]
}

```

##### POST `/_matrix/identity/v2/lookup`

A new key is added in response, `third_party_mappings`. It permits to the
identity service to answer that it doesn't know this 3PID but knows where
to find it:

```json
{
  "mappings": {
    "4kenr7N9drpCJ4AfalmlGQVsOn3o2RHjkADUpXJWZUc": "@alice:example.org"
  },
  "third_party_mappings": {
    "matrix.domain.com:8448": [
      "nlo35_T5fzSGZzJApqu8lgIudJvmOQtDaHtr-I4rU7I"
    ]
  }
}
```

The client application has to do a new lookup query to `matrix.domain.com:8448`.
The hash value given here isn't valid on this new server: the client application
has to calculate a new hash using pepper/alg from `matrix.domain.com:8448`.

#### Establishing associations

##### POST `/_matrix/identity/v2/lookups`

A new endpoint, reserved to trusted servers, will allow to declare a list
of hashes owned by the (trusted) server. Hashes are calculated using the
pepper of recipient server.

Request body:

```json
{
  "algorithm": "sha256",
  "pepper": "matrix_rocks",
  "mappings": {
    "matrix.domain.com:8448": [
      "nlo35_T5fzSGZzJApqu8lgIudJvmOQtDaHtr-I4rU7I"
    ]
  }
}
```

## Potential issues

To avoid conversation hijacking, only trusted server should be allowed to push
a list of owned hashes.

## Security considerations

This proposal is based on current Matrix-Identity-Service security mechanisms.
Only the new endpoint should accept request only from trusted server.
