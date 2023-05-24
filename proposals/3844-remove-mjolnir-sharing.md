# MSC3844: Remove "Mjolnir" (policy room) sharing mechanism

Way back when [MSC2313](https://github.com/matrix-org/matrix-spec-proposals/pull/2313) was written,
it included a [sharing](https://spec.matrix.org/v1.3/client-server-api/#sharing-1) mechanism that
never got used.

That sharing mechanism is to be removed from the specification due to lack of use and questionable
technical approach. In practice, users and implementations have been handing out room aliases to
policy rooms just fine.

Normally an MSC would propose deprecation followed by eventual removal, however seeing as the core
team is aware of exactly zero implementations of this feature it feels safe to just outright remove.
