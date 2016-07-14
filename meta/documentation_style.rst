Documentation Style
===================

A brief single sentence to describe what this file contains; in this case a
description of the style to write documentation in.

Format
------

We use restructured text throughout all the documentation. You should NOT use
markdown (github-flavored or otherwise). This format was chosen partly because
Sphinx only supports RST.


Sections
--------

RST support lots of different punctuation characters for underlines on sections.
Content in the specification MUST use the same characters in order for the
complete specification to be merged correctly. These characters are:

- ``=``
- ``-``
- ``~``
- ``+``
- ``^``
- `````
- ``@``
- ``:``

If you find yourself using ``^`` or beyond, you should rethink your document
layout if possible.

TODOs
-----

Any RST file in this repository may make it onto ``matrix.org``. We do not want
``TODO`` markers visible there. For internal comments, notes, TODOs, use standard
RST comments like so::

  .. TODO-Bob
    There is something to do here. This will not be rendered by something like
    rst2html.py so it is safe to put internal comments here.

You SHOULD put your username with the TODO so we know who to ask about it.

Line widths
-----------

We use 80 characters for line widths. This is a guideline and can be flouted IF
AND ONLY IF it makes reading more legible. Use common sense.
