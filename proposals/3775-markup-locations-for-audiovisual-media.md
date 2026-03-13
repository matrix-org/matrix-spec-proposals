# Markup Locations for Audiovisual Media

[MSC3574](https://github.com/matrix-org/matrix-spec-proposals/pull/3574)
proposes a mechanism for marking up resources (webpages, documents, videos, and
other files) using Matrix. The proposed mechanism requires an
`m.markup.location` schema for representing the location of annotations within
different kinds of resources. MSC3574 punts on what standard location types
might be available, deferring that large family of questions to other MSCs.
This MSC aims to provide basic location types for marking up audiovisual media
resources.

## Proposal

Basic markup locations for audiovisual media should make use of the [Media
Fragments URI specification](https://www.w3.org/TR/media-frags/). The media
fragment specification is quite simple, and results in annotations compatible
with the w3c's [web annotation data
model](https://www.w3.org/TR/annotation-model/).

Basic markup locations for audiovisual media should be applicable to `audio/*`,
`video/*` and `image/*` media types.

The basic media fragment specification addresses content along two dimensions:
temporal (in the form of a time interval), and spatial (in the form of a
rectangle of pixels in the original media). The specification also includes
support for addressing media by track (in the case of audio with multiple
parallel media streams, for example a secondary dubbed English-language audio
stream). We only make use of the temporal and spatial dimensions in this MSC.

Temporal locations consist of half-open intervals, specifying the first moment
included the location, and the first moment not included in the location. This
MSC will use milliseconds to represent moments. The Media Fragments URI
specification uses seconds with a decimal part. Spatial locations consist of
rectangular selections given by the x,y coordinates of the upper left corner
and the width and height of the rectangle. The coordinates and dimensions of
the rectangle can be indicated either with integers representing pixels (with
0,0 representing the top left corner of the image or video), or with integers
representing percentages of the width and height of the media. This MSC will
represent percentages with integers in [0,1000000], allowing for four decimal
points of accuracy. Temporal and spatial locations can be combined to select
spatio-temporal segments of video recordings.

### Media Fragments

Media Fragments will be represented as follows:

```
"m.markup.location": {
    "m.markup.media.fragment": {
        "start": ..
        "end": ..
        "x": ..
        "y": ..
        "w": ..
        "h": ..
    }
    ..
}
```

or (when spatial dimensions are given in percentages) as

```
"m.markup.location": {
    "m.markup.media.fragment": {
        "start": ..
        "end": ..
        "xp": ..
        "yp": ..
        "wp": ..
        "hp": ..
    }
    ..
}
```

with all fields optional, but with the requirement that at least one field is
present, and that if any of `xywh`  are present, then all are.

The `start` and `end` values should be non-negative integers with `start <
end`, where `start` indicates the first millisecond of media included in the
location, and `end` indicates the first millisecond of media not included. If
`start` is omitted, the location begins at zero, and if `end` is omitted, the
location includes the whole duration of the media.

The `xywh` fields should be non-negative integers describing a spatial region
within the media in pixel coordinates as described above. So `xy` should be
smaller than then [intrinsic height and width of the
video](https://html.spec.whatwg.org/multipage/media.html#concept-video-intrinsic-width)
respectively, and `wh` should be smaller than the difference between `x` and
the intrinsic width, and the difference between `y` and the intrinsic height,
respectively. In cases where the exception on `wh` is violated, the region
described should be clipped at the edges of the media. In the case where the
expectation on `xy` is violated, the location should be ignored as invalid.

The `xp` `yp` `wp` and `hp` fields should be non-negative integers less than or
equal to 1000000, giving a spatial region within the media in percentage
coordinates as described above. If either `xp` + `wp` or `yp` + `hp` is greater
than 1000000, then the location should be ignored as invalid.

### Web Annotation Data Model Serialization

[MSC3574](https://github.com/matrix-org/matrix-spec-proposals/pull/3574)
includes a scheme for serializing matrix markup events as web annotations in
the web annotation data model. The scheme requires each markup location type to
have a canonical serialization as [a web annotation
selector](https://www.w3.org/TR/annotation-model/#selectors]). In this section,
we describe how to serialize `m.markup.media.fragment` as a WADM selector.

We take advantage of the WADM's support for URI fragments as locations, using
the [FragmentSelector](https://www.w3.org/TR/annotation-model/#text-quote-selector)
selector.

This allows us to encode a location of the form

```
"m.markup.media.fragment": {
    "start": $START
    "end": $END
    "x": $X
    "y": $Y
    "w": $W
    "h": $H
}
```

as a selector

``` 
{
  "type": "FragmentSelector",
  "conformsTo": "http://www.w3.org/TR/media-frags/",
  "value": "t=($START/1000),($END/1000)&xywh=$X,$Y,$W,$H"
}
```

and 

```
"m.markup.media.fragment": {
    "start": $START
    "end": $END
    "xp": $X
    "yp": $Y
    "wp": $W
    "hp": $H
}
```

as

``` 
{
  "type": "FragmentSelector",
  "conformsTo": "http://www.w3.org/TR/media-frags/",
  "value": "t=($START/1000),($END/1000)&xywh=percent:($X/1000),($Y/1000),($W/1000),($H/1000)"
}
```

## Security considerations

Because room state is unencrypted, `m.space.child` events conveying locations
via `m.markup.media.fragment` could leak information about the duration and
dimensions of a piece of media. This is part of a more general problem with
state events potentially leaking information, and deserves a general
resolution, a la [MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414)


## Unstable prefix

| Proposed Final Identifier | Purpose                                                    | Development Identifier                        |
| ------------------------- | ---------------------------------------------------------- | --------------------------------------------- |
| `m.markup.media.fragment` | key in `m.markup.location`                                 | `com.open-tower.msc3775.markup.media.fragment`|
