# MSC4227: Audio based quick login

MSC4108 allows the matrix ecosystem to offer users a quicker way to sign in trusted devices, using 
a QR code based workflow. This is familiar to a lot of users, as they were exposed to this workflow 
on other networks.

However, the pains for visually impaired users regarding this workflow are the same here as they 
are on other devices, because it is nearly impossible, with current assistive technologies, to 
reliably scan a QR code. Because of that, any workflow involving those is unreasonably difficult, 
to the point that there are lots of workarounds developed for these situations, some working only 
some of the time, while others not at all.

Although normal login works for visually impaired people as well as it does for everyone, we have a 
quicker way to login now, and a person should not be barred from using innovations in the matrix 
world because of a disability. To that effect, this MSC aims to facilitate a distribution method 
for the binary string that qr code decodes to, which is similar in functionality and purpose to the 
qr code itself, but in an accessible way, so that everyone, disabled or not, can use it without 
hindrance, provided they have at least one recording capable device.

## Proposal

The only thing this MSC changes from the protocol outlined in the dependent MSC is the transport 
layer through which the binary string goes from one device to another. The cryptographic 
primitives, the insecure session channel, the way in which  it is turned into a secure one, the 
strings exchanged between the two clients remain unchanged, which means that a lot of the 
mechanisms are in place already.

Like in the dependent MSC, any device can generate the audio signal, same for recieving it. This 
means that the login is more likely to succeed, all one needs is a single device which has a 
microphone, the other having speakers functional is implied because this is providing accessibility 
to visually impaired people, who definitely have speakers working otherwise they wouldn't have 
speech output.

