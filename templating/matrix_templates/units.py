"""
Contains all the units for the spec.

This file loads swagger and JSON schema files and parses out the useful bits
and returns them as Units for use in Batesian.

For the actual conversion of data -> RST (including templates), see the sections
file instead.
"""
from batesian.units import Units
import inspect
import json
import os
import re
import subprocess
import urllib
import yaml

V1_CLIENT_API = "../api/client-server/v1"
V1_EVENT_EXAMPLES = "../event-schemas/examples/v1"
V1_EVENT_SCHEMA = "../event-schemas/schema/v1"
V2_CLIENT_API = "../api/client-server/v2_alpha"
CORE_EVENT_SCHEMA = "../event-schemas/schema/v1/core-event-schema"
CHANGELOG = "../CHANGELOG.rst"
TARGETS = "../specification/targets.yaml"

ROOM_EVENT = "core-event-schema/room_event.json"
STATE_EVENT = "core-event-schema/state_event.json"


def get_json_schema_object_fields(obj, enforce_title=False):
    # Algorithm:
    # f.e. property => add field info (if field is object then recurse)
    if obj.get("type") != "object":
        raise Exception(
            "get_json_schema_object_fields: Object %s isn't an object." % obj
        )
    if enforce_title and not obj.get("title"):
        raise Exception(
            "get_json_schema_object_fields: Nested object %s doesn't have a title." % obj
        )

    required_keys = obj.get("required")
    if not required_keys:
        required_keys = []

    fields = {
        "title": obj.get("title"),
        "rows": []
    }
    tables = [fields]

    parents = obj.get("allOf")
    props = obj.get("properties")
    if not props:
        props = obj.get("patternProperties")
        if props:
            # try to replace horrible regex key names with pretty x-pattern ones
            for key_name in props.keys():
                pretty_key = props[key_name].get("x-pattern")
                if pretty_key:
                    props[pretty_key] = props[key_name]
                    del props[key_name]
    if not props and not parents:
        # Sometimes you just want to specify that a thing is an object without
        # doing all the keys. Allow people to do that if they set a 'title'.
        if obj.get("title"):
            parents = [{
                "$ref": obj.get("title")
            }]
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
                prop_val = props[key_name]["additionalProperties"]["type"]
                if prop_val == "object":
                    nested_object = get_json_schema_object_fields(
                        props[key_name]["additionalProperties"],
                        enforce_title=True
                    )
                    key = props[key_name]["additionalProperties"].get(
                        "x-pattern", "string"
                    )
                    value_type = "{%s: %s}" % (key, nested_object[0]["title"])
                    if not nested_object[0].get("no-table"):
                        tables += nested_object
                else:
                    value_type = "{string: %s}" % prop_val
            else:
                nested_object = get_json_schema_object_fields(
                    props[key_name], 
                    enforce_title=True
                )
                value_type = "{%s}" % nested_object[0]["title"]

                if not nested_object[0].get("no-table"):
                    tables += nested_object
        elif props[key_name]["type"] == "array":
            # if the items of the array are objects then recurse
            if props[key_name]["items"]["type"] == "object":
                nested_object = get_json_schema_object_fields(
                    props[key_name]["items"], 
                    enforce_title=True
                )
                value_type = "[%s]" % nested_object[0]["title"]
                tables += nested_object
            else:
                value_type = "[%s]" % props[key_name]["items"]["type"]
                array_enums = props[key_name]["items"].get("enum")
                if array_enums:
                    if len(array_enums) > 1:
                        value_type = "[enum]"
                        desc += (
                            " One of: %s" % json.dumps(array_enums)
                        )
                    else:
                        desc += (
                            " Must be '%s'." % array_enums[0]
                        )
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
            if isinstance(value_type, list):
                value_type = " or ".join(value_type)

        fields["rows"].append({
            "key": key_name,
            "type": value_type,
            "required": required,
            "desc": desc,
            "req_str": "**Required.** " if required else ""
        })
    return tables


