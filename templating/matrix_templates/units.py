# Copyright 2016 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Contains all the units for the spec.

This file loads swagger and JSON schema files and parses out the useful bits
and returns them as Units for use in Batesian.

For the actual conversion of data -> RST (including templates), see the sections
file instead.
"""
from batesian.units import Units
from collections import OrderedDict
import logging
import inspect
import json
import os
import re
import subprocess
import sys
import urllib
import yaml

HTTP_APIS = {
    "../api/application-service": "as",
    "../api/client-server": "cs",
    "../api/identity": "is",
    "../api/push-gateway": "push",
}
EVENT_EXAMPLES = "../event-schemas/examples"
EVENT_SCHEMA = "../event-schemas/schema"
CORE_EVENT_SCHEMA = "../event-schemas/schema/core-event-schema"
CHANGELOG_DIR = "../changelogs"
TARGETS = "../specification/targets.yaml"

ROOM_EVENT = "core-event-schema/room_event.yaml"
STATE_EVENT = "core-event-schema/state_event.yaml"

logger = logging.getLogger(__name__)

# a yaml Loader which loads mappings into OrderedDicts instead of regular
# dicts, so that we preserve the ordering of properties from the api files.
#
# with thanks to http://stackoverflow.com/a/21912744/637864
class OrderedLoader(yaml.Loader):
    pass
def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    pairs = loader.construct_pairs(node)
    return OrderedDict(pairs)
OrderedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_mapping)

def resolve_references(path, schema):
    if isinstance(schema, dict):
        # do $ref first
        if '$ref' in schema:
            value = schema['$ref']
            path = os.path.join(os.path.dirname(path), value)
            with open(path) as f:
                ref = yaml.load(f, OrderedLoader)
            result = resolve_references(path, ref)
            del schema['$ref']
        else:
            result = OrderedDict()

        for key, value in schema.items():
            result[key] = resolve_references(path, value)
        return result
    elif isinstance(schema, list):
        return [resolve_references(path, value) for value in schema]
    else:
        return schema


def inherit_parents(obj):
    """
    Recurse through the 'allOf' declarations in the object
    """
    logger.debug("inherit_parents %r" % obj)
    parents = obj.get("allOf", [])
    if not parents:
        return obj

    result = {}

    # settings defined in the child take priority over the parents, so we
    # iterate through the parents first, and then overwrite with the settings
    # from the child.
    for p in map(inherit_parents, parents) + [obj]:
        for key in ('title', 'type', 'required', 'description'):
            if p.get(key):
                result[key] = p[key]

        for key in ('properties', 'additionalProperties', 'patternProperties'):
            if p.get(key):
                result.setdefault(key, OrderedDict()).update(p[key])

    return result


def get_json_schema_object_fields(obj, enforce_title=False):
    # Algorithm:
    # f.e. property => add field info (if field is object then recurse)
    if obj.get("type") != "object":
        raise Exception(
            "get_json_schema_object_fields: Object %s isn't an object." % obj
        )

    obj_title = obj.get("title")

    logger.debug("Processing object with title '%s'", obj_title)

    additionalProps = obj.get("additionalProperties")
    props = obj.get("properties")
    if additionalProps and not props:
        # not "really" an object, just a KV store
        logger.debug("%s is a pseudo-object", obj_title)

        key_type = additionalProps.get("x-pattern", "string")
        res = process_data_type(additionalProps)
        return {
            "type": "{%s: %s}" % (key_type, res["type"]),
            "tables": res["tables"],
        }

    if not props:
        props = obj.get("patternProperties")
        if props:
            # try to replace horrible regex key names with pretty x-pattern ones
            for key_name in props.keys():
                pretty_key = props[key_name].get("x-pattern")
                if pretty_key:
                    props[pretty_key] = props[key_name]
                    del props[key_name]



    # Sometimes you just want to specify that a thing is an object without
    # doing all the keys.
    if not props:
        return {
            "type": obj_title if obj_title else 'object',
            "tables": [],
        }

    if enforce_title and not obj_title:
        # Force a default titile of "NO_TITLE" to make it obvious in the
        # specification output which parts of the schema are missing a title
        obj_title = 'NO_TITLE'

    required_keys = set(obj.get("required", []))

    first_table_rows = []
    tables = []

    for key_name in props:
        try:
            logger.debug("Processing property %s.%s", obj_title, key_name)
            required = key_name in required_keys
            res = process_data_type(props[key_name], required)

            first_table_rows.append({
                "key": key_name,
                "type": res["type"],
                "required": required,
                "desc": res["desc"],
            })
            tables.extend(res["tables"])
            logger.debug("Done property %s" % key_name)

        except Exception, e:
            e2 = Exception("Error reading property %s.%s: %s" %
                           (obj_title, key_name, str(e)))
            # throw the new exception with the old stack trace, so that
            # we don't lose information about where the error occurred.
            raise e2, None, sys.exc_info()[2]

    tables.insert(0, {
        "title": obj_title,
        "rows": first_table_rows,
    })

    return {
        "type": obj_title,
        "tables": tables,
    }


# process a data type definition. returns a dictionary with the keys:
# type:     stringified type name
# desc:     description
# enum_desc: description of permissible enum fields
# is_object: true if the data type is an object
# tables:   list of additional table definitions
def process_data_type(prop, required=False, enforce_title=True):
    prop = inherit_parents(prop)

    prop_type = prop['type']
    tables = []
    enum_desc = None
    is_object = False

    if prop_type == "object":
        res = get_json_schema_object_fields(
            prop,
            enforce_title=enforce_title,
        )
        prop_type = res["type"]
        tables = res["tables"]
        is_object = True

    elif prop_type == "array":
        nested = process_data_type(prop["items"])
        prop_type = "[%s]" % nested["type"]
        tables = nested["tables"]
        enum_desc = nested["enum_desc"]

    if prop.get("enum"):
        if len(prop["enum"]) > 1:
            prop_type = "enum"
            enum_desc = (
                "One of: %s" % json.dumps(prop["enum"])
            )
        else:
            enum_desc = (
                "Must be '%s'." % prop["enum"][0]
            )

    if isinstance(prop_type, list):
        prop_type = " or ".join(prop_type)


    rq = "**Required.**" if required else None
    desc = " ".join(x for x in [rq, prop.get("description"), enum_desc] if x)

    return {
        "type": prop_type,
        "desc": desc,
        "enum_desc": enum_desc,
        "is_object": is_object,
        "tables": tables,
    }

def deduplicate_tables(tables):
    # the result may contain duplicates, if objects are referred to more than
    # once. Filter them out.
    #
    # Go through the tables backwards so that we end up with a breadth-first
    # rather than depth-first ordering.

    titles = set()
    filtered = []
    for table in reversed(tables):
        if table.get("no-table"):
            continue

        if table.get("title") in titles:
            continue

        titles.add(table.get("title"))
        filtered.append(table)
    filtered.reverse()

    return filtered

def get_tables_for_schema(schema):
    pv = process_data_type(schema, enforce_title=False)
    return deduplicate_tables(pv["tables"])

def get_tables_for_response(schema):
    pv = process_data_type(schema, enforce_title=False)
    tables = deduplicate_tables(pv["tables"])

    # make up the first table, with just the 'body' row in, unless the response
    # is an object, in which case there's little point in having one.
    if not pv["is_object"]:
        tables = [{
            "title": None,
            "rows": [{
                "key": "<body>",
                "type": pv["type"],
                "desc": pv["desc"],
            }]
        }] + tables

    logger.debug("response: %r" % tables)

    return tables

def get_example_for_schema(schema):
    """Returns a python object representing a suitable example for this object"""
    schema = inherit_parents(schema)
    if 'example' in schema:
        example = schema['example']
        return example

    proptype = schema['type']

    if proptype == 'object':
        if 'properties' not in schema:
            raise Exception('"object" property has neither properties nor example')
        res = OrderedDict()
        for prop_name, prop in schema['properties'].iteritems():
            logger.debug("Parsing property %r" % prop_name)
            prop_example = get_example_for_schema(prop)
            res[prop_name] = prop_example
        return res

    if proptype == 'array':
        if 'items' not in schema:
            raise Exception('"array" property has neither items nor example')
        return [get_example_for_schema(schema['items'])]

    if proptype == 'integer':
        return 0

    if proptype == 'string':
        return proptype

    raise Exception("Don't know to make an example %s" % proptype)

def get_example_for_param(param):
    """Returns a stringified example for a parameter"""
    if 'x-example' in param:
        return param['x-example']
    schema = param.get('schema')
    if not schema:
        return None

    # allow examples for the top-level object to be in formatted json
    exampleobj = None
    if 'example' in schema:
        exampleobj = schema['example']
        if isinstance(exampleobj, basestring):
           return exampleobj

    if exampleobj is None:
        exampleobj = get_example_for_schema(schema)

    return json.dumps(exampleobj, indent=2)

def get_example_for_response(response):
    """Returns a stringified example for a response"""
    exampleobj = None
    if 'examples' in response:
        exampleobj = response["examples"].get("application/json")
        # the openapi spec suggests that examples in the 'examples' section should
        # be formatted as raw objects rather than json-formatted strings, but we
        # have lots of the latter in our spec, which work with the swagger UI,
        # so grandfather them in.
        #
        # FIXME: swagger-ui no longer supports this. We should fix the inputs
        # and remove the grandfathering.
        if isinstance(exampleobj, basestring):
            return exampleobj

    if exampleobj is None:
        schema = response.get('schema')
        if schema:
            if schema['type'] == 'file':
                # no example for 'file' responses
                return None
            exampleobj = get_example_for_schema(schema)

    if exampleobj is None:
        return None

    return json.dumps(exampleobj, indent=2)

class MatrixUnits(Units):
    def _load_swagger_meta(self, api, group_name):
        endpoints = []
        for path in api["paths"]:
            for method in api["paths"][path]:
                single_api = api["paths"][path][method]
                full_path = api.get("basePath", "").rstrip("/") + path
                endpoint = {
                    "title": single_api.get("summary", ""),
                    "deprecated": single_api.get("deprecated", False),
                    "desc": single_api.get("description", single_api.get("summary", "")),
                    "method": method.upper(),
                    "path": full_path.strip(),
                    "requires_auth": "security" in single_api,
                    "rate_limited": 429 in single_api.get("responses", {}),
                    "req_param_by_loc": {},
                    "req_body_tables": [],
                    "res_headers": [],
                    "res_tables": [],
                    "responses": [],
                    "example": {
                        "req": "",
                    }
                }
                logger.info(" ------- Endpoint: %s %s ------- " % (method, path))

                path_template = api.get("basePath", "").rstrip("/") + path
                example_query_params = []
                example_body = ""

                for param in single_api.get("parameters", []):
                    # even body params should have names, otherwise the active docs don't work.
                    param_name = param["name"]

                    try:
                        param_loc = param["in"]

                        if param_loc == "body":
                            self._handle_body_param(param, endpoint)
                            example_body = get_example_for_param(param)
                            continue

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

                        endpoint["req_param_by_loc"].setdefault(param_loc, []).append({
                            "key": param_name,
                            "type": val_type,
                            "desc": desc
                        })

                        example = get_example_for_param(param)
                        if example is None:
                            continue

                        if param_loc == "path":
                            path_template = path_template.replace(
                                "{%s}" % param_name, urllib.quote(example)
                            )
                        elif param_loc == "query":
                            if type(example) == list:
                                for value in example:
                                    example_query_params.append((param_name, value))
                            else:
                                example_query_params.append((param_name, example))

                    except Exception, e:
                        raise Exception("Error handling parameter %s" % param_name, e)
                # endfor[param]

                good_response = None
                for code in sorted(single_api.get("responses", {}).keys()):
                    res = single_api["responses"][code]
                    if not good_response and code == 200:
                        good_response = res
                    description = res.get("description", "")
                    example = get_example_for_response(res)
                    endpoint["responses"].append({
                        "code": code,
                        "description": description,
                        "example": example,
                    })

                # add response params if this API has any.
                if good_response:
                    if "schema" in good_response:
                        endpoint["res_tables"] = get_tables_for_response(
                            good_response["schema"]
                        )
                    if "headers" in good_response:
                        headers = []
                        for (header_name, header) in good_response["headers"].iteritems():
                            headers.append({
                                "key": header_name,
                                "type": header["type"],
                                "desc": header["description"],
                            })
                        endpoint["res_headers"] = headers

                query_string = "" if len(example_query_params) == 0 else "?"+urllib.urlencode(example_query_params)
                if example_body:
                    endpoint["example"]["req"] = "%s %s%s HTTP/1.1\nContent-Type: application/json\n\n%s" % (
                        method.upper(), path_template, query_string, example_body
                    )
                else:
                    endpoint["example"]["req"] = "%s %s%s HTTP/1.1\n\n" % (
                        method.upper(), path_template, query_string
                    )

                endpoints.append(endpoint)

        return {
            "base": api.get("basePath").rstrip("/"),
            "group": group_name,
            "endpoints": endpoints,
        }


    def _handle_body_param(self, param, endpoint_data):
        """Update endpoint_data object with the details of the body param
        :param string filepath       path to the yaml
        :param dict   param          the parameter data from the yaml
        :param dict   endpoint_data  dictionary of endpoint data to be updated
        """
        try:
            schema = inherit_parents(param["schema"])
            if schema["type"] != "object":
                logger.warn(
                    "Unsupported body type %s for %s %s", schema["type"],
                    endpoint_data["method"], endpoint_data["path"]
                )
                return

            req_body_tables = get_tables_for_schema(schema)

            if req_body_tables == []:
                # no fields defined for the body.
                return

            # put the top-level parameters into 'req_param_by_loc', and the others
            # into 'req_body_tables'
            body_params = endpoint_data['req_param_by_loc'].setdefault("JSON body",[])
            body_params.extend(req_body_tables[0]["rows"])

            body_tables = req_body_tables[1:]
            endpoint_data['req_body_tables'].extend(body_tables)

        except Exception, e:
            e2 = Exception(
                "Error decoding body of API endpoint %s %s: %s" %
                (endpoint_data["method"], endpoint_data["path"], e)
            )
            raise e2, None, sys.exc_info()[2]


    def load_swagger_apis(self):
        apis = {}
        for path, suffix in HTTP_APIS.items():
            for filename in os.listdir(path):
                if not filename.endswith(".yaml"):
                    continue
                logger.info("Reading swagger API: %s" % filename)
                filepath = os.path.join(path, filename)
                with open(filepath, "r") as f:
                    # strip .yaml
                    group_name = filename[:-5].replace("-", "_")
                    group_name = "%s_%s" % (group_name, suffix)
                    api = yaml.load(f.read(), OrderedLoader)
                    api = resolve_references(filepath, api)
                    api["__meta"] = self._load_swagger_meta(
                        api, group_name
                    )
                    apis[group_name] = api
        return apis

    def load_common_event_fields(self):
        path = CORE_EVENT_SCHEMA
        event_types = {}

        for (root, dirs, files) in os.walk(path):
            for filename in files:
                if not filename.endswith(".yaml"):
                    continue

                event_type = filename[:-5]  # strip the ".yaml"
                filepath = os.path.join(root, filename)
                with open(filepath) as f:
                    try:
                        event_info = yaml.load(f, OrderedLoader)
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

    def load_apis(self, substitutions):
        cs_ver = substitutions.get("%CLIENT_RELEASE_LABEL%", "unstable")
        fed_ver = substitutions.get("%SERVER_RELEASE_LABEL%", "unstable")
        return {
            "rows": [{
                "key": "`Client-Server API <client_server/"+cs_ver+".html>`_",
                "type": cs_ver,
                "desc": "Interaction between clients and servers",
            }, {
                "key": "`Server-Server API <server_server/"+fed_ver+".html>`_",
                "type": fed_ver,
                "desc": "Federation between servers",
            }, {
                "key": "`Application Service API <application_service/unstable.html>`_",
                "type": "unstable",
                "desc": "Privileged server plugins",
            }, {
                "key": "`Identity Service API <identity_service/unstable.html>`_",
                "type": "unstable",
                "desc": "Mapping of third party IDs to Matrix IDs",
            }, {
                "key": "`Push Gateway API <push_gateway/unstable.html>`_",
                "type": "unstable",
                "desc": "Push notifications for Matrix events",
            }]
        }

    def load_event_examples(self):
        path = EVENT_EXAMPLES
        examples = {}
        for filename in os.listdir(path):
            if not filename.startswith("m."):
                continue
            with open(os.path.join(path, filename), "r") as f:
                event_name = filename.split("#")[0]
                example = json.loads(f.read())

                examples[filename] = examples.get(filename, [])
                examples[filename].append(example)
                if filename != event_name:
                    examples[event_name] = examples.get(event_name, [])
                    examples[event_name].append(example)
        return examples

    def load_event_schemas(self):
        path = EVENT_SCHEMA
        schemata = {}

        for filename in os.listdir(path):
            if not filename.startswith("m."):
                continue
            filepath = os.path.join(path, filename)
            try:
                schemata[filename] = self.read_event_schema(filepath)
            except Exception, e:
                e2 = Exception("Error reading event schema "+filepath+": "+
                               str(e))
                # throw the new exception with the old stack trace, so that
                # we don't lose information about where the error occurred.
                raise e2, None, sys.exc_info()[2]

        return schemata

    def read_event_schema(self, filepath):
        logger.info("Reading %s" % filepath)

        with open(filepath, "r") as f:
            json_schema = yaml.load(f, OrderedLoader)

        schema = {
            "typeof": "",
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
            firstRef = json_schema["allOf"][0]["$ref"]
            if firstRef in base_defs:
                schema["typeof"] = base_defs[firstRef]

        json_schema = resolve_references(filepath, json_schema)

        # add type
        schema["type"] = Units.prop(
            json_schema, "properties/type/enum"
        )[0]

        # add summary and desc
        schema["title"] = json_schema.get("title")
        schema["desc"] = json_schema.get("description", "")

        # walk the object for field info
        schema["content_fields"] = get_tables_for_schema(
            Units.prop(json_schema, "properties/content")
        )

        # This is horrible because we're special casing a key on m.room.member.
        # We need to do this because we want to document a non-content object.
        if schema["type"] == "m.room.member":
            invite_room_state = get_tables_for_schema(
                json_schema["properties"]["invite_room_state"]["items"],
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

        return schema

    def load_changelogs(self):
        changelogs = {}

        for f in os.listdir(CHANGELOG_DIR):
            if not f.endswith(".rst"):
                continue
            path = os.path.join(CHANGELOG_DIR, f)
            name = f[:-4]

            title_part = None
            changelog_lines = []
            with open(path, "r") as f:
                lines = f.readlines()
            prev_line = None
            for line in lines:
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
                    changelog_lines.append("    " + line)
            changelogs[name] = "".join(changelog_lines)

        return changelogs


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
