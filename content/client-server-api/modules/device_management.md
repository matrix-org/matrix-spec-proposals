---
type: module
---

### Device Management

This module provides a means for a user to manage their [devices](/#devices).

#### Client behaviour

Clients that implement this module should offer the user a list of
registered devices, as well as the means to update their display names.
Clients should also allow users to delete disused devices.

{{% http-api spec="client-server" api="device_management" %}}

#### Security considerations

Deleting devices has security implications: it invalidates the
access\_token assigned to the device, so an attacker could use it to log
out the real user (and do it repeatedly every time the real user tries
to log in to block the attacker). Servers should require additional
authentication beyond the access token when deleting devices (for
example, requiring that the user resubmit their password).

The display names of devices are publicly visible. Clients should
consider advising the user of this.
