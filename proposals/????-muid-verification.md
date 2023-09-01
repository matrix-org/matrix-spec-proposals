# MSC0000: Matrix user id verification for thrid parties

If you want to sign-up for a service which wants to have a guaranteed contact way, the current standard process is to send a verification code or link to the user. A similar method is used for so-called 'Magic links'. But this method is heavily flawed, since it requires you to change the app and for verification codes to copy the code. Finally you need to delete the message. This proposal should simplify this process with minimal effort for the websites using this method.

## User story
A user registers to a website, using his matrix user. The user is then asked in his matrix client to confirm his identity to the website. The user than either receives a code to enter on the website or the click on the button already triggers the verification.
#### Possible overlay design in a matrix-client
```
+---------------------------------------------------+
| example.org wants to verify its you who signed up.|
|  +------------------+       +------------------+  |
|  |    Disapprove    |       |     Approve      |  |
|  +------------------+       +------------------+  |
+---------------------------------------------------+
```

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
- ```verification-methods``` ```Object```<br>This objects contains all possible verification methods in the order they should be tried in.
  - ```code``` ```Object``` ```optional```<br>This verification methods provides the user with a code, that needs to be enter into a form on the website. (This is an object to possibly allow an extension of this method in the future.)
    - ```code``` ```String``` - This is the string with the code that needs to be entered on the website.
  - ```link``` ```Object``` ```optional```<br>This verification method lets the user open a link to verify his identity. This could be done without the user seeing it, just opening in the background after the user accepts the request.
    - ```url``` ```String``` - Link that should be opened if the user accepts
    - ```hide``` ```Bool``` ```optional``` - Should the user NOT see the webpage behind the link (Defaults to ```false```)
    - ```expect_response``` ```Bool``` ```optional``` - If the matrix-client opens the link, should the client expect a json-object as the response and therefor display an error if this doesn't happen? (Defaults to ```false```)
- ```disapprove_methods``` ```Object``` ```optional```<br>This objects contains all possible methods to tell the webservice, that it was NOT you, who tried to sign-up/log-in. The methods are the same as for the ```verification_methods```.

### Verify via link
If the verification request supports verification via link, and the client chooses to use this method, the client opens this link (hiden or not is decided via the hide key). The webserver than can return a ```JSON```-file. It should have the form of a matrix event as described here:
- ```matrix-event``` ```Object```
  - ```type``` ```String``` - ```m.muid-verification.result```
  - ```content``` ```Object```
    - ```result``` ```String``` - ```success```, ```error```
    - ```error_code``` ```String``` ```optional``` - ```m.invalid_url```, ```m.wrong_device```, ```m.expired```, ...

## Potential issues

*Not all proposals are perfect. Sometimes there's a known disadvantage to implementing the proposal,
and they should be documented here. There should be some explanation for why the disadvantage is
acceptable, however - just like in this example.*

Someone is going to have to spend the time to figure out what the template should actually have in it.
It could be a document with just a few headers or a supplementary document to the process explanation,
however more detail should be included. A template that actually proposes something should be considered
because it not only gives an opportunity to show what a basic proposal looks like, it also means that
explanations for each section can be described. Spending the time to work out the content of the template
is beneficial and not considered a significant problem because it will lead to a document that everyone
can follow.


## Alternatives

*This is where alternative solutions could be listed. There's almost always another way to do things
and this section gives you the opportunity to highlight why those ways are not as desirable. The
argument made in this example is that all of the text provided by the template could be integrated
into the proposals introduction, although with some risk of losing clarity.*

Instead of adding a template to the repository, the assistance it provides could be integrated into
the proposal process itself. There is an argument to be had that the proposal process should be as
descriptive as possible, although having even more detail in the proposals introduction could lead to
some confusion or lack of understanding. Not to mention if the document is too large then potential
authors could be scared off as the process suddenly looks a lot more complicated than it is. For those
reasons, this proposal does not consider integrating the template in the proposals introduction a good
idea.


## Security considerations

*Some proposals may have some security aspect to them that was addressed in the proposed solution. This
section is a great place to outline some of the security-sensitive components of your proposal, such as
why a particular approach was (or wasn't) taken. The example here is a bit of a stretch and unlikely to
actually be worthwhile of including in a proposal, but it is generally a good idea to list these kinds
of concerns where possible.*

By having a template available, people would know what the desired detail for a proposal is. This is not
considered a risk because it is important that people understand the proposal process from start to end.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy and MSCzzzz (which at the time of writing have not yet been accepted
into the spec).
