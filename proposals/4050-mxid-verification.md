# MSC4050: Matrix user id verification for third parties

If you want to sign up for a service that requires a guaranteed contact method, the current standard process is to send a verification code or link to the user.
A similar method is used for so-called magic links.
But this method is heavily flawed since it requires you to change the app, and for verification codes to copy the code.
Finally, you need to delete the message.
This proposal should simplify this process with minimal effort for the websites and services, from now on called third parties, using this method.

## User story
A user registers with a third party using his matrix user.
The user is then asked in his matrix client (f.e. via a pop up) to confirm his identity to the third party.
The user then either receives a code to enter on the website or app of the third party; or the click on the approve-button already triggers the verification.
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
- ```m.requesting_device``` ```Object``` ```optional```
  - ```m.browser``` ```Object``` ```optional```
    - ```m.name``` ```String``` - Name of the browser
    - ```m.version``` ```String``` ```optional``` - Version of the browser
  - ```m.os``` ```Object``` ```optional```
    - ```m.name``` ```String``` - Name of the os
    - ```m.version``` ```String``` ```optional``` - Version of the os
  - ```m.ip``` ```String``` ```optional``` - IP-address of the device
- ```m.verification-methods``` ```Object```<br>
This object contains all possible verification methods in the order they should be tried in.
  - ```m.code``` ```Object``` ```optional```<br>
This verification methods provides the user with a code, that needs to be enter into a form on the website. (This is an object to possibly allow an extension of this method in the future.)
    - ```m.code``` ```String``` - This is the string with the code that needs to be entered on the website.
  - ```m.link``` ```Object``` ```optional```<br>
This verification method lets the user open a link to verify his identity.
This could be done without the user seeing it, just opening in the background after the user accepts the request.
    - ```m.url``` ```String``` - Link that should be opened if the user accepts
    - ```m.hide``` ```Bool``` ```optional``` - Should the user NOT see the webpage behind the link (Defaults to ```false```)
    - ```m.expect_response``` ```Bool``` ```optional``` -
If the matrix-client opens the link, should the client expect [json](#verify)  as the response and therefor display an error if this doesn't happen? (Defaults to ```false```)
- ```m.disapprove_methods``` ```Object``` ```optional```<br>
This object contains all possible methods to tell the webservice, that it was NOT you, who tried to sign up/log in. The methods are the same as for the ```m.verification_methods```.

### Verify
If the user takes an action, the server should send a new event to let the client know the current state.
  - ```type``` ```String``` - ```m.mxid_verification.result```
  - ```content``` ```Object```
    - ```m.relates_to``` ```Object```
```optional if used in the HTTP context (since it can get hard to exchange event ids between the matrix server and the server delivering the response via HTTP and the matrix client knows which event id the response is for)```
      - ```rel_type``` ```String``` - ```m.thread```
      - ```m.in_reply_to``` ```Object```
        - ```event_id``` ```String```
      - ```event_id``` ```String```
    - ```m.mxid_verification.result.id``` ```String``` - An id assigned by the third party to let the client match responses via HTTP and matrix.
    - ```m.result``` ```String``` - ```success```, ```error```
    - ```m.state``` ```String``` - ```m.pending```, ```m.verified```, ```m.disapproved```
    - ```m.error_code``` ```String``` ```optional```
      - ```m.invalid_verification``` - The url/code is invalid
        - ```.expired```
      - ```m.wrong_device``` -
The device the link was opened on does not fulfill a criteria to be accepted (f.e. the third party requires the same ip address for both the link being opened on and the registering device).
        - ```.ip```
        - ```.cookie```
       
#### Verify via link
If the verification request supports verification via link, and the client chooses to use this method, the client opens this link (hidden or not is decided via the hide key).
The webserver than can return a ```JSON```-file.
It should have the form of a matrix event, as described above, but all in a ```matrix_event``` object (the reason for transmitting the event also via the HTTP connection is to allow faster responses in the users matrix-clients ui).

## Potential issues

None I can think of.


## Alternatives

The planned switch to OIDC for matrix would allow users to verify their matrix-user-id via OIDC.
But this only works if you want to verify your mxid on a device you have access to your OIDC log in.


## Security considerations

None I can think of.

## Unstable prefix

Replace the ```m.``` with a ```io.github.jucktnich```.
