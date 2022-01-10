# Marking up resources

This MSC proposes a way to annotate and discuss various resources (web pages, documents, videos, and other files) using Matrix. The general idea is to use [Spaces (MSC1772)](https://github.com/matrix-org/matrix-doc/pull/1772) to represent a general resource to be annotated, and then a combination of child rooms and [Extensible Events (MSC1767)](https://github.com/matrix-org/matrix-doc/blob/matthew/msc1767/proposals/1767-extensible-events.md) to represent annotations and discussion. This MSC specifies:

* Additional data in the `m.room.create` event to mark a space as describing  a resource to be annotated.
* Additional (optional) data in the `m.space.child` and `m.space.parent` events to mark sections of the resource (pages, timestamps, etc.) that are being discussed by the child room. The specific format of the location data is resource-specific, and will be described in further MSCs.
* An annotation event that is used within child rooms. The specific data describing the annotation location is once again resource-specific, and will be described in further MSCs.

Resources and markup can be displayed in specialized annotation-aware clients, and potentially in a widget or widget-like interface for widget-compatible clients, although the latter possibility remains speculative. The use of extensible events and standard space events should provide for a reasonable degree of compatibility with general-purpose matrix clients.

# Proposal

## Additional data in `m.room.create`

A space will be considered a *resource* if its creation event includes a key `m.markup.resource`. 

The `m.markup.resource` value MUST include either:

1. an `m.file` key, populated according to the `m.file` schema as presented in [Extensible Events - Files (MSC3551)](https://github.com/matrix-org/matrix-doc/blob/travis/msc/extev/files/proposals/3551-extensible-events-files.md), or
2. a `url` and `mimetype` key. This format is preferred for potentially mutable resources (like web pages with dynamic content) or for resources that require multiple network requests to display properly.

Clients should recognize that a `url` subordinate to an `m.markup.resource` (including within an `m.file` value) may contain URI schemes other than `mxc`. It may contain `http(s)`, and may ultimately contain other schemes in the future. Clients handling `m.markup.resource` should be prepared to fail gracefully upon encountering an unrecognized scheme.

An optional `sha256_hash` key may be included. If present, this key should be populated by a sha256 hash of the resource, for file-integrity checking.

### Examples

#### A hypothetical web resource

```
{
    "type": "m.room.create",
    "state_key": "",
    "content": {
           "creator": "@example:example.org",
           "m.federate": true,
           "room_version": "7"
           "m.markup.resource": {
             "url": "https://danilafe.com/blog/introducing_highlight/"
             "mimetype": "text/html"
           }
        }
    }
}
```


## Additional data in `m.space.child` and `m.space.parent`

Children of resources will be considered *conversations concerning* the resource. For purposes of discoverability,  may sometimes be helpful to attach additional data to the content of `m.space.child` and `m.space.parent` events, in order to indicate a specific part of the resource that the conversation is based upon. The location of the part of the resource that the conversation is based upon will be indicated by the value of an `m.markup.location` key within the contents of the `m.space.child` and/or `m.space.parent` event.

Different mimetypes will require different notions of "location". A need for new notions of location may become evident over time. For example PDFs begin with a need to specify highlighted regions and then at a later date, pindrop locations. One location might also reasonably be presented in two or more different ways. For example, in a PDF, a location might be presented both as coordinates designating a region of a page, and as a tag or set of tags with offsets for use with a screen reader. In an audio file, a location might be presented both as a pair of bounding timestamps and as a pair of offsets within the text of embedded lyrics.

Hence, the `m.markup.location` value MUST be an object, whose keys are different kinds of locations occupied by a single annotation, with the names of those locations either formalized in the matrix spec or namespaced using Java conventions. Some proposed location types are described in:

- [MSC3592: Markup locations for PDF documents)[https://github.com/matrix-org/matrix-doc/pull/3592]

### Examples

#### A hypothetical audio annotation:

```
{
    "type": "m.space.child",
    "state_key": "!abcd:example.com",
    "content": {
        "via": ["example.com", "test.org"]
        "m.markup.location": {
           "m.markup.audio_timespan" {
               "begin": 0
               "end": 31983
           }
           "com.genius.markup.lyrics" {
               "begin": 0
               "end": 35
           }
        }
    }
}
```

## Annotation Message Events

It may be desirable, within a conversation concerning a resource, to make reference to some part of the resource. Annotation message events make this possible.

An annotation message event will treat `m.markup` as an extensible event schema following [Extensible events (MSC1767)](https://github.com/matrix-org/matrix-doc/pull/1767), but the message will ordinarily include an `m.text` value with text optionally describing the annotation as a fallback. The `m.markup` value will consist of an `m.markup.location`, and an `m.markup.parent` that indicates the room id of the resource with which the annotation message is associated. (The latter is necessary when a room has more than one parent resource.) Until migration to extensible events is complete, annotations will send messages of the type `m.room.message`, for compatibility with non-annotation-aware clients.

### Examples

#### An annotation prior to MSC1767 adoption


```
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.emote",
        "body": "created an annotation",
        "org.matrix.msc1767.text": "created an annotation",
        "m.markup": {
            "m.markup.location": {..}
            "m.markup.parent": "!WKZqabcAWoDDNZzupv:matrix.org"
        }
    }
}
```

#### An annotation after MSC1767 adoption and migration


```
{
    "type": "m.markup",
    "content": {
        "m.text": "created an annotation",
        "m.emote": {}
        "m.markup": {
            "m.markup.location": {..}
            "m.markup.parent": "!WKZqabcAWoDDNZzupv:matrix.org"
        }
    }
}
```

# Potential Issues

There's no notion of "ownership" for state events---anyone who can send `m.space.parent` events can overwrite `m.space.parent` events sent by others. So anyone who can create a conversation concerning a certain resource can also remove conversations created by others. Clients can partly mitigate this by at least discouraging accidental deletions and encouraging courtesy. A more robust mitigation might be to introduce subspaces of resources, within which less-trusted users could still create conversations concerning a given resource. However, this seems undesirably complicated for an initial implementation. If it turns out to be necessary in practice, it could be added in a future MSC.

# Alternatives

## Greater generality

The idea of attaching conversations to locations might be construed even more broadly, to incorporate spaces representing resources that aren't easily associated with mimetypes and urls. For example, someone might want to create a space with rooms located at some sort of geospatial region, or located during some time-slice of an event. 

However, these more abstract cases can be subsumed under the design here. Geospatial data can be represented using something like [geojson](https://en.wikipedia.org/wiki/GeoJSON) or some other standard, and time-slices of events can be represented as locations within a recording of the event (or locations within some other representation of the event, if no recording is available).

## Resources as a space type or subtype

Resources could be designated as such using an `m.purpose` event, as in [Room subtyping (MSC3088)](https://github.com/matrix-org/matrix-doc/blob/travis/msc/mutable-subtypes/proposals/3088-room-subtyping.md), or with an `m.room.type` event as in [Room Types (MSC1840)](https://github.com/matrix-org/matrix-doc/pull/1840). 

However, 

1. Indicating an associated resource in the room creation event makes it possible to inspect an invitation to a new space, allowing annotation-oriented clients to ignore irrelevant invitations.
2. If `m.purpose` or `m.room.type` are integrated into the spec and turn out to be useful for, e.g. filtering, then it would be straightforward to designate one or more `m.purpose` values or `m.room.type` values for resource rooms.

## Standalone `m.annotation.location` state events

Rather than being represented by `m.space.child` events, annotations that open a conversation concerning a part of a resource could be introduced as a new kind of state event. This has the disadvantage of not making relationships between a resource and conversations about its parts visible to clients which are space-aware but not annotation-aware.

## Discussions as threads

Discussions concerning a part of resource could be modeled as threads rooted in `m.markup` message events, using [Threading via `m.thread` relation (MSC3440)](https://github.com/matrix-org/matrix-doc/pull/3440). The current proposal is intended to be compatible with clients that model discussions this way, since those clients are free to build threads rooted in `m.markup` events and display these however they like. However, an alternative approach to marking up resources would be to *only* introduce `m.markup` events, and expect all clients to follow a thread-based model.

Instead, the current proposal also provides the option of modeling discussions concerning a resource as standalone rooms. There are a number of advantages to this choice. Discussions modeled as rooms inherit:

* Unread counts and read-up-to-markers
* Typing notifications
* Fine-grained access controls (for e.g. a private discussions of a part of a resource)
* Conversation threading (since MSC3440 doesn't allow nested threads)

among other things.

The main disadvantage to allowing both models seems to be the possibility of fragmentation and incompatibility between annotation-aware clients. In practice, this seems unlikely to be a major problem.

# Security Considerations

## The Web Annotation Data Model

The [Web Annotation Working group](https://www.w3.org/annotation/) at the W3C has published a detailed set of recommendations for interoperable and shared web annotation. These include both [a data model](https://www.w3.org/TR/annotation-model/) and [a protocol](https://www.w3.org/TR/annotation-protocol/) for annotation servers. The fundamental idea of the annotation model is to view an annotation as a connection between zero or more "body" resources, annotating one or more "target" resources.

<img width="353" alt="intro_model" src="https://user-images.githubusercontent.com/6383381/148815059-b2f6350b-37aa-4926-95d7-4dd34f699492.png">

Targets are identified using a combination of an internationalized URI, and a set of [selectors](https://www.w3.org/TR/annotation-model/#selectors) (e.g. XPaths or CSS selectors) to pick out a part of the resource designated by the URI. Bodies can be identified in the same way, or embedded as formatted or unformatted text within the annotation.

Matrix could adopt a markup spec based on this set of recommendations, and focus on annotations that link targets, potentially specified via `mxc://` or `matrix://` uris, to bodies, potentially presented as `matrix://` or `mxc://` uris. Annotations could be sent in timelines as extensible events, and in resource spaces meant to collect sets of annotations - roughly corresponding to the w3c's concept of [annotation collections and pages](https://www.w3.org/TR/annotation-model/#collections). Downstream, it's conceivable that annotation servers speaking the w3c annotation protocol with a matrix backend could be implemented as app services.

Some advantages of this proposal are:

1. In principle, using a w3c spec should support greater interoperability with other annotation systems, as well as better exportability, archivability, machine-readability...
2. The w3c spec is detailed and includes features (a notion of annotation state, accessibility attribution, rendering advice...) that go considerably beyond what this MSC proposes, and whose inclusion into the matrix spec proper might feel like bloat.
3. The w3c spec is broad enough to support the functionality provided by this MSC, but also supports some other functionality (i.e. annotations with embedded bodies, annotations linking to standalone content in or out of matrix).

Some disadvantages are:

1. In practice, near-term prospects for interoperability might be limited. There are not many [implementations](https://w3c.github.io/test-results/annotation-model/all.html) in the wild. Even, for example, Hypothes.is supports only part of the w3c data model, and [apparently only in an undocumented read-only capacity](https://github.com/hypothesis/h/blob/28c2c5bdf5d85f12307ed56f90995ad1c1f214ac/h/routes.py#L122). If desired, bridging might be better accomplished by using APIs for individual annotation services directly, rather than by routing through an incompletely supported data model.
2. The w3c spec's selectors for PDF annotation are somewhat limited, and more generally the set of selectors built into the spec are not likely to cover all use cases. The w3c spec does incorporate [an extension mechanism](https://www.w3.org/TR/annotation-vocab/#extensions), via JSON-LD contexts. Perhaps the matrix spec for document markup would want to eventually incorporate a well-documented JSON-LD context for any extended selector types that become important.

# Security Considerations - 

None.

# Unstable Prefix

| Proposed Final Identifier | Purpose                                                    | Development Identifier                    |
| ------------------------- | ---------------------------------------------------------- | ----------------------------------------- |
| `m.markup.location`       | key in `m.space.child`, `m.space.parent` and `m.annotation`| `com.open-tower.msc3574.markup.location`   |
| `m.markup.resource`       | key in `m.create`                                          | `com.open-tower.msc3574.markup.resource`   |
| `m.markup`                | extensible event schema                                    | `com.open-tower.msc3574.markup`            |
| `m.markup.parent`         | key in `m.annotation`                                      | `com.open-tower.msc3574.markup.parent`     |
