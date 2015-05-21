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

    def get_content_fields(obj, enforce_title=False):
        # Algorithm:
        # f.e. property => add field info (if field is object then recurse)
        if obj.get("type") != "object":
            raise Exception(
                "get_content_fields: Object %s isn't an object." % obj
            )
        if enforce_title and not obj.get("title"):
            raise Exception(
                "get_content_fields: Nested object %s doesn't have a title." % obj
            )

        required_keys = obj.get("required")
        if not required_keys:
            required_keys = []

        fields = {
            "title": obj.get("title"),
            "rows": []
        }
        tables = [fields]

        props = obj["properties"]
        for key_name in props:
            value_type = None
            required = key_name in required_keys
            desc = props[key_name].get("description", "")

            if props[key_name]["type"] == "object":
                if props[key_name].get("additionalProperties"):
                    # not "really" an object, just a KV store
                    value_type = (
                        "{string: %s}" %
                        props[key_name]["additionalProperties"]["type"]
                    )
                else:
                    nested_object = get_content_fields(
                        props[key_name], 
                        enforce_title=True
                    )
                    value_type = "{%s}" % nested_object[0]["title"]
                    tables += nested_object
            elif props[key_name]["type"] == "array":
                # if the items of the array are objects then recurse
                if props[key_name]["items"]["type"] == "object":
                    nested_object = get_content_fields(
                        props[key_name]["items"], 
                        enforce_title=True
                    )
                    value_type = "[%s]" % nested_object[0]["title"]
                    tables += nested_object
                else:
                    value_type = "[%s]" % props[key_name]["type"]
            else:
                value_type = props[key_name]["type"]

            fields["rows"].append({
                "key": key_name,
                "type": value_type,
                "required": required,
                "desc": desc,
                "req_str": "**Required.** " if required else ""
            })
        return tables

    for filename in os.listdir(path):
        if not filename.startswith("m."):
            continue
        print "Reading %s" % os.path.join(path, filename)
        with open(os.path.join(path, filename), "r") as f:
            json_schema = json.loads(f.read())
            schema = {
                "typeof": None,
                "type": None,
                "title": None,
                "desc": None,
                "content_fields": [
                # {
                #   title: "<title> key"
                #   rows: [
                #       { key: <key_name>, type: <string>, 
                #         desc: <desc>, required: <bool> }
                #   ]
                # }
                ]
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
            schema["title"] = json_schema.get("title")
            schema["desc"] = json_schema.get("description")

            # walk the object for field info
            schema["content_fields"] = get_content_fields(
                prop(json_schema, "properties/content")
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
