# MSC0000: Matrix user id verification for third parties

If you want to sign up for a service that requires a guaranteed contact method, the current standard process is to send a verification code or link to the user. A similar method is used for so-called magic links. But this method is heavily flawed since it requires you to change the app, and for verification codes to copy the code. Finally, you need to delete the message. This proposal should simplify this process with minimal effort for the websites and services, from now on called third parties, using this method.

## User story
A user registers with a third party using his matrix user. The user is then asked in his matrix client (f.e. via a pop up) to confirm his identity to the third party. The user then either receives a code to enter on the website or app of the third party; or the click on the approve-button already triggers the verification.
<!---#### Possible overlay design in a matrix-client
```
+---------------------------------------------------+
| example.org wants to verify its you who signed up.|
|  +------------------+       +------------------+  |
|  |    Disapprove    |       |     Approve      |  |
|  +------------------+       +------------------+  |
+---------------------------------------------------+
```--->

## Proposal
### Requesting verification
The back-end of the requesring server sends a matrix event to the user. The content object has the following keys:
- ```requesting_device``` ```Object``` ```optional```
  - ```browser``` ```Object``` ```optional```
    - ```name``` ```String``` - Name of the browser
    - ```version``` ```String``` ```optional``` - Version of the browser
  - ```os``` ```Object``` ```optional```
    - ```name``` ```String``` - Name of the os
    - ```version``` ```String``` ```optional``` - Version of the os
  - ```ip``` ```String``` ```optional``` - IP-address of the device
- ```verification-methods``` ```Object```<br>This object contains all possible verification methods in the order they should be tried in.
  - ```code``` ```Object``` ```optional```<br>This verification methods provides the user with a code, that needs to be enter into a form on the website. (This is an object to possibly allow an extension of this method in the future.)
    - ```code``` ```String``` - This is the string with the code that needs to be entered on the website.
  - ```link``` ```Object``` ```optional```<br>This verification method lets the user open a link to verify his identity. This could be done without the user seeing it, just opening in the background after the user accepts the request.
    - ```url``` ```String``` - Link that should be opened if the user accepts
    - ```hide``` ```Bool``` ```optional``` - Should the user NOT see the webpage behind the link (Defaults to ```false```)
    - ```expect_response``` ```Bool``` ```optional``` - If the matrix-client opens the link, should the client expect [json](#verify-via-link) as the response and therefor display an error if this doesn't happen? (Defaults to ```false```)
- ```disapprove_methods``` ```Object``` ```optional```<br>This object contains all possible methods to tell the webservice, that it was NOT you, who tried to sign up/log in. The methods are the same as for the ```verification_methods```.

### Verify via link
If the verification request supports verification via link, and the client chooses to use this method, the client opens this link (hiden or not is decided via the hide key). The webserver than can return a ```JSON```-file. It should have the form of a matrix event, as described here:
- ```matrix-event``` ```Object```
  - ```type``` ```String``` - ```m.muid-verification.result```
  - ```content``` ```Object```
    - ```m.relates_to``` ```Object``` ```optional if used in the HTTP context (since it can get hard to exchange event ids between the matrix server and the server delivering the response via HTTP and the matrix client knows which event id the response is for)```
      - ```rel_type``` ```String``` - ```m.thread```
      - ```m.in_reply_to``` ```Object```
        - ```event_id``` ```String```
      - ```event_id``` ```String```
    - ```result``` ```String``` - ```success```, ```error```
    - ```error_code``` ```String``` ```optional```
      - ```m.invalid_url``` - The url is invalid
        - ```.expired```
      - ```m.wrong_device``` - The device the link was opened on does not fulfill a criteria to be accepted (f.e. the third party requires the same ip address for both the link beeing opened on and the registering device).
        - ```.ip```
        - ```.cookie```

## Potential issues

None I can think of.


## Alternatives

The planned switch to OIDC for matrix would allow users to verify their matrix-user-id via OIDC. But this only works if you want to verify your muid on a device you have access to your OIDC log in.


## Security considerations

None I can think of.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*
