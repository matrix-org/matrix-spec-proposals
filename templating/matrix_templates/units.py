"""Contains all the units for the spec."""
from batesian.units import Units
import inspect
import json
import os
import re
import subprocess
import urllib
import yaml

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


class MatrixUnits(Units):

    def _load_swagger_meta(self, api, group_name):
        endpoints = []
        for path in api["paths"]:
            for method in api["paths"][path]:
                single_api = api["paths"][path][method]
                endpoint = {
                    "title": single_api.get("summary", ""),
                    "desc": single_api.get("description", single_api.get("summary", "")),
                    "method": method.upper(),
                    "path": api.get("basePath", "") + path,
                    "requires_auth": "security" in single_api,
                    "rate_limited": 429 in single_api.get("responses", {}),
                    "req_params": [],
                    "res_params": [],
                    "example": {
                        "req": "",
                        "res": ""
                    }
                }
                self.log(".o.O.o. Endpoint: %s %s" % (method, path))
                for param in single_api.get("parameters", []):
                    # description
                    desc = param.get("description", "")
                    if param.get("required"):
                        desc = "**Required.** " + desc

                    # assign value expected for this param
                    val_type = param.get("type") # integer/string
                    refType = Units.prop(param, "schema/$ref/") # Error,Event
                    schemaFmt = Units.prop(param, "schema/format") # bytes e.g. uploads
                    if not val_type and refType:
                        val_type = refType  # TODO: Resolve to human-readable.
                    if not val_type and schemaFmt:
                        val_type = schemaFmt
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
                            "API endpoint group=%s path=%s method=%s param=%s"+
                            " has no valid parameter value." % (
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
                    for key in json_body:
                        endpoint["req_params"].append({
                            "key": key,
                            "loc": "JSON body",
                            "type": json_body[key]["type"],
                            "desc": json_body[key]["description"]
                        })
                # endfor[param]
                # group params by location to ease templating
                endpoint["req_param_by_loc"] = {
                    #   path: [...], query: [...], body: [...]
                }
                for p in endpoint["req_params"]:
                    if p["loc"] not in endpoint["req_param_by_loc"]:
                        endpoint["req_param_by_loc"][p["loc"]] = []
                    endpoint["req_param_by_loc"][p["loc"]].append(p)

                # add example response if it has one
                res = single_api["responses"][200]  # get the 200 OK response
                endpoint["example"]["res"] = res.get("examples", {}).get(
                    "application/json", ""
                )
                # form example request if it has one. It "has one" if all params
                # have either "x-example" or a "schema" with an "example".
                params_missing_examples = [
                    p for p in single_api.get("parameters", []) if (
                        "x-example" not in p and 
                        not Units.prop(p, "schema/example")
                    )
                ]
                if len(params_missing_examples) == 0:
                    path_template = api.get("basePath", "") + path
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
                    endpoint["example"]["req"] = "%s %s%s\n%s" % (
                        method.upper(), path_template, query_string, body
                    )
                else:
                    self.log(
                        "The following parameters are missing examples :( \n %s" %
                        [ p["name"] for p in params_missing_examples ]
                    )

                # add response params if this API has any.
                res_type = Units.prop(res, "schema/type")
                if res_type and res_type not in ["object", "array"]:
                    # response is a raw string or something like that
                    endpoint["res_params"].append({
                        "key": res["schema"].get("name", ""),
                        "type": res_type,
                        "desc": res.get("description", "")
                    })
                elif res_type and Units.prop(res, "schema/properties"):  # object
                    res_tables = get_json_schema_object_fields(res["schema"])
                    # TODO: Is this good enough or should we be doing multiple
                    # tables for HTTP responses?!
                    endpoint["res_params"] = res_tables[0]["rows"]

                endpoints.append(endpoint)

        return {
            "base": api.get("basePath"),
            "group": group_name,
            "endpoints": endpoints,
        }

    def load_swagger_apis(self):
        path = "../api/client-server/v1"
        apis = {}
        for filename in os.listdir(path):
            if not filename.endswith(".yaml"):
                continue
            self.log("Reading swagger API: %s" % filename)
            with open(os.path.join(path, filename), "r") as f:
                # strip .yaml
                group_name = filename[:-5]
                api = yaml.load(f.read())
                api["__meta"] = self._load_swagger_meta(api, group_name)
                apis[group_name] = api
        return apis

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
                schema["content_fields"] = get_json_schema_object_fields(
                    Units.prop(json_schema, "properties/content")
                )

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
        path = "../CHANGELOG.rst"
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

        self.log("Version: %s Title part: %s Changelog lines: %s" % (
            version, title_part, len(changelog_lines)
        ))
        if not version or len(changelog_lines) == 0:
            raise Exception("Failed to parse CHANGELOG.rst")

        return {
            "version": version,
            "changelog": "".join(changelog_lines)
        }

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
