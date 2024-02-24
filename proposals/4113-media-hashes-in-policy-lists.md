# MSC4113: Image hashes in Policy Lists
Currently Policy lists are mainly focused on users, rooms and servers and not content. 
This proposal adds a fourth kind: Media. Especially this focuses on image media 
which can be hashed and compared using 
[Perceptual hashes](https://en.wikipedia.org/wiki/Perceptual_hashing).

The use for these are crowd-gathered hashlists for potentially bad media which 
allow people to then scan their media with and also block dangerous media.

## Proposal
The MSC proposes adding a state event called `m.policy.media_hash`.
The MSC recommends that the hash itself is used for the state_key as it 
should be sufficiently unique.

In the content of the event, there are expected to be hash implementation-specific 
values. Therefore the event has a mandatory typekey which differentiates the 
various types of hashes. Each of the types MUST follow the in matrix common java 
style namespace format. For example, a pdqhash type would look like `m.pdqhash` 
where `m` is your namespace and `pdqhash` is the hash type.

An object approach is chosen to make sure that in the future the events can be 
easily upgraded while staying backwards compatible with old implementations.
For example when there are issues with hash algos discovered in the future.

The reason field is expected like in the other policy events.

Recommendations might depend on thresholds that are implementation specific.
Hence these are nested in the hash implementation.
In some cases like pdqhashes they are also defined for the whole data and therefor
not included in the event as this would be not useful.

Such an event in full would look like this:

```json
{
  "content": {
    "m.pdqhash": {
      "hash": "d8f8f0cce0f4a84f0e370a22028f67f0b36e2ed596623e1d33e6b39c4e9c9b22",
      "quality": "100"
    },
    "reason": "Meow"
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "state_key": "d8f8f0cce0f4a84f0e370a22028f67f0b36e2ed596623e1d33e6b39c4e9c9b22",
  "type": "m.policy.media_hash"
}
```

### m.pdqhash
As an initial hash type, the [pdqhash algorithm](https://github.com/facebook/ThreatExchange/tree/main/pdq) 
is chosen due to ongoing implementations.

The pdqhash requires a minimum of the `hash` itself and the `quality` field 
for a comparison.

From the document itself:
- `Distance` Threshold to consider two hashes to be similar/matching: <=31
- `Quality` Threshold where we recommend discarding hashes: <=49

This means that for the hash type `m.pdqhash` the content MUST include at 
least these 2 fields: `hash` and `quality` for the implementation itself.

A `recommendation` field is not included as instead the implementation should define
global thresholds as suggested by https://github.com/facebook/ThreatExchange/tree/main/pdq#matching

## Potential issues
Since there might be multiple implementations there might be multiple hash types 
being used. There is currently no easy way to have a list of used type strings 
across matrix.

An action is hard to define and needs to be discussed as part of the MSC process. 
(Please attach a thread here). Ideally, we follow the recommendations given by the 
hashes. For example, pdqhash gives the above suggestions where the distance is a 
[hamming distance](https://en.wikipedia.org/wiki/Hamming_distance) between 2 hashes. 
If the threshold given causes a hit an admin should act. However, this does not 
account for various levels of media issues (CSAM and other kinds). It treats all 
of them as the same level of bad. Suggestions are welcome on this. 

## Security considerations

Some hash algorithms for perceptual hashes are prone to reversing attacks. 
While blurred this leads to images being visible quite well 
(See https://anishathalye.com/inverting-photodna/ for an example).

As a suggestion therefore it's recommended to at least not use the photodna 
algorithm in a CSAM media context to prevent the accidental spreading of such 
images even at lower quality.

Additionally, it's also important when implementing to ensure that the MXC URL 
is NOT included in the event. This can lead to unintentional spreading of the 
media itself or for people to actively use this to search find the media just 
before its being removed.

## Unstable prefix
As an unstable prefix, one should use `space.midnightthoughts.policy.media_hash` 
and `space.midnightthoughts.pdqhash`.
