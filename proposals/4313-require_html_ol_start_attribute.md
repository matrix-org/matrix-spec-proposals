# MSC4313: Require HTML `<ol>` `start` Attribute support

The Matrix specification allows text messages to optionally contain a HTML-formatted version over the plain text
body.
A set of "safe" tags [is recommended](https://spec.matrix.org/v1.17/client-server-api/#mroommessage-msgtypes),
along with a set of "safe" attributes for some of the tags that support them. 
Additional Matrix-specific attributes are also introduced.
However, all of this is optional on any level:

Clients may choose for example to

- not implement sending or showing or HTML-formatting at all
- only implement some tags
- implement additional tags outside of the existing recommendation

This can lead to problems in terms of interoperability:
If a sending client sends certain markup that implies some information, and a receiving client does
not support that markup, removing it as it displays the message, then the received message is not
complete and thus has possibly altered meaning.

Specifically, over the last decade of Matrix, clients have repeatedly had issues with ordered lists.

The key words “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”,
and “OPTIONAL” in this document are to be interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).


## Proposal

Imagine the following conversation to illustrate:

Alice asks a question, giving multiple options.
How these are formatted is not relevant to this example, important is
instead that they can clearly be referenced by number.

```
1. <a very long option>
2. <another very long description>
3. <a huge third description>
```

Bob replies very minimally, using the number indices Alice conveniently provided:

```
2.
```

Let's assume Bob's client takes the option to translate the plain text `2.` to HTML.
Assuming further that Bob's client has full support to the extent recommended by the spec, then Bob's
message becomes `"formatted_body": "<ol start=\"2\"><li></li></ol>"`, i.e. an ordered ("numbered") list with a single,
empty entry, that starts at an index of two.

Let's assume Alice's client also implements HTML markup in a configuration allowed by the spec:
Her client supports `ol` tags, but not the `start` attribute.
A common implementation is to parse the HTML and simply remove any tags not implemented by the client.
After safely ingesting the message, Alice's client ends up with `"formatted_body": "<ol><li></li></ol>"`.
Rendering this, Alice's screen shows:

Bob said:

```
1.
```

This is a clear break in communication, since this message has an entirely different meaning not only
from Bob's intended meaning, but also as it is viewed from different client implementations.

This MSC proposes to alter the spec such that a client implementing rendering of the `ol` HTML tag
in `formatted_body`s MUST also implement its `start` attribute, in order to prevent
loss of meaning of a message.


## Potential issues

This proposal increases the load on client developers (though presumably only a tiny bit),
which could mean that fewer clients could choose to implement `ol` at all.


## Alternatives

- Define a list of all HTML tags whose displaying must be supported if `formatted_body` is used to display
  messages at all, based on whether tags can replace characters such as in the demonstrated example.
  This could apply recursively also for all attributes.
- Find a way for clients to determine whether the `body` matches its supported interpretation of the
  `formatted_body`.
  This could end up very similar to the previous alternative and additionally lead to inconsistent
  behavior on clients where `formatted_body` is only sometimes used for display as a result.
- Remove HTML from the spec entirely. Possibly replace it with another markup language that prevents
  this issue.


## Security considerations

No potential security issues are known to the author.
We are only defining more precisely combinations of options that are already allowed, removing some of them.


## Unstable prefix

Not required, since implementations of this MSC would only allow an existing subclass of the currently legal
HTML-formatted messages.


## Dependencies

None.
