Testing a schema
----------------
There are [many](http://json-schema.org/implementations.html) JSON Schema
validators you can use to validate incoming events. Not all of them support
JSON Schema v4, and some of them have bugs which prevent ``$ref`` from being
resolved correctly. For basic CLI testing, we recommend and have verified they
work with the Node.js package [z-schema](https://github.com/zaggino/z-schema):
```
 $ npm install -g z-schema
 $ z-schema schema/v1/m.room.message examples/v1/m.room.message_m.text
 schema validation passed
 json #1 validation passed
```
