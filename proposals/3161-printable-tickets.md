# MSC3155: Printable tickets for Matrix

This proposal specifies how can a printable ticket be made to invite users and/or knock into a room.

## The data specification

### 2D barcode

Printable tickets shall feature Aztec codes with 21 layers (99×99). The barcode shall be printed in the
dark-on-light colour scheme, however, if the ticket is printed in a light sensitive medium like a photo
film, the light-on-dark scheme is also allowed. The check word amount shall be set as 

## The paper layout

The printing resolution should allow the Aztec code to be printed in a manner that each pixel can be mapped
to an integral number of dots without breaking the squareness of the pixels.

### The large format (210×74mm)


### The small format (54×89mm)



## Alternatives


## Security considerations

## Unstable prefix

No unstable prefix required, as this proposal does not affect any communication data unit.
