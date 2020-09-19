# MSCXXXX: Homeserver Migration Data Format

This MSC proposes a specification of a data format for homeservers to export into, and other
homeservers to import from.

This could counter potential "lock-in" and allow easy domain re-use, and more importantly;
transparent migration between homeserver implementations.

## Proposal

The matrix spec should define an abstract resource/data format which homeservers can export their internal data into.

This data format should be extendable, ensuring that implementation-specific details can be additionally caught by other implementations, should these details not yet have been formalized into specification.

For example, this specification can be as simple as a gzipped-folder with the following structure;

```text

+- manifest.json
|
+- m.core.json
|
+- m.events/
|  +- events.1.cbor
|  +- events.2.cbor
|  +- events.3.cbor
|  [...]
|
+- m.users/
|  +- users.1.cbor
|  +- users.2.cbor
|  [...]
|
+- org.matrix.synapse/
|  +- admin_data.json
|  +- community_data.json
|
+- org.matrix.msc.9876/
   +- locations_index.idx
   +- locations.cbor

```

With a manifest in the following format:

```json
{
  "version": 1,
  "items": {
    "m.core": {
      "v": 1
    },
    "m.events": {
      "v": 2
    },
    "m.users": {
      "v": 3
    },
    "org.matrix.synapse": {
      "v": [1, 19, 2],
      "_": {
        "admin": true,
        "community": true,
      }
    },
    "org.matrix.msc.9876": {
      "v": 98,
      "_": {
        "world_backup": true
      }
    }
  }
}
```

(This is just an example, but it can show the extendability of the format)

Having a common format to work with, which can be extended to include implementation-specific details, proposals, or other non-spec data which can then be persisted.

This also allows implementations or organizations external to matrix.org to work with own supplemental data formats for implementation or domain-specific data persisted in matrix.

## Potential issues

Forward-compatibility is a huge note, as exports are versioned, and non-spec keys could exist for a long time, a fairly lossless process must be applied to ensure that older formats (within reason) can be resolved with ease.

This includes when adjusting keys (from `org.matrix.` to `m.`), this process should be transparent to import resolvers.

## Alternatives

One alternative proposed to abstracting migration is to write and maintain one-way one-time migration scripts, which would convert a homeserver's database into another's.

This, if accepted as a standard, will probably become only more impractical once times goes on, as then multiple scripts targeting multiple homeservers with multiple versions (with multiple own versions to take into account) should be maintained as an alternative.

## Security considerations

The exported file contains all possible data a homeserver can have in an easily-indexable format. Breach risk is about the same as a full database copy of the original homeserver, plus all additional files (such as the signing key, and e2ee device information.)