class MatrixUnits(Units):

    def _load_swagger_meta(self, api, group_name):
        endpoints = []
        for path in api["paths"]:
            for method in api["paths"][path]:
                single_api = api["paths"][path][method]
                full_path = api.get("basePath", "").rstrip("/") + path
                endpoint = {
                    "title": single_api.get("summary", ""),
                    "desc": single_api.get("description", single_api.get("summary", "")),
                    "method": method.upper(),
                    "path": full_path.strip(),
                    "requires_auth": "security" in single_api,
                    "rate_limited": 429 in single_api.get("responses", {}),
                    "req_params": [],
                    "res_tables": [],
                    "example": {
                        "req": "",
                        "responses": [],
                        "good_response": ""
                    }
                }
                self.log(" ------- Endpoint: %s %s ------- " % (method, path))
                for param in single_api.get("parameters", []):
                    # description
                    desc = param.get("description", "")
                    if param.get("required"):
                        desc = "**Required.** " + desc

                    # assign value expected for this param
                    val_type = param.get("type") # integer/string

                    if param.get("enum"):
                        val_type = "enum"
                        desc += (
                            " One of: %s" % json.dumps(param.get("enum"))
                        )

                    refType = Units.prop(param, "schema/$ref/") # Error,Event
                    schemaFmt = Units.prop(param, "schema/format") # bytes e.g. uploads
                    if not val_type and refType:
                        val_type = refType  # TODO: Resolve to human-readable.
                    if not val_type and schemaFmt:
                        val_type = schemaFmt
                    # handle top-level strings/bools
                    if not val_type and Units.prop(param, "schema/type") == "string":
                        val_type = "string"
                    if not val_type and Units.prop(param, "schema/type") == "boolean":
                        val_type = "boolean"
                    if val_type:
                        endpoint["req_params"].append({
                            "key": param["name"],
                            "loc": param["in"],
                            "type": val_type,
                            "desc": desc
                        })
                        continue
                    # If we're here, either the param has no value or it is an
                    # object which we haven't $reffed (so probably just a json
                    # object with some keys; we'll add entries f.e one)
                    if "schema" not in param:
                        raise Exception(
                            ("API endpoint group=%s path=%s method=%s param=%s"+
                            " has no valid parameter value.") % (
                                group_name, path, method, param
                            )
                        )
                    if Units.prop(param, "schema/type") != "object":
                        raise Exception(
                            ("API endpoint group=%s path=%s method=%s defines a"+
                            " param with a schema which isn't an object. Array?")
                            % (group_name, path, method)
                        )
                    # loop top-level json keys
                    json_body = Units.prop(param, "schema/properties")
                    required_params = []
                    if Units.prop(param, "schema/required"):
                        required_params = Units.prop(param, "schema/required")
                    for key in json_body:
                        req_obj = json_body[key]
                        pdesc = req_obj["description"]
                        if key in required_params:
                            pdesc = "**Required.** " + pdesc

                        is_array = req_obj["type"] == "array"
                        is_array_of_objects = (
                            is_array and req_obj["items"]["type"] == "object"
                        )
                        endpoint["req_params"].append({
                            "key": key,
                            "loc": "JSON body",
                            "type": (
                                req_obj["type"] if not is_array else
                                "array[%s]" % req_obj["items"]["type"]
                            ),
                            "desc": pdesc
                        })
                        if not is_array_of_objects and req_obj["type"] == "array":
                            continue
                        # Put in request.dot.notation for nested keys
                        if req_obj["type"] in ["object", "array"]:
                            if is_array_of_objects:
                                req_obj = req_obj["items"]

                            req_tables = get_json_schema_object_fields(req_obj)

                            if req_tables > 1:
                                for table in req_tables[1:]:
                                    nested_key_name = [
                                        s["key"] for s in req_tables[0]["rows"] if
                                        s["type"] == ("{%s}" % (table["title"],))
                                    ][0]
                                    for row in table["rows"]:
                                        row["key"] = "%s.%s" % (nested_key_name, row["key"])

                            key_sep = "[0]." if is_array else "."
                            for table in req_tables:
                                if table.get("no-table"):
                                    continue
                                for row in table["rows"]:
                                    nested_key = key + key_sep + row["key"]
                                    endpoint["req_params"].append({
                                        "key": nested_key,
                                        "loc": "JSON body",
                                        "type": row["type"],
                                        "desc": row["req_str"] + row["desc"]
                                    })

                # endfor[param]
                for row in endpoint["req_params"]:
                    self.log("Request parameter: %s" % row)

                # group params by location to ease templating
                endpoint["req_param_by_loc"] = {
                    #   path: [...], query: [...], body: [...]
                }
                for p in endpoint["req_params"]:
                    if p["loc"] not in endpoint["req_param_by_loc"]:
                        endpoint["req_param_by_loc"][p["loc"]] = []
                    endpoint["req_param_by_loc"][p["loc"]].append(p)

                good_response = None
                for code, res in single_api.get("responses", {}).items():
                    if not good_response and code == 200:
                        good_response = res
                    description = res.get("description", "")
                    example = res.get("examples", {}).get("application/json", "")
                    if description and example:
                        endpoint["example"]["responses"].append({
                            "code": code,
                            "description": description,
                            "example": example,
                        })

                # form example request if it has one. It "has one" if all params
                # have either "x-example" or a "schema" with an "example".
                params_missing_examples = [
                    p for p in single_api.get("parameters", []) if (
                        "x-example" not in p and 
                        not Units.prop(p, "schema/example")
                    )
                ]
                if len(params_missing_examples) == 0:
                    path_template = api.get("basePath", "").rstrip("/") + path
                    qps = {}
                    body = ""
                    for param in single_api.get("parameters", []):
                        if param["in"] == "path":
                            path_template = path_template.replace(
                                "{%s}" % param["name"], urllib.quote(
                                    param["x-example"]
                                )
                            )
                        elif param["in"] == "body":
                            body = param["schema"]["example"]
                        elif param["in"] == "query":
                            qps[param["name"]] = param["x-example"]
                    query_string = "" if len(qps) == 0 else "?"+urllib.urlencode(qps)
                    if body:
                        endpoint["example"]["req"] = "%s %s%s HTTP/1.1\nContent-Type: application/json\n\n%s" % (
                            method.upper(), path_template, query_string, body
                        )
                    else:
                        endpoint["example"]["req"] = "%s %s%s HTTP/1.1\n\n" % (
                            method.upper(), path_template, query_string
                        )

                else:
                    self.log(
                        "The following parameters are missing examples :( \n %s" %
                        [ p["name"] for p in params_missing_examples ]
                    )

                # add response params if this API has any.
                if good_response:
                    self.log("Found a 200 response for this API")
                    res_type = Units.prop(good_response, "schema/type")
                    res_name = Units.prop(good_response, "schema/name")
                    if res_type and res_type not in ["object", "array"]:
                        # response is a raw string or something like that
                        good_table = {
                            "title": None,
                            "rows": [{
                                "key": "<" + res_type + ">" if not res_name else res_name,
                                "type": res_type,
                                "desc": res.get("description", ""),
                                "req_str": ""
                            }]
                        }
                        if good_response.get("headers"):
                            for (header_name, header) in good_response.get("headers").iteritems():
                                good_table["rows"].append({
                                    "key": header_name,
                                    "type": "Header<" + header["type"] + ">",
                                    "desc": header["description"],
                                    "req_str": ""
                                })
                        endpoint["res_tables"].append(good_table)
                    elif res_type and Units.prop(good_response, "schema/properties"):
                        # response is an object:
                        schema = good_response["schema"]
                        res_tables = get_json_schema_object_fields(schema)
                        for table in res_tables:
                            if "no-table" not in table:
                                endpoint["res_tables"].append(table)
                    elif res_type and Units.prop(good_response, "schema/items"):
                        # response is an array:
                        # FIXME: Doesn't recurse at all.
                        schema = good_response["schema"]
                        array_type = Units.prop(schema, "items/type")
                        if Units.prop(schema, "items/allOf"):
                            array_type = (
                                Units.prop(schema, "items/title")
                            )
                        endpoint["res_tables"].append({
                            "title": schema.get("title", ""),
                            "rows": [{
                                "key": "N/A",
                                "type": ("[%s]" % array_type),
                                "desc": schema.get("description", ""),
                                "req_str": ""
                            }]
                        })

                for response_table in endpoint["res_tables"]:
                    self.log("Response: %s" % response_table["title"])
                    for r in response_table["rows"]:
                        self.log("Row: %s" % r)
                if len(endpoint["res_tables"]) == 0:
                    self.log(
                        "This API appears to have no response table. Are you " +
                        "sure this API returns no parameters?"
                    )

                endpoints.append(endpoint)

                aliases = single_api.get("x-alias", None)
                if aliases:
                    alias_link = aliases["canonical-link"]
                    for alias in aliases["aliases"]:
                        endpoints.append({
                            "method": method.upper(),
                            "path": alias,
                            "alias_for_path": full_path,
                            "alias_link": alias_link
                        })

        return {
            "base": api.get("basePath").rstrip("/"),
            "group": group_name,
            "endpoints": endpoints,
        }

    def load_swagger_apis(self):
        paths = [
            V1_CLIENT_API, V2_CLIENT_API
        ]
        apis = {}
        for path in paths:
            is_v2 = (path == V2_CLIENT_API)
            if not os.path.exists(V2_CLIENT_API):
                self.log("Skipping v2 apis: %s does not exist." % V2_CLIENT_API)
                continue
            for filename in os.listdir(path):
                if not filename.endswith(".yaml"):
                    continue
                self.log("Reading swagger API: %s" % filename)
                with open(os.path.join(path, filename), "r") as f:
                    # strip .yaml
                    group_name = filename[:-5].replace("-", "_")
                    if is_v2:
                        group_name = "v2_" + group_name
                    api = yaml.load(f.read())
                    api["__meta"] = self._load_swagger_meta(api, group_name)
                    apis[group_name] = api
        return apis

    def load_common_event_fields(self):
        path = CORE_EVENT_SCHEMA
        event_types = {}

        for (root, dirs, files) in os.walk(path):
            for filename in files:
                if not filename.endswith(".json"):
                    continue

                event_type = filename[:-5]  # strip the ".json"
                filepath = os.path.join(root, filename)
                with open(filepath) as f:
                    try:
                        event_info = json.load(f)
                    except Exception as e:
                        raise ValueError(
                            "Error reading file %r" % (filepath,), e
                        )

                if "event" not in event_type:
                    continue  # filter ImageInfo and co

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
        path = V1_EVENT_EXAMPLES
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
        path = V1_EVENT_SCHEMA
        schemata = {}

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
                    ROOM_EVENT: "Message Event",
                    STATE_EVENT: "State Event"
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
                schema["content_fields"] = get_json_schema_object_fields(
                    Units.prop(json_schema, "properties/content")
                )

                # This is horrible because we're special casing a key on m.room.member.
                # We need to do this because we want to document a non-content object.
                if schema["type"] == "m.room.member":
                    invite_room_state = get_json_schema_object_fields(
                        json_schema["properties"]["invite_room_state"]["items"]
                    )
                    schema["content_fields"].extend(invite_room_state)


                # grab msgtype if it is the right kind of event
                msgtype = Units.prop(
                    json_schema, "properties/content/properties/msgtype/enum"
                )
                if msgtype:
                    schema["msgtype"] = msgtype[0]  # enum prop

                # link to msgtypes for m.room.message
                if schema["type"] == "m.room.message" and not msgtype:
                    schema["desc"] += (
                        " For more information on ``msgtypes``, see "+
                        "`m.room.message msgtypes`_."
                    )

                # Assign state key info if it has some
                if schema["typeof"] == "State Event":
                    skey_desc = Units.prop(
                        json_schema, "properties/state_key/description"
                    )
                    if not skey_desc:
                        raise Exception("Missing description for state_key")
                    schema["typeof_info"] = "``state_key``: %s" % skey_desc

                schemata[filename] = schema
        return schemata

    def load_spec_meta(self):
        path = CHANGELOG
        title_part = None
        version = None
        changelog_lines = []
        with open(path, "r") as f:
            prev_line = None
            for line in f.readlines():
                if line.strip().startswith(".. "):
                    continue  # comment
                if prev_line is None:
                    prev_line = line
                    continue
                if not title_part:
                    # find the title underline (at least 3 =)
                    if re.match("^[=]{3,}$", line.strip()):
                        title_part = prev_line
                        continue
                    prev_line = line
                else:  # have title, get body (stop on next title or EOF)
                    if re.match("^[=]{3,}$", line.strip()):
                        # we added the title in the previous iteration, pop it
                        # then bail out.
                        changelog_lines.pop()
                        break
                    changelog_lines.append(line)

        # parse out version from title
        for word in title_part.split():
            if re.match("^v[0-9\.]+$", word):
                version = word[1:]  # strip the 'v'

        self.log("Version: %s Title part: %s Changelog line count: %s" % (
            version, title_part, len(changelog_lines)
        ))
        if not version or len(changelog_lines) == 0:
            raise Exception("Failed to parse CHANGELOG.rst")

        return {
            "version": version,
            "changelog": "".join(changelog_lines)
        }


    def load_spec_targets(self):
        with open(TARGETS, "r") as f:
            return yaml.load(f.read())


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

        git_version = "Unknown"
        if git_branch or git_tag or git_commit or git_dirty:
            git_version = ",".join(
                s for s in
                (git_branch, git_tag, git_commit, git_dirty,)
                if s
            ).encode("ascii")
        return {
            "string": git_version,
            "revision": git_commit
        }
