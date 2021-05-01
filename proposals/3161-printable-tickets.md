# MSC3161: Printable tickets for Matrix

This proposal specifies how can a printable ticket be made to invite users and/or knock into a room.

## The data specification

### 2D barcode

Printable tickets shall feature Aztec codes with 21 layers (99×99). The barcode shall be printed in the
dark-on-light colour scheme, however, if the ticket is printed in a light sensitive medium like a photo
film, the light-on-dark scheme is also allowed. The check word amount shall be set as the smallest number
possible that is greater than 25% of the data words.

### Data to be embedded within barcode



## The paper layout

The printing resolution should allow the Aztec code to be printed in a manner that each pixel can be
mapped to an integral number of dots without breaking the squareness of the pixels. In both large and
small formats, the Aztec barcode should be sized at 49.5×49.5 millimetres with a 0.25 millimetres wide
quiet zone around it (the actual quiet zone is larger due to the placement of the barcode in the
layout). This means each pixel of the barcode will occupy 0.5×0.5 millimetres.

### The large format (210×74mm)

This format is intended for easy mass production in the types of large ticket printers that are used
at the turnstiles and ticket offices of airports, railway stations and the stadiums. Can also be easily
at home printers by printing into A4 and cutting it into 4 equal pieces longitudinally.

### The small format (54×89mm)

This format is intended for production in the barcode reading handheld terminals with ticket printers.

In this format, the barcode is placed such that the edge of the Aztec code lies 2 millimetres from
the top margin, and the barcode is laterally centred. Following a 2.75 millimetre blank zone below
the Aztec code, the room name shall be printed in bold, followed by the room ID in italics after
a line break, then the room description after another line break, then the inviter/knock request creator
of the ticket after yet another line break, respectively. The font to be used is Helvetica/Arial in 8pt.

## Alternatives


## Security considerations

## Unstable prefix

No unstable prefix required, as this proposal does not affect any communication data unit.
