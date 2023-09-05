# MSC2774: Giving widgets their ID so they can communicate

Under the [current specification](https://github.com/matrix-org/matrix-doc/pull/2764), widgets are
able to communicate with their client host, however doing so is a bit difficult if they don't already
know their widget ID. Some widgets will be able to get their ID from another source like an
integration manager, however this is not the case for all widgets.

[MSC2762](https://github.com/matrix-org/matrix-doc/pull/2762) has a fair amount of background
information on widgets, as does the current specification linked above.

## Proposal

Currently widgets can expect a `?widgetId` query parameter sent to them in clients like Element,
however this has some issues and as such is not proposed to exist any further. One of the issues
is that the widget must retain the query string, which isn't entirely possible for some frontends
(they would instead prefer to use the fragment). It's also a privacy risk in that by being sent
through the query string, the server can be made aware of the widget ID. The widget ID doesn't
normally contain any useful information (it's an opaque string), however it's not required for
the server to function under typical usage.

The proposal is to introduce a `$matrix_widget_id` template variable for the URL, similar to the
existing `$matrix_room_id` variable. Widgets can then have their widget ID wherever they want in
the widget URL, making it easier on them to find and use.

This carries the same risks as a room ID being passed to the widget: the client can easily lie about
it, however there's no real risk involved in doing so because it's used for communication only. So
long as the client is able to identify which widget is talking to it, it doesn't really matter. It's
more of a problem if the client uses a widget ID from another widget as that could confuse the
client, however this is believed to be a bug. Clients should also be performing origin checks to
ensure the widget is talking from a sane origin and not somewhere else, like another tab or browser.

## Potential issues

This is not backwards compatible with the history of widgets so far, so clients and widgets will
need to be modified to support it. Clients which currently use the `?widgetId` parameter are
encouraged to continue supporting the parameter until sufficient adoption is reached.

## Alternatives

As mentioned, a query parameter could be used, though this has the issues previously covered. Another
solution might be to allow a single widget API action which has no widget ID solely for the purpose
of finding the widget ID, however clients are unlikely to be able to differentiate between two widgets
if this were the case.

Another solution would be to let the widget discover its widget ID by harvesting it out of the first
widget API request it sees. This can't always be relied upon (some flows require the widget to
speak first), and as the widget API becomes more capable it could become a security risk. A malicious
browser extension could spam the widget with fake requests to try and convince it to talk to it
instead of the client, thus redirecting some information to the wrong place.

## Unstable prefix

Implementations should use `$org.matrix.msc2774_widget_id` as a variable until this lands in a 
released version of the specification.
