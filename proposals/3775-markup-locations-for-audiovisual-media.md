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
0,0 representing the top left corner of the image), or with integers
representing percentages of the width and height of the media. Temporal and
spatial locations can be combined to select spatio-temporal segments of video
recordings.
