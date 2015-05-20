"""Contains all the units for the spec."""
from . import AccessKeyStore
import json
import os

def prop(obj, path):
    # Helper method to extract nested property values
    nested_keys = path.split("/")
    val = obj
    for key in nested_keys:
        val = val.get(key, {})
    return val

def _load_examples():
    path = "../event-schemas/examples/v1"
    examples = {}
    for filename in os.listdir(path):
        if not filename.startswith("m."):
            continue
        with open(os.path.join(path, filename), "r") as f:
            examples[filename] = json.loads(f.read())
            if filename == "m.room.message#m.text":
                examples["m.room.message"] = examples[filename]
    return examples

def _load_schemas():
    path = "../event-schemas/schema/v1"
    schemata = {}

    def format_for_obj(obj):
        obj_type = "<%s>" % obj.get("type")
        if obj_type == "<object>":
            if obj.get("properties"):
                format = {}
                for key in obj.get("properties"):
                    format[key] = format_for_obj(obj.get("properties")[key])
                return format
            elif obj.get("additionalProperties"):
                return {
                    "<string>": (
                        "<%s>" % obj.get("additionalProperties").get("type")
                    )
                }
        elif obj_type == "<array>" and obj.get("items"):
            return [
                format_for_obj(obj.get("items"))
            ]

        enum_text = ""
        # add on enum info
        enum = obj.get("enum")
        if enum:
            if len(enum) > 1:
                obj_type = "<enum>"
                enum_text = " (" + "|".join(enum) + ")"
            else:
                obj_type = enum[0]

        return obj_type + enum_text

    for filename in os.listdir(path):
        if not filename.startswith("m."):
            continue
        print "Reading %s" % os.path.join(path, filename)
        with open(os.path.join(path, filename), "r") as f:
            json_schema = json.loads(f.read())
            schema = {
                "typeof": None,
                "type": None,
                "summary": None,
                "desc": None,
                "json_format": None,
                "required_keys": None
            }

            # add typeof
            base_defs = {
                "core#/definitions/room_event": "Room Event",
                "core#/definitions/state_event": "State Event"
            }
            if type(json_schema.get("allOf")) == list:
                schema["typeof"] = base_defs.get(
                    json_schema["allOf"][0].get("$ref")
                )

            # add type
            schema["type"] = prop(json_schema, "properties/type/enum")[0]

            # add summary and desc
            schema["summary"] = json_schema.get("title")
            schema["desc"] = json_schema.get("description")

            # add json_format
            content_props = prop(json_schema, "properties/content")
            if content_props:
                schema["json_format"] = format_for_obj(content_props)

            # add required_keys
            schema["required_keys"] = prop(
                json_schema, "properties/content/required"
            )
            schemata[filename] = schema
    return schemata

UNIT_DICT = {
    "event-examples": _load_examples,
    "event-schemas": _load_schemas
}

def load():
    store = AccessKeyStore()
    for unit_key in UNIT_DICT:
        unit = UNIT_DICT[unit_key]()
        print "Generated unit '%s' : %s" % (
            unit_key, json.dumps(unit)[:50].replace("\n","")
        )
        store.add(unit_key, unit)
    return store
