# MSC3790: Register Clients
It should be possible to delegate specific tasks to other clients which are able to handle them. To make this 
possible the spec should define a special private room for the user, which is used by clients to register their 
abilities, to which device they belong and by which method they can be startet.

If a matrix chat-client finds an event which is not related to messaging, it searches the registry for clients
that can process the event and offers to launch them.

For an example a remote-control app could use matrix to establish a p2p connection. Therefore the app would not
need its own backend and account system. Another example is collaborative editing directly in matrix.

## Proposal

The spec should reserve the special room "client_registrations". 
On first login a client postes an event of type `m.client_registration` to this room.

Example message:
```
{
  "type": "m.client_registration",
  "content": {
    "client_name":"the name",
    "client_device_id":"",
    "launch_command":"/home/me/bin/some_excutable",
    "associated_event_types": [
        "org.example.custom",
        "org.example.cumtom2"
    ],
    "actions": [
        {
            "name": "do something",
            "command": "/home/me/bin/some_excutable --do_something",
            "icon": {
              "url": "mxc://example.org/efgh5678",
              "mimetype": "image/jpeg",
              "size": 123,

              "width": 160,
              "height": 120
            }
            "description": "does something",
        },
    ]
    
  }
}
```

```
{
  "type": "m.client_registration",
  "content": {
    "client_name":"the name",
    "client_device_id":"",
    "launch_command":"somewebsite.com/app",
    "associated_event_types": [
        "org.example.custom",
        "org.example.cumtom2"
    ],
    "actions": [
        {
            "name": "do something",
            "url": "somewebsite.com/app?action=some",
            "icon": {
              "url": "mxc://example.org/efgh5678",
              "mimetype": "image/jpeg",
              "size": 123,

              "width": 160,
              "height": 120
            }
            "description": "does something",
        },
    ]
    
  }
}
```

`client_name` is the app name.
`client_device_id` is the id the device this client is located on.
`launch_command` is the command to run when the user wants to inspect one of the associated_event_types.
`launch_url` is the url the user should open to inspect the command.
`actions` is a list of actions this app can perform independently of any prior message:
- `name` is the name of the action.
- `command` is the command which performs the action.
- `url` is the url which performs the action.
- `description` explains what the action does.

when launch_command is excuted the enviorment varaible MATRIX_CLIENT_STARTUP_EVENT is set to "<room_id>/<message_id>"
when an action is started the enviorment varaible MATRIX_CLIENT_ACTION_LOCATION is set to "<room_id>"

Using enviorment varaibles has the advantage that this functionality can be implemented as a plugin for an existing app.

To highlight certain events a client can use "m.event_description" event.

Example event:
```
{
  "type": "m.event_description",
  "content": {
    "target":"event_id",
    "description": "this event does something",
    "main_action": "respond",
    "icon": {
      "url": "mxc://example.org/efgh5678",
      "mimetype": "image/jpeg",
      "size": 123,

      "width": 160,
      "height": 120
    }
  }
}
```

`target` is the event this event is reffering to.
`main_action` is text on the button which opens the client.
`description` gives information about this event.

## Potential issues
By sending a malicious message to this room, you can trigger abitrary code execution. Maybe this can be circumvented
by only allowing executing commnds which point to files that have a certain prefix like `matrix_client_`.

## Alternatives:
Just do it mannually. The specialised client can send a message saying new events have arrived.
