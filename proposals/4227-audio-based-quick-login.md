# MSC4227: Audio based quick login

MSC4108 allows the matrix ecosystem to offer users a quicker way to sign in trusted devices, using a QR code based workflow. This is familiar to a lot of users, as they were exposed to this workflow on other networks.

However, similar are the pains for visually impaired users regarding this workflow, because it is nearly impossible, with current assistive technologies, to reliably scan a QR code. Because of that, any workflow involving those is unreasonably difficult, to the point that there are lots of workarounds developed for these situations, some working only some of the time, while others not at all.

Although normal login works for visually impaired people as well as it does for anyone, we have a quicker way to login now, and a person should not be barred from using innovations in the matrix world because of a disability. To that effect, this MSC aims to facilitate a distribution method for the binary string that qr code decodes to, which is similar in functionality and purpose to the qr code itself, but in an accessible way, so that everyone, disabled or not, can use it without hindrance, provided they have at least one recording capable device.

## Proposal

The only thing this MSC changes from the protocol outlined in the dependent MSC is the transport of the initial secret, the binary string represented through a qr code. The cryptographic primitives, the insecure session channel, the way in which  it is turned into a secure one, the strings exchanged between the two clients remain unchanged, which means that a lot of the mechanisms are in place already.

Like in the dependent MSC, any device can generate the audio signal, same for recieving it. This means that the login is more likely to succeed, all one needs is a single device which has a microphone, the other having speakers functional is implied because this is providing accessibility to visually impaired people, who definitely have speakers working otherwise they wouldn't have speech output.

