# Improving .well-known discovery of homeservers

Having [done an implementation](https://github.com/matrix-org/matrix-react-sdk/pull/2227) in the react-sdk
for .well-known autodiscovery there's a few tweaks that could be made to have the experience be easier for
developers, without sacrificing critical functionality.

In general, the process should be shortened to two steps: get the JSON and use it if possible. Currently the
process employs a lot of verification methods that don't seem to prevent anything.


### Reduce the user ID parsing to a single step

For reference, here are the current steps:

> 1. Extract the server name from the user's Matrix ID by splitting the Matrix ID at the first colon.
> 2. Extract the hostname from the server name.

This doesn't seem to account for the fact that the user's ID may have an IP address (v4 or v6), making
"extract the hostname" potentially difficult. Although the spec requires IPv6 addresses to be contained
within clear markings, using ports in IDs is generally discouraged anyways. Instead of parsing the server
hostname out, .well-known discovery should only require the use of step 1 from the reference material.

Using the result from step 1 means that we'd potentially be using the federation port to do discovery,
however this is closer to a misconfiguration of a homeserver to begin with. Although the feature is
supported in Matrix and has valid use cases, it is exceedingly rare to see the port number used in user
IDs and we have alternative, nicer, ways to use different ports in Matrix.

Note: the react-sdk PR linked above implements this approach to avoid having even more checks in place.

### Refining the validation process

For reference, here are the current UX states:

> `PROMPT`
>   Retrieve the specific piece of information from the user in a way which fits within the existing client
>   user experience, if the client is inclined to do so. Failure can take place instead if no good user
>   experience for this is possible at this point.
>
> `IGNORE`
>   Stop the current auto-discovery mechanism. If no more auto-discovery mechanisms are available, then the
>   client may use other methods of determining the required parameters, such as prompting the user, or using
>   default values.
>
> `FAIL_PROMPT`
>   Inform the user that auto-discovery failed due to invalid/empty data and PROMPT for the parameter.
>
> `FAIL_ERROR`
>   Inform the user that auto-discovery did not return any usable URLs. Do not continue further with the
>   current login process. At this point, valid data was obtained, but no homeserver is available to serve
>   the client. No further guess should be attempted and the user should make a conscientious decision what
>   to do next.

Also for reference, here is the last step of the discovery process (the validation):

> 3. Make a `GET` request to `https://hostname/.well-known/matrix/client`.
>   a. If the returned status code is 404, then `IGNORE`.
>   b. If the returned status code is not 200, or the response body is empty, then `FAIL_PROMPT`.
>   c. Parse the response body as a JSON object
>       i. If the content cannot be parsed, then `FAIL_PROMPT`.
>   d. Extract the `base_url` value from the `m.homeserver` property. This value is to be used as the base URL of
>      the homeserver.
>       i. If this value is not provided, then `FAIL_PROMPT`.
>   e. Validate the homeserver base URL:
>       i. Parse it as a URL. If it is not a URL, then `FAIL_ERROR`.
>       ii. Clients SHOULD validate that the URL points to a valid homeserver before accepting it by connecting
>           to the `/_matrix/client/versions` endpoint, ensuring that it does not return an error, and parsing and
>           validating that the data conforms with the expected response format. If any step in the validation
>           fails, then `FAIL_ERROR`. Validation is done as a simple check against configuration errors, in order
>           to ensure that the discovered address points to a valid homeserver.
>   f. If the `m.identity_server` property is present, extract the base_url value for use as the base URL of the
>      identity server. Validation for this URL is done as in the step above, but using `/_matrix/identity/api/v1`
>      as the endpoint to connect to. If the `m.identity_server` property is present, but does not have a `base_url`
>      value, then `FAIL_ERROR`.

A lot of the validation here doesn't need to be done for the following reasons. In general, the validation steps make
it difficult for libraries to provide the functionality to support their UI counterparts. By reducing the amount
of validation required, an expressive UI is still possible while also making it easier for automated clients and
libraries to use the functionality.

Step 3 in the reference should remain the same, however all of the sub points should be replaced with just two:
* If the request was successful, use the `m.homeserver` configuration where possible. The lack of a homeserver
  configuration should be considered a failure.
* If the request was successful, use the `m.identity_server` configuration where possible. This assumes that
  there is an appropriate `m.homeserver` configuration in the response.

The first check removed is checking whether the `base_url` is actually a URL. There is no definition as to what
makes a valid URL, which is completely unhelpful for the people having to implement this. Instead, the unwritten
rule where the client should be verifying the information is appropriate for its own purpose should come into
effect. This also allows application-specific clients to verify the URL independently of the specification, or
not at all if it chooses to. The risk of an invalid URL here is relatively minimal, as a responsible client would
be communicating to the user what the URL it is about to use is for the user to verify.

The other check removed is verifying a Matrix server (homeserver or identity) is actually present on the given
URL. The URL was given to the client for the sole purpose of assisting the user into the system, and is unlikely
to be wrong. If it were wrong, the administrator would be more than likely interested in fixing it for their users.
In the event of a security breach where the .well-known configuration is changed to point at a malicious party,
the client's responsibility to show which URL it is about to connect to comes into play.

Further to the point of not having to verify if a Matrix server exists on the endpoint, the risk of a conflicting
service is minimal. There are not many services out there that use both "matrix" and "m.homeserver" to do .well-known
discovery. Not to mention the possibility of a Matrix server not running on the endpoint is also minimal as a Matrix
user would have invoked the query in the first place, indicating that there is an extremely high chance that the
server is capable of speaking Matrix.
