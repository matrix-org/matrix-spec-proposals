Servers MUST strictly enforce the JSON format specified in the
[appendices](/appendices#canonical-json). This translates to a
400 `M_BAD_JSON` error on most endpoints, or discarding of events over
federation. For example, the Federation API's `/send` endpoint would
discard the event whereas the Client Server API's `/send/{eventType}`
endpoint would return a `M_BAD_JSON` error.