The mechanism used for transmitting the audio signal across devices is morse code, as standardised and described by International Telecommunication Union [at this address](https://www.itu.int/rec/R-REC-M.1677-1-200910-I/). Here are afew reason for which this way of communication was chosen, as well as what criteria other protocols would have to satisfy in order to be considered:

* intelligible and decodable, even across moderate zones of interference. Morse stands the test of time in this category even today, because it was constructed in such a way to be minimalist, yet decodable even if recieved through a very noisy radio uplink. This means that even if the microphones and speakers of both devices are badly made, the signal should still be intelligible enough to be decodable
* well understood by a lot of people in the telecommunications industry, which means that there should be encoder and decoder implementations for it floating around in pretty much every important programming language, and if not, there are lots of docs on how to encode and parse morse
* well-formed, similar to the QR code. This means that even if there are errors in transmission, it should be possible for the initial meaning to be recovered, because glitches and errors during recording or playback still can't make a beep where there was none, or make a short beep appear long, the most it can do is create a pause between beeps, or distort a beep somewhat, but it should in most cases still be recognisable as a beep

In the following section, the workflow of sending and recieving that binary code will be explained, on both the sender device, refered to as device A from here onwards, as well as the receiver device, refered to as device B from here onwards

### initial code preparation

the binary code, the exact same one which would have been used for creating a QR code from, undergoes the following transformations:

* it gets compressed using the LZMA2 compression algorythm, so that the length of the transmission over morse is as short as possible. The following additional parameters are being used for LZMA:
  * level, 8
  * LC, 4
  * FB, 256
  * MC, 10000
  * writeEndMark, 1
* base64 encoding is being aplied, in order to not make the morse code encoder error out when parsing binary characters resulting from the compression
* the morse code signal is being generated and stored in memory, in case login didn't succeed the first time. Note however, such a signal should be deleted from memory imediately after its corresponding session timed out, like its QR equivalent. The following options should be used to generate the signal:
  * the beep being used must be a sign wave, sampled at a value between 50000 and 80000 HZ
  * the volume of the produced sign wave should not be clamped in normal conditions, but if it has to be due to potential clipping, the result should not be less than 50% of the current device's volume
  * the pause between beeps should be no less than 150 milliseconds, but not greater than 1 second, in order to make room for detecting and mitigating interference

### device A, code transmission procedure

First, the client should warn the user that they should have headphones disconnected during audio login, and if the platform on which the client is running allows for it, audio login should not be started until anything that identifies as headphones, multimedia devices, or accepting audio from the device except for speakers if such can be determined, is disconnected.

Then, once the user initiates audio login, the client should wait for at least 3 seconds, displaying or verbalising an accessible countdown, depending on platform. This is specified in order to allow the user to silence the screenreader and anything else which might be interfering with the recording on device B, as well as allowing enough time for picking up the second device and pressing record.

Finally, the device plays the recording. If at any time during the authentication flow inside the insecure channel, key mismatches are detected, this device must offer the user to restart the audio login process, be that with the same code or another, in case this one expired.

### device B, receiving the recording

Audio login must have been initiated by the first device to continue. For platforms which require microphone permissions, these should have been requested before this point, where the user is expected to initiate the recording process. For mobile devices, this most likely has to be set in static permissions, since microphone access is required so early in the flow

After the record action has been initiated, the device should play a short beep indicating it's recording, about 128 MS long. The user is advised to time this short beep after the last number in the countdown was spoken or shown, but before the morse code starts playing.

The device decodes the live recording stream from morse, then base64, untill the LZMA end marker is found. At that point, recording can be stopped imediately. In order to help with making the recording clearer and eliminating some ambient noise, the client can optionally aply a lowpass filter to remove everything below 50000 HZ, and a highpass one to remove anything above 80000 HZ

Finally, decompression, with the same compression parameters as before, is being aplied, in order to get the initial code. The rest of the login flow is being followed precisely as written in the dependent MSC, so it will not be repeated here

### note regarding accessibility and user convenience

Because the situation where one client only supports qr code, while the other only supports morse is not desirable and should be avoided, client implementors should do the following:

* if a client implements QR code login, it is strongly recommended that it also implements audio login, for accessibility reasons, because even if the other client supports audio login, the VI person still can't do anything to get the information from that qr code
* if a client implements audio login, it is not required to also implement QR loggin, because audio login is accessible to everyone

## Potential issues

This proposal may not work well, or at all, while in very noisy environments. However, since the user is about to use audio login, it should be apparent that audio login requires the audio to actually be audible, similar to trying to scan a QR code in bright sunlight. So, in most circumstances, this is a nonissue, at least for the moment. If any noise whatsoever is imediately disturbing the recording and transcribing the code wrongly, then this should be revisited, because it's a worse problem than initially anticipated

This proposal does not work at all if none of those devices have a functional microphone. There are very few devices on which one would typically use matrix where this is the case nowadays, and while this is a problem, it's one this MSC cannot solve, the only thing that can still be said about this issue is that a login that works for most visually impaired people is better than a login which works for no visually impaired people.

This proposal doesn't work if the sending device has no speakers. This is highly unlikely, considering that the overwhelming majority of visually impaired users have their devices configured with the capability of using TTS, even if that is not the primary way for them of consuming information, so speakers are most likely working

## Alternatives

Before settling on morse code, other methods were thought of, each being ultimately rejected for relatively simple reasons.

The first alternative was bluetooth based login, followed by typing a short code in one of the devices, similar to how smartphones are being connected to smart watches. This does not work because a lot of target devices for matrix users still don't have bluetooth, for example desktops.

Another idea was NFC based sending of the code, where the two devices contact each other on a specific surface, where the NFC chips are, for the sender to send the binary string along. Similar to alternative 1, the problem is availability, as this is pretty much only available in mobile devices, and perhaps tablets

Another interesting method is file sharing, where the code would be put in a file, which the user would have to transfer it to the other device. There are multiple issues with this one, only considering that the two devices are a phone and a computer, otherwise it's completely infezable:

* it takes time: plugging in a usb cable, finding it among hundreds of other files, if you know where the app even put it in the first place, all that takes a lot of time if you're reading line by line with a screenreader
* on some devices, that might not even work: if we consider the combination between the iphone and a non-apple device, if nothing major regarding this changed from ios 10, the computer is still heavily restricted in what it could access, so that file may not even be accessible outside the phone whatsoever
* not everyone has a USB cable on them all the time: yes, this is the biggest issue by far here, not everyone walks with one of those in their pockets, so if one has to quickly login to a device while on the go or something, they definitely won't be able to

A last method would be using a security key, but that wouldn't work broadly because not a lot of people have those. Furthermore, passkeys, security key authentication, etc, those should be handled by open ID connect, not quick login

## Security considerations

A serious issue that could potentially compromise the account of the user who tryes to login in this way is if someone is next to them somewhere and manages to record the morse code exchange between devices. It is true that a QR code is 2d, so the attacker would literally have to be next to the person, while audio travels in all directions so even someone over at the next table can hear and record it clearly in ideal circumstances, however this inherits all of the security protections of its dependent MSC, which means that sholder surfing, or in this case, recording the morse code by an unauthorised device, is thought of in there, and all the mitigations in there aply here as well.

Furthermore, a client could send invalid code, or send valid morse code which lasts for a very long time, trying to trigger a buffer overflow or inject bad input. Any client is recommended to stop at the first bad morse received by their decoder, and stop recording after half a minute has elapsed, if the end of stream mark hasn't been encountered yet.

If a client waits too long before sending the next batch of morse encoded samples over, and does it repeatedly, similar to a slowloris attack ment to overwhelm the listening device, then the user should stop whenever the detected silence lasts longer than the value described above in this document

## Unstable prefix

not applicable here

## Dependencies

This MSC builds on MSC4108 (which at the time of writing has not yet been accepted into the spec).
