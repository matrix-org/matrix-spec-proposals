"""Contains all the units for the spec."""
from batesian.units import Units
import inspect
import json
import os
import subprocess


class MatrixUnits(Units):

    def load_common_event_fields(self):
        path = "../event-schemas/schema/v1/core"
        event_types = {}
        with open(path, "r") as f:
            core_json = json.loads(f.read())
            for event_type in core_json["definitions"]:
                if "event" not in event_type:
                    continue  # filter ImageInfo and co
                event_info = core_json["definitions"][event_type]
                table = {
                    "title": event_info["title"],
                    "desc": event_info["description"],
                    "rows": []
                }
                for prop in sorted(event_info["properties"]):
                    row = {
                        "key": prop,
                        "type": event_info["properties"][prop]["type"],
                        "desc": event_info["properties"][prop].get("description","")
                    }
                    table["rows"].append(row)
                event_types[event_type] = table
        return event_types

    def load_event_examples(self):
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

    def load_event_schemas(self):
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

            props = obj.get("properties")
            parents = obj.get("allOf")
            if not props and not parents:
                raise Exception(
                    "Object %s has no properties or parents." % obj
                )
            if not props:  # parents only
                return [{
                    "title": obj["title"],
                    "parent": parents[0]["$ref"],
                    "no-table": True
                }]

            for key_name in sorted(props):
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

                        if not nested_object[0].get("no-table"):
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
                        value_type = "[%s]" % props[key_name]["items"]["type"]
                else:
                    value_type = props[key_name]["type"]
                    if props[key_name].get("enum"):
                        if len(props[key_name].get("enum")) > 1:
                            value_type = "enum"
                            desc += (
                                " One of: %s" % json.dumps(props[key_name]["enum"])
                            )
                        else:
                            desc += (
                                " Must be '%s'." % props[key_name]["enum"][0]
                            )

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
            self.log("Reading %s" % os.path.join(path, filename))
            with open(os.path.join(path, filename), "r") as f:
                json_schema = json.loads(f.read())
                schema = {
                    "typeof": None,
                    "typeof_info": "",
                    "type": None,
                    "title": None,
                    "desc": None,
                    "msgtype": None,
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
                    "core#/definitions/room_event": "Message Event",
                    "core#/definitions/state_event": "State Event"
                }
                if type(json_schema.get("allOf")) == list:
                    schema["typeof"] = base_defs.get(
                        json_schema["allOf"][0].get("$ref")
                    )
                elif json_schema.get("title"):
                    schema["typeof"] = json_schema["title"]

                # add type
                schema["type"] = Units.prop(
                    json_schema, "properties/type/enum"
                )[0]

                # add summary and desc
                schema["title"] = json_schema.get("title")
                schema["desc"] = json_schema.get("description", "")

                # walk the object for field info
                schema["content_fields"] = get_content_fields(
                    Units.prop(json_schema, "properties/content")
                )

                # grab msgtype if it is the right kind of event
                msgtype = Units.prop(
                    json_schema, "properties/content/properties/msgtype/enum"
                )
                if msgtype:
                    schema["msgtype"] = msgtype[0]  # enum prop

                # Assign state key info
                if schema["typeof"] == "State Event":
                    skey_desc = Units.prop(
                        json_schema, "properties/state_key/description"
                    )
                    if not skey_desc:
                        raise Exception("Missing description for state_key")
                    schema["typeof_info"] = "``state_key``: %s" % skey_desc

                schemata[filename] = schema
        return schemata

    def load_git_version(self):
        null = open(os.devnull, 'w')
        cwd = os.path.dirname(os.path.abspath(__file__))
        try:
            git_branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                stderr=null,
                cwd=cwd,
            ).strip()
        except subprocess.CalledProcessError:
            git_branch = ""
        try:
            git_tag = subprocess.check_output(
                ['git', 'describe', '--exact-match'],
                stderr=null,
                cwd=cwd,
            ).strip()
            git_tag = "tag=" + git_tag
        except subprocess.CalledProcessError:
            git_tag = ""
        try:
            git_commit = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stderr=null,
                cwd=cwd,
            ).strip()
        except subprocess.CalledProcessError:
            git_commit = ""
        try:
            dirty_string = "-this_is_a_dirty_checkout"
            is_dirty = subprocess.check_output(
                ['git', 'describe', '--dirty=' + dirty_string, "--all"],
                stderr=null,
                cwd=cwd,
            ).strip().endswith(dirty_string)
            git_dirty = "dirty" if is_dirty else ""
        except subprocess.CalledProcessError:
            git_dirty = ""

        if git_branch or git_tag or git_commit or git_dirty:
            git_version = ",".join(
                s for s in
                (git_branch, git_tag, git_commit, git_dirty,)
                if s
            )
            return git_version.encode("ascii")
        return "Unknown rev"