The mechanism used for transmitting the audio signal across devices is Dual-tone multi-frequency 
signaling (DTMF), as standardised and described by the International Telecommunication Union, with 
[ITU-T Recommendation Q.23](http://www.itu.int/rec/T-REC-Q.23/en). Here are afew reasons for which 
this way of communication was chosen, as well as what criteria other protocols would have to 
satisfy in order to be considered viable in the future:

* intelligible and decodable, even across moderate zones of interference. DTMF stands the test of 
time in this category even today, because it was constructed in such a way to be minimalist, out of 
the way of voice and most normally occuring background ambience sources, yet decodable even if 
recieved through a very noisy phone line, being used even today for telephone operated menus, as 
well as pieces of equipment. This means that even if the microphones and speakers of both devices 
are badly made, the signal should still be intelligible enough to be decodable, because however bad 
it is, it can't really be worse than 22000 HZ, as phones were transmitting and recieving back in 
the day this was invented
* understood by a lot of people in the telecommunications industry, which means that there should 
be encoder and decoder implementations for it floating around in pretty much every important 
programming language, and if not, there are lots of docs on how to encode and parse it. There will 
be some additions to the standard, or rather, some reinterpretations of what some of the values in 
there mean which will be discussed later in this document, however normal DTMF decoders should be 
able to understand this slightly altered version as well, and these alterations are minor enough 
that clients can deal with the discrepancies on their own, on top of the regular DTMF decoding and 
encoding procedures as described by the standard
* well-formed, with similar properties to the QR code in that regard. Phone lines, line operators, 
answering machines and lots of equipment still use this technology even today, because it's very 
hard to blur or obstruct such a signal with regular voice and ambient noises, as its frequency 
range can be easily enough isolated without irrecoverable degradation. This means that it's very 
hard to get a corrupted key while sending this kind of signal, even in a very bad reception 
environment, for example the microphone being very crappy or speakers very quiet, which is also 
important here

In the following section, the workflow of sending and recieving that binary code will be explained, 
on both the sender device, refered to as device A from here onwards, as well as the receiver 
device, refered to as device B

### initial code preparation

the binary code, the exact same one which would have been used for creating a QR code from, 
undergoes some transformations, for the machines to be able to capture and send it easier.

Every byte in the binary stream is considered numerically, without consideration to what it 
initially ment. To that effect, every byte is being split in pairs of four bits, enough for a DTMF 
tone to encode. So, in order to recover one byte from the initial binary code on the other side, 
two tones would have to be received.

The bytes are processed in the little endian mode, regardless of the endianness of the platform, 
this allows for greatter portability.

The original DTMF standard supports numbers from 0 to 9, letters from A to D and the symbols * and 
#. However, because we're encoding binary, some adjustments have to be made to the original 
standard, for our purposes it helps if the range of values supported by dtmf are seen as encoding a 
hexadecimal digit, so then the following aplies:

* numbers 0...9 are cleanly mapping onto hexadecimal, 0x0...0x9
* a, b, c and d get mapped to 0xA aka 10 in decimal, all the way to 0xD which is 13 in decimal
* the symbols * and #, however, are not letters whatsoever, so they will be repurposed to map onto 
0xE and 0xF specifically

In order for the audio login process, especially the recording process, to be as painless and as 
uncluttered with extra noise as possible, there has to be a way for the recording device to know 
when to start and when to stop decoding the live sample stream coming from the microphone. For this 
purpose, the sequence which normally decodes to `**` should be parsed as beginning of transmission, 
meaning that any recorded data before that point should be irrelevant, and `##` should be used for 
end of transmission, at which point the recording device should imediately stop recording and 
decoding, as the whole code should be already transmitted in its entirety by then. Unfortunately, 
this means that bytes of the value 0xEE and 0xFF are forbidden, so if the encryption algorythms or 
the URL encoded in that binary string resolve to those bytes, then they are no longer allowed, and 
an alternative way of encoding should be found for them

The tone itself should be made according to the standard, with afew important changes:

* the duration of a tone should be no more than 128 MS
* the pauses between tones should be no more than 25 MS

### device A, code transmission procedure

First, the client should warn the user that they should have headphones disconnected during audio 
login, and if the platform on which the client is running allows for it, audio login should not be 
started until anything that identifies as headphones, multimedia devices, or accepting audio from 
the device except for speakers if such can be determined, is disconnected.

Then, once the user initiates audio login, the client should wait for at least 3 seconds, 
displaying or verbalising an accessible countdown, depending on platform. This is specified in 
order to allow the user to silence the screenreader and anything else which might be interfering 
with the recording on device B, as well as allowing enough time for picking up the second device 
and pressing record.

Finally, the device plays the recording. If at any time during the authentication flow inside the 
insecure channel, key mismatches are detected, this device must offer the user to restart the audio 
login process, be that with the same code or another, in case this one expired.

### device B, receiving the recording

Audio login must have been initiated by the first device to continue. For platforms which require 
microphone permissions, these should have been requested before this point, where the user is 
expected to initiate the recording process. For mobile devices, this most likely has to be set in 
static permissions, since microphone access is required so early in the flow

After the record action has been initiated, as well as after the recording stopped (see below), the 
device should play a short beep indicating it's recording, about 25 MS long. This is mostly 
cosmetic and its absence shouldn't negatively affect the user experience, except that it's good for 
the user to know when recording is started or stopped

The device should only begin decoding the recorded stream after two consecutive tones decoding to 
`**`, or 0xEE by the mappings discussed above, are captured, and decoding should end either after a 
50 second timeout, or if two consecutive tones decoded as `##`, or 0xFF by the mappings above, are 
identified. Anything which falls outside the decoding interval should be dropped and not considered 
decoding related data.

In order to help with making the recording clearer and eliminating some ambient noise, the client 
can optionally aply a lowpass filter to remove everything below the frequency of the tones as 
described by the standard, and a highpass one to remove anything above that same frequency, but in 
most cases that is not required because those tones are played at a frequency which doesn't often 
collide with anything in the neighborhood of the typical user.

To get the initial code, the decoder should take a pair of tones at a time, reconstructing the 
original byte at that position, based on the rules and mappings discussed above. Note however, the 
network order in this case is little endian, implementors should be careful when reconstructing 
those to order the four bit pairs according to the endianness of the platform their client is 
running on. The rest of the login flow is being followed precisely as written in the dependent MSC, 
so it will not be repeated here

### note regarding accessibility and user convenience

Because the situation where one client only supports qr code, while the other only supports DTMF is 
not desirable and should be avoided, client implementors should do the following:

* if a client implements QR code login, it is required that it also implements audio login, for 
accessibility reasons, because even if the other client supports audio login, the VI person still 
can't do anything to get the information from the qr code displayed by the first client
* if a client implements audio login, it is recommended to also implement QR login wherever doing 
so would make sense for the current platform, demographic or device capabilities, because while 
audio login is accessible to everyone, there are still situations in which it is impossible to 
perform an audio login with that device, for example the inability to use speakers, the person 
finding themselves in an aria where it's not allowed to make unauthorised noise, etc

## Potential issues

This proposal may not work well, or at all, while in very noisy environments. However, since the 
user is about to use audio login, it should be apparent that audio login requires the audio to 
actually be audible, similar to trying to scan a QR code in bright sunlight. So, in most 
circumstances, this is a nonissue, at least for the moment. If any noise whatsoever is imediately 
disturbing the recording and transcribing the code wrongly, then this should be revisited, because 
it's a worse problem than initially anticipated

This proposal does not work at all if none of the participating devices have a functional 
microphone. There are very few devices on which one would typically use matrix where this is the 
case nowadays, and while this is a problem, it's one this MSC cannot solve, the only thing that can 
still be said about this issue is that a login that works for most visually impaired people is 
better than a login which works for no visually impaired people.

This proposal doesn't work if the sending device has no speakers. This is highly unlikely, 
considering that the overwhelming majority of visually impaired users have their devices configured 
with the capability of using TTS, even if that is not the primary way for them of consuming 
information, so speakers are most likely working. However, if for any reason whatsoever the device 
doesn't have speakers, for example if only headphones are attached to a particular device, then 
putting the phone close to the headphones might achieve some results, but this spec does not also 
extend to those cases, as normal login is still available for everyone

## Alternatives

Before settling on TDMF, other methods were thought of, each being ultimately rejected for various 
reasons.

An alternative used in previous versions of this MSC was morse code. This had the potential of 
working unlike any of the below alternatives, however it would have required more transformations 
than just slightly altering the binary code to fit the DTMF standard.

We also have to consider the notoriety of morse code for being very long, meanwhile this method is 
expected to finish transporting the code in at most half a minute, which is definitely an 
improvement. Furthermore, it is capable of encoding fewer variation than DTMF while taking more 
space, so after further consideration, this version was abandoned.

The MSC was very complicated as a result, containing compression, custom end recording markers 
which could very well have been encoded in multi-letter base32 encoded binary, it would definitely 
take more processing power when implemented as a result, which is another reason for which this 
specification proposal is simpler to understand and probably also to implement.

After morse, one possibility would have been bluetooth or wifi based login, followed by typing a 
short 6 digit code in one of the devices, similar to how smartphones are connecting to smart 
watches today. This does not work because a lot of target devices for matrix users still don't have 
bluetooth, for example desktops.

Another idea was NFC based sending of the code, where the two devices contact each other on a 
specific surface, where the NFC chips are, for the sender to send the binary string along. Similar 
to alternative 1, the problem is availability, as this is pretty much only available in mobile 
devices, and perhaps tablets

Another interesting method is file sharing, where the code would be put in a file, which the user 
would have to then transfer across to the other device. There are multiple issues with this 
proposal:

* this can only be done reliably and quickly enough between a computer and a phone. Trying to use 
usb storage devices between two computers would take too long, causing the attempt to quickly time 
out. Using bluetooth is an option, but the issue there is that not enough devices have it enabled, 
see the beginning of this section
* it takes time: plugging in a usb cable, finding the temporarily created file among hundreds of 
others, if you know where the app even put it in the first place, all that takes a lot of time if 
you're reading line by line with a screenreader, and even if you know your phone very well, this 
still presents a hurdle because it'll time out a lot
* on some devices, that might not even work: if we consider the combination between the iphone and 
a non-apple device, the computer is heavily restricted in what it could access, so that file may 
not even be accessible outside the phone whatsoever
* not everyone has a USB cable on them all the time: yes, this is the biggest issue by far here, 
not everyone walks with one of those in their pockets, so if one has to quickly login to a device 
while on the go or something, they definitely won't be able to do so at all

A last method would be using a hardware security key, but that wouldn't work broadly because not a 
lot of people have those. Furthermore, passkeys, security key authentication, etc, those should be 
handled by open ID connect, not quick login

## Security considerations

A serious issue that could potentially compromise the account of the user who tryes to login in 
this way is if someone is next to them somewhere and manages to record the code exchange between 
devices. It is true that a QR code is 2d, so the attacker would literally have to be next to the 
person, while audio travels in all directions so even someone over at the next table can hear and 
record it clearly in ideal circumstances, however this inherits all of the security protections of 
its dependent MSC, which means that sholder surfing, or in this case, recording the code by an 
unauthorised device, is thought of in there, and all the mitigations described there aply here as 
well.

Furthermore, a client could send invalid tone sequences on purpose, or send valid DTMF tones which 
last for a very long time, trying to trigger a buffer overflow or inject bad input. Any client is 
recommended to stop at the first bad tone, within reason considering correction for ambience noise 
if applicable, received by their decoder, and stop recording after half a minute has elapsed, if 
the end of stream mark hasn't been encountered yet.

If a client waits too long before sending the next batch of encoded samples over, and does it 
repeatedly, similar to a slowloris attack ment to overwhelm the listening device, then the user 
should stop whenever the detected silence lasts longer than the value described above, when talking 
about the pause between beeps.

## Unstable prefix

not applicable here

## Dependencies

This MSC builds on [MSC4108](https://github.com/matrix-org/matrix-spec-proposals/pull/4108), which at the time of writing has not yet been accepted into the spec.

