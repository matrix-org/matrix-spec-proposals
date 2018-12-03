# MSC 1740: Using the Accept header to select an encoding

Matrix has always aimed to support many types of encoding However, in practice the only supported option
is JSON. The assumption that all clients and servers make is that requests will be carried out in JSON.
This proposal aims to change that by using the `Accept` HTTP header to select the best encoding for the
client and the server. This proposal doesn't attempt to use the same header for federation (S2S) endpoints,
just for C2S endpoints.

The reason for supporing multiple encodings other than JSON would be to open the door to more efficent
encoding methods in the future for the HTTP transport, for example CBOR which was found to have a 20%
reduction in size. However, this proposal is not here to evaluate the merits of any one particular encoding.

## Proposal

### Servers

Servers can support multiple encodings for both reading requests and sending responses over HTTP. They
should read the `Accept` header [RFC7231](https://tools.ietf.org/html/rfc7231#section-5.3.2) from client
and decide based on the rules provided in the RFC what is the best encoding they can support.

If a encoding could not be found that satifies both parties, the server should default to JSON. This is
due to historical reasons as Matrix has presumed JSON support in all implementations. Another benefit to this
is that JSON is human-readable, which means that even basic clients such as `telnet` or `curl `will be
able to read a response from a server.

To that end, we do NOT use `HTTP 406 Not Acceptable` which would imply that no content type was determined.

Servers should send the correct `Content-Type` for the encoding they picked, even if the encoding
is the fallback of JSON.

If the client sends a request in an encoding the server does not support, the server should respond with
`HTTP 415 Unsupported Media Type` and an error of:

```
{
  "errcode": "M_CONTENT_TYPE_NOT_SUPPORTED",
  "error": "..error message left to the discretion of the implementation.."
}
```

It is not important that the client can decode the response, because 415 should be clear that the server
can not parse the request.

### Clients

Clients should supply `Accept` to all requests they make, and set `Content-Type` to the encoding
they intend to use.

The client should not attempt to communicate with this homeserver if the response `Content-Type` was
not acceptable to the client, because it will mean that neither party have a supported encoding type.
An appropriate error may be displayed to the user.

It is suggested (but not required), that clients first request `/_matrix/client/versions`  from the
sever to ensure that `Accept` is acceptable and by doing so negotiate an appropriate encoding.

## Alternative solutions

### Negotiate transport(+encoding)

It's clear that this proposal still limits Matrix to serving HTTP. We could expand the proposal 
to negoitating transport either from within a HTTP header (which would `Upgrade` you to a different
transport), .well-known or a SRV record rather than limiting ourselves to `Accept`. The proposal 
does not currently look at negotiating transport as I believe the encoding should be negotiated 
within the transport and is a seperate proposal. 

## Potential issues

- This proposal does NOT specify any additional encoding formats for the time being, and could be dealt
with in future by another proposal.

# Security considerations

I cannot think of any security issues with doing this.

## Conclusion

This proposal allows implementations to broaden what encodings they support without
having to be configured on a case by case basis. This proposal uses standard HTTP headers
to deliver a simple method of determinign what encodings both parties support. This paves
the way for a more diverse and competitive ecosystem over speed and performance of different
encodings.
