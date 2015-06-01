"""Contains all the sections for the spec."""
from batesian import AccessKeyStore
from batesian.sections import Sections
import inspect
import json
import os


class MatrixSections(Sections):

    # pass through git ver so it'll be dropped in the input file
    def render_git_version(self):
        return self.units.get("git_version")

    def render_spec_version(self):
        spec_meta = self.units.get("spec_meta")
        return spec_meta["version"]

    def render_spec_changelog(self):
        spec_meta = self.units.get("spec_meta")
        return spec_meta["changelog"]

    def _render_events(self, filterFn, sortFn, title_kind="~"):
        template = self.env.get_template("events.tmpl")
        examples = self.units.get("event_examples")
        schemas = self.units.get("event_schemas")
        sections = []
        for event_name in sortFn(schemas):
            if not filterFn(event_name):
                continue
            sections.append(template.render(
                example=examples[event_name], 
                event=schemas[event_name],
                title_kind=title_kind
            ))
        return "\n\n".join(sections)

    def _render_http_api_group(self, group, sortFn=sorted, title_kind="-"):
        template = self.env.get_template("http-api.tmpl")
        http_api = self.units.get("swagger_apis")[group]["__meta"]
        sections = []
        for endpoint in sortFn(http_api["endpoints"]):
            sections.append(template.render(
                endpoint=endpoint,
                title_kind=title_kind
            ))
        return "\n\n".join(sections)

    def render_profile_http_api(self):
        def sortFn(endpoints):
            ordering = ["displayname", "avatar_url"]
            sorted_endpoints = []
            for path_substr in ordering:
                for e in endpoints:
                    if path_substr in e["path"]:
                        sorted_endpoints.append(e)  # could have multiple
            # dump rest
            rest = [ e for e in endpoints if e not in sorted_endpoints ]
            return sorted_endpoints + rest
        return self._render_http_api_group(
            "profile", sortFn=sortFn, title_kind="+"
        )

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
                example=examples[event_name], 
                event=schemas[event_name]
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
        return self._render_events(filterFn, sorted, title_kind="+")

    def _render_ce_type(self, type):
        template = self.env.get_template("common-event-fields.tmpl")
        ce_types = self.units.get("common_event_fields")
        return template.render(common_event=ce_types[type])

    def render_common_event_fields(self):
        return self._render_ce_type("event")

    def render_common_room_event_fields(self):
        return self._render_ce_type("room_event")

    def render_common_state_event_fields(self):
        return self._render_ce_type("state_event")
