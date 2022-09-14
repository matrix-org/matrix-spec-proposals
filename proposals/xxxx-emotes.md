# MSCXXXX: Emotes
## Proposal
Every emote proposal uses a shortcode and a way to store the image and make the client render it. Under this proposal they are not sent in the message source as <img> tags, which is what many non-Element clients use. In this proposal, the message source is not edited and it is sent as a shortcode. Rather it is up to the client to load it when rendering. In the current implementation/proposal it is rendered in the message as follows:
```html
 <img class="mx_Emote" title=":shortcode:" src="blob:https://example.com/blob-guid">
```
This is similar to current implementations in structure, but rather than having clients render img tags from the message source they are added during construction of the message html.
## Emote sources
###Room emotes
Room emotes are per-room emotes that are defined in an m.room.emote event. 
The emotes are defined inside of a dict which has the shortcode as a key and the either encrypted or unencrypted source for the emote as a value.
For encrypted rooms it follows the format:
```json
{
  "short": { IEncryptedFile  }
}
```

For non encrypted rooms it follows: 
```json
{
"short": { 
“mxc://abcdefg”
  }
}
```

Note: this format could be modified, but would have to be agreed upon so the clients can load them in properly.

## Alternatives:
Other proposals regarding this issue: [MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545) and [MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951)

Below is a comparison highlighting the differences between this and other proposals.
### Advantages
Security: Emotes in private rooms can be encrypted so that potentially sensitive data is not publicly available to the server. Emotes in public rooms are necessarily unencrypted. One note is that although emotes are encrypted they are available to anyone in the private room, and server admins can join private rooms so they are not fully e2ee like messages. If server admins lose the ability to join any private room
Message source is not edited. The client does not edit the actual sent message but renders emotes locally. Leaving the message source untouched could be helpful for future updates or deleting emotes/changing the way emotes are rendered.
Rendering. Current implementations use data-mx-emoticon types in the img tag. This uses the mx_Emote class name although that could also be changed since it is rendered locally.
Compatibility with other MSCs: Although certain aspects of other MSCs cannot be kept the same, many general ideas from those could be carried over.
### Disadvantages
Lack of user-specific emotes. It might be possible to implement this in public rooms if the client pulls every user’s public emote data to load. Generally user specific emotes goes against the idea of emotes being a shared set of images.
Might be more difficult for clients to implement. Requires existing clients to change their implementations.
## Additional Points
This could be extended to spaces although the main current implementation does not have this. Spaces would take priority over individual room emotes if there is a shortcode clash. 
Add custom emotes for reactions and the emoji picker. 
Other MSCs introduced the idea of shareable packs. Those would be compatible with image packs except for encrypted rooms. It might be simpler to allow users to download a zip file of all the emotes in a room.
