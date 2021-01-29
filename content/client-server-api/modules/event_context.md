---
type: module
weight: 210
---

### Event Context

This API returns a number of events that happened just before and after
the specified event. This allows clients to get the context surrounding
an event.

#### Client behaviour

There is a single HTTP API for retrieving event context, documented
below.

{{event\_context\_cs\_http\_api}}

#### Security considerations

The server must only return results that the user has permission to see.
