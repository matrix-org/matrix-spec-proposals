Abstract
========

Matrix does not define how to send rich text messages. This proposal defines a
format for ``m.room.message`` which allows it to send rich text messages.
This proposal is not designed to replace the existing system for sending images,
audio, files, etc though there is some overlap which would allow it to do so.


Current State
=============

The current unofficial way to send HTML messages uses the format::


    "type": "m.room.message",
    "content": {
        "body": "[matrix-org/matrix-ios-sdk] giomfo pushed to master: Handle new events notification  - https://github.com/matrix-org/matrix-ios-sdk/commit/c21e91a3",
        "format": "org.matrix.custom.html",
        "formatted_body": "[matrix-org/matrix-ios-sdk] giomfo pushed to <b>master</b>: Handle new events notification  - https://github.com/matrix-org/matrix-ios-sdk/commit/c21e91a3",
        "msgtype": "m.text"
    }

This works but has several problems with it:
 - It assumes the client can display HTML. If they cannot, there is no
   alternative representation other than plain text.
 - It doesn't provide support for textual representations of things which HTML
   isn't great at (e.g. formatting for math equations).
 - It doesn't account for HTML sanitizers very well. What you put in
   ``formatted_body`` may look *vastly different* depending on the strictness of
   the HTML sanitizer used.

Proposal
========

A new ``msgtype`` to ``m.room.message`` is added: ``m.rich_text``. Messages with
this type MUST include an ``html`` key which is a string. Messages MAY include a
``formats`` key which is an array of objects. Each object in ``formats`` MUST
have a ``mimetype`` key whose value is a valid mimetype. Mimetypes which start
with ``text/`` MUST have a ``body`` key. Mimetypes which do not start
with ``text/`` can have type-specific keys. The ``formats`` array is ordered so
that the preferred format appears first and the least preferred format appears
last. Clients will loop through this array and display the first format they
recognise. The ``html`` key MUST have an HTML representation of the message as
the value.


Example::

  content: {
      msgtype: "m.rich_text",
      formats: [
        {
            mimetype: "text/x-rst",
            body: "A **big** :green:`green` boat"
        },
        {
            mimetype: "text/markdown",
            body: "A **big** green boat"
        }
      ],
      html: "A <b>big</b> <font color=\"green\">green</font> boat"
      body: "A big green boat"
  }


Rationale
=========

There are many different ways of marking up some text. Not all clients can use
the same representation when marking up. HTML was chosen as the fallback rich
text format because it is the most commonly supported markup language for
devices / languages. This means that many libraries already exist for
converting from HTML to some UI display. In addition, HTML is
one of the most expressive markup languages: allowing pixel-perfect layouts, a
wide range of styling options, etc. This means that information loss can be
minimised in this representation. If we do not specify ``html`` as a required
key (and instead rely on clients setting it as an object in ``formats``) we
cannot ensure the largest amount of clients seeing the most accurate form of the
message. This can fragment the UX depending on the client being used.

The ``formats`` array was chosen to allow senders to specify a variety of
alternative representations for the text in question. This may be preferable
if the client cannot (or is unwilling to) display untrusted HTML. An array was
chosen over say ``"mime/type": "text"`` mappings because the sender may wish to
have several alternative representations using the same mimetype. As the
elements in this array are ordered, subsequent elements are effectively the
"fallback" for the previous element.

