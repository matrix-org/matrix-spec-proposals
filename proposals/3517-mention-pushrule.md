# MSC3517: Mention Pushrule

Pings in matrix can be inconsistent for someone coming from an environment where pings are explicit
(e.g. Discord, Telegram, Slack, Whatsapp, etc.)

Currently, personal pings are governed by 2 push rules; match on display name, and match on username.

However, due to a variety of reasons, these push rules can have false-positives, and a suitable
alternative that only gives notifications on explicit pings does not exist.

## Proposal

This proposal aims to change that, adding the following default push rule:

```json
{
    "rule_id": ".m.rule.pings_mxid",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "mxid_ping"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        },
        {
            "set_tweak": "highlight"
        }
    ]
}
```

And the following condition, `mxid_ping`, which is defined below.

### Triggering the rule

The process of determining if the `mxid_ping` condition should trigger is described with the following pseudocode;

```py

# event: the raw event, at least containing `type` and `content`
# mxid: the @-prefixed User ID (e.g. "@bob:example.com")
def should_trigger_mention(event: dict, mxid: str) -> bool:
    # 1. If an event type is m.room.message;
    if event.type == "m.room.message":
        content = event.content

        # 1.1. In event content, test if `body` is present and contains mxid substring, trigger if so.
        if "body" in content and content["body"].contains(mxid):
            return True

        # 1.2. In event content, test if `format` is present, equals "org.matrix.custom.html",
        # "formatted_body" is present, and is a string. If so;
        if "format" in content and content["format"] == "org.matrix.custom.html" and \
            "formatted_body" in content and isinstance(content["formatted_body"], str):

            # 1.2.1. Check formatted_body with the html subroutine,
            # if it returned true, trigger.
            if check_html_mxid(content["formatted_body"], mxid):
                return True

    # 2. For ExtEv checking, test if event type is m.room.message, or m.message.
    # Also test if m.text or m.message exists in the event content.
    # If so, run the extev subroutine, if it returned true, trigger.
    if event.type in ["m.room.message", "m.message"] and \
        ("m.text" in event.content or "m.message" in event.content):
        return should_trigger_mention_extev(event)

# ExtEv subroutine
def should_trigger_mention_extev(extev_event: dict, mxid: str) -> bool:
    content = extev_event.content

    # E.1. In event content, test if `m.text` is present and contains mxid substring, trigger if so.
    if "m.text" in content and content["m.text"].contains(mxid):
        return True

    # E.2. In event content, if `m.html` is present, run html subroutine on it, trigger if it returned true.
    if "m.html" in content and check_html_mxid(content["m.html"], mxid):
        return True

    # E.3. In event content, if `m.message` is present;
    if "m.message" in content:
        # E.3.1. Iterate over objects, for each...
        for obj in content["m.message"]:
            # E.3.2. ...if `mimetype` is "text/plain":
            # test if `body` contains mxid substring, trigger if so.
            if obj["mimetype"] == "text/plain" and obj["body"].contains(mxid):
                return True

            # E.3.3. ...if `mimetype` is "text/html":
            # run html subroutine on `body`, trigger if it returned true.
            if obj["mimetype"] == "text/plain" and check_html_mxid(obj["body"], mxid):
                return True

    # E.4. Fallback to False
    return False


# Html subroutine
def check_html_mxid(html: str, mxid: str) -> bool:
    from bs4 import BeautifulSoup

    # H.1. Interpret html string as HTML document.
    html = BeautifulSoup(content["formatted_body"], 'html.parser')

    # H.2. Iterate over all <a> tags.
    for link in soup.find_all('a'):

        # H.2.1. Ensure and extract a `href` tag.
        if "href" not in link:
            continue
        href = link["href"]

        # H.2.2. If href starts with "http" or "https";
        if href.startswith("http") or href.startswith("https"):
            from urllib.parse import urlparse, unquote

            # H.2.2.1. Interpret href as a URL.
            url = urlparse(href)

            # H.2.2.2. Ensure URL authority part is "matrix.to".
            if url.netloc != "matrix.to":
                continue

            # H.2.2.3. Grab URL fragment, unquote it, and test if it contains mxid substring,
            # return true if so.
            frag = url.fragment
            if unquote(frag).contains(mxid):
                return True

        # H.2.3. Convert a copy of the MXID to have its `@` character replaced with "matrix:u/"
        matrix_uri_mxid = "matrix:u/" + mxid[1:]

        # H.2.4. Test if href starts with this converted Matrix URI MXID, if so, return true.
        if href.startswith(matrix_uri_mxid):
            return True

    # H.3 Fallback to returning false.
    return False

```

The above also takes into account a stablized version of
[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767), which, at the time of writing,
is poised to become stablized very soon.

### Rationale

The condition is called a MXID *ping* specifically, as it is abstract over any specific form
of detecting a mention, such as "contains", or "mention.

It is the idea that, in the future, MSCs come around which add in more sophisticated methods of
embedding "pings" into messages (such as an explicit mention array), and that this condition can
be altered to automatically include those.

## Unstable prefix

The prefix for the rule should be `.nl.automatia.rule.pings_mxid`

The prefix for the condition should be `nl.automatia.mxid_ping`