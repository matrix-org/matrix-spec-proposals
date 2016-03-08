"""Contains all the sections for the spec."""
from batesian import AccessKeyStore
from batesian.sections import Sections
import inspect
import json
import os


class MatrixSections(Sections):

    # pass through git ver so it'll be dropped in the input file
    def render_git_version(self):
        return self.units.get("git_version")["string"]

    def render_git_rev(self):
        return self.units.get("git_version")["revision"]

    def render_client_server_changelog(self):
        changelogs = self.units.get("changelogs")
        return changelogs["client_server"]

    def _render_events(self, filterFn, sortFn):
        template = self.env.get_template("events.tmpl")
        examples = self.units.get("event_examples")
        schemas = self.units.get("event_schemas")
        subtitle_title_char = self.units.get("spec_targets")[
            "relative_title_styles"
        ]["subtitle"]
        sections = []
        for event_name in sortFn(schemas):
            if not filterFn(event_name):
                continue
            sections.append(template.render(
                examples=examples[event_name],
                event=schemas[event_name],
                title_kind=subtitle_title_char
            ))
        return "\n\n".join(sections)

    def _render_http_api_group(self, group, sortFnOrPathList=None):
        template = self.env.get_template("http-api.tmpl")
        http_api = self.units.get("swagger_apis")[group]["__meta"]
        subtitle_title_char = self.units.get("spec_targets")[
            "relative_title_styles"
        ]["subtitle"]
        sections = []
        endpoints = []
        if sortFnOrPathList:
            if isinstance(sortFnOrPathList, list):
                # list of substrings to sort by
                sorted_endpoints = []
                for path_substr in sortFnOrPathList:
                    for e in http_api["endpoints"]:
                        if path_substr in e["path"]:
                            sorted_endpoints.append(e)  # could have multiple
                # dump rest
                rest = [
                    e for e in http_api["endpoints"] if e not in sorted_endpoints
                ]
                endpoints = sorted_endpoints + sorted(rest, key=lambda k: k["path"])
            else:
                # guess it's a func, call it.
                endpoints = sortFnOrPathList(http_api["endpoints"])
        else:
            # sort alphabetically based on path
            endpoints = sorted(http_api["endpoints"], key=lambda k: k["path"])

        for endpoint in endpoints:
            sections.append(template.render(
                endpoint=endpoint,
                title_kind=subtitle_title_char
            ))
        return "\n\n".join(sections)


    # Special function: Returning a dict will specify multiple sections where
    # the key is the section name and the value is the value of the section
    def render_group_http_apis(self):
        # map all swagger_apis to the form $GROUP_http_api
        swagger_groups = self.units.get("swagger_apis").keys()
        renders = {}
        for group in swagger_groups:
            sortFnOrPathList = None
            if group == "presence_cs":
                sortFnOrPathList = ["status"]
            elif group == "profile_cs":
                sortFnOrPathList=["displayname", "avatar_url"]
            renders[group + "_http_api"] = self._render_http_api_group(
                group, sortFnOrPathList
            )
        return renders

    # Special function: Returning a dict will specify multiple sections where
    # the key is the section name and the value is the value of the section
    def render_group_events(self):
        # map all event schemata to the form $EVENTTYPE_event with s/./_/g
        # e.g. m_room_topic_event
        schemas = self.units.get("event_schemas")
        renders = {}
        for event_type in schemas:
            renders[event_type.replace(".", "_") + "_event"] = self._render_events(
                lambda x: x == event_type, sorted
            )
        return renders

    def render_room_events(self):
        def filterFn(eventType):
            return (
                eventType.startswith("m.room") and 
                not eventType.startswith("m.room.message#m.")
            )
        return self._render_events(filterFn, sorted)

    def render_msgtype_events(self):
        template = self.env.get_template("msgtypes.tmpl")
        examples = self.units.get("event_examples")
        schemas = self.units.get("event_schemas")
        subtitle_title_char = self.units.get("spec_targets")[
            "relative_title_styles"
        ]["subtitle"]
        sections = []
        msgtype_order = [
            "m.room.message#m.text", "m.room.message#m.emote",
            "m.room.message#m.notice", "m.room.message#m.image",
            "m.room.message#m.file"
        ]
        other_msgtypes = [
            k for k in schemas.keys() if k.startswith("m.room.message#") and
            k not in msgtype_order
        ]
        for event_name in (msgtype_order + other_msgtypes):
            if not event_name.startswith("m.room.message#m."):
                continue
            sections.append(template.render(
                example=examples[event_name][0],
                event=schemas[event_name],
                title_kind=subtitle_title_char
            ))
        return "\n\n".join(sections)

    def render_voip_events(self):
        def filterFn(eventType):
            return eventType.startswith("m.call")
        def sortFn(eventTypes):
            ordering = [
                "m.call.invite", "m.call.candidates", "m.call.answer",
                "m.call.hangup"
            ]
            rest = [
                k for k in eventTypes if k not in ordering
            ]
            return ordering + rest
        return self._render_events(filterFn, sortFn)

    def render_presence_events(self):
        def filterFn(eventType):
            return eventType.startswith("m.presence")
        return self._render_events(filterFn, sorted)

    def _render_ce_type(self, type):
        template = self.env.get_template("common-event-fields.tmpl")
        ce_types = self.units.get("common_event_fields")
        subtitle_title_char = self.units.get("spec_targets")[
            "relative_title_styles"
        ]["subtitle"]
        return template.render(
            common_event=ce_types[type], title_kind=subtitle_title_char
        )

    def render_common_event_fields(self):
        return self._render_ce_type("event")

    def render_common_room_event_fields(self):
        return self._render_ce_type("room_event")

    def render_common_state_event_fields(self):
        return self._render_ce_type("state_event")

