# MSC3892: Emotes
## Proposal
#### Definitions:
Emotes: Short for emoticons, a shortcode/image pair that are used inline in messages and in reactions. <br/> 
Emojis: Shortcode/image pairs with unicode representations. Currently supported in most clients. A subset of emotes. <br/> 
Shortcode: A short piece of text surrounded in colons to represent an emote/emoji. Ex. :shortcode: 
<br/><br/>
Every emote proposal uses a shortcode and a way to store the image and make the client render it. <br/> 
Under this proposal they are not sent in the message source as img tags, which is what many non-Element clients use. <br/> 
In this proposal, the message source is not edited and it is sent as a shortcode. Rather, it is up to the client to <br/>load it when rendering messages.<br/> 
<br/><br/>
In the current implementation/proposal it is rendered in the message html as follows:

```html
 <img class="mx_Emote" title=":shortcode:" src="blob:https://example.com/blob-guid">
```
This is similar to current implementations in structure, but rather than having clients render img tags <br/>
from the message source they are added during construction of the message html. Encrypted rooms can use the blob obtained after decryption
while unencrypted ones can directly use the mxc url.

## Emote sources
### Room emotes
Room emotes are per-room emotes that are defined in an m.room.emotes event. They can be uploaded from the room settings by moderators or above.
The emotes are defined inside of a dict which has the shortcode as a key and the either encrypted or unencrypted source for the emote as a value.
### Storage format
For encrypted rooms the m.room.emotes event follows the format:
```
{
"content":{
	"short": IEncryptedFile (a json object with information on how to decrypt the file)
	}
}
```

For non encrypted rooms the m.room.emotes event follows: 
```
{
"content":{
 	"short": “mxc://abcdefg”
	}
}
```

Note: this format could be modified, but would have to be agreed upon so the clients can load the emotes in properly.

## Alternatives:
Other proposals regarding this issue: [MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545) and [MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951)

Below is a comparison highlighting the differences between this and other proposals.
### Advantages
#### Security
Emotes in private rooms can be encrypted so that potentially sensitive data is not publicly available to server members. <br/> 
Emotes in public rooms are necessarily unencrypted. <br/>
One important note is that although emotes are encrypted they are available to anyone in the private room, and server <br/> 
admins can see the emotes in the room state so they are not e2ee like messages. <br/> 
If the file keys or room state is encrypted [MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414) and if server admins lose the ability to join any private room <br/>it would then be e2ee.
The current advantage is that the emotes will not be obtainable for other users on the server who are not in the private room.
<br/>
#### Message source is not edited
The client does not edit the actual sent message but renders emotes locally. Leaving the message source untouched <br/>
 could be helpful for future updates or deleting emotes/changing the way emotes are rendered.
<br/>
#### Rendering
Current implementations use data-mx-emoticon types in the img tag. This uses the mx_Emote class name although that <br/>
could also be changed since it is rendered locally.
Compatibility with other MSCs: Although certain aspects of other MSCs cannot be kept the same, many general ideas from <br/>
those could be carried over.
### Disadvantages
#### Lack of user-specific emotes. 
It might be possible to implement this in public rooms if the client pulls every user’s public emote data to load. <br/>
Generally, however, user specific emotes goes against the idea of emotes being a shared set of images. <br/>
Additionally, user specific emotes could be handled by sending image data in the message json, but that would be <br/>
separate from room emotes as defined in this proposal since room emotes should update when the room settings are updated.

#### Might be more difficult for clients to implement
Requires existing clients to change their implementations.
## Additional Points
This could be extended to spaces although the main current implementation does not have this. <br/>
Spaces would take priority over individual room emotes if there is a shortcode clash. 
<br/><br/>
Add custom emotes for reactions and the emoji picker. 
<br/><br/>
Other MSCs introduced the idea of shareable packs. This could be compatible with image packs except for encrypted rooms. <br/> 
It would be simpler to allow users to download a zip file of all the emotes in a room.
<br/><br/>