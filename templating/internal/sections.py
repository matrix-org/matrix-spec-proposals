"""Contains all the sections for the spec."""
from . import AccessKeyStore
import inspect
import os


class Sections(object):
    """A class which creates sections for each method starting with "render_".
    The key for the section is the text after "render_"
    e.g. "render_room_events" has the section key "room_events"
    """

    def __init__(self, env, units, debug=False):
        self.env = env
        self.units = units
        self.debug = debug

    def log(self, text):
        if self.debug:
            print text

    def get_sections(self):
        render_list = inspect.getmembers(self, predicate=inspect.ismethod)
        section_dict = {}
        for (func_name, func) in render_list:
            if not func_name.startswith("render_"):
                continue
            section_key = func_name[len("render_"):]
            section = func()
            section_dict[section_key] = section
            self.log("Generated section '%s' : %s" % (
                section_key, section[:60].replace("\n","")
            ))
        return section_dict

    def render_room_events(self):
        template = self.env.get_template("events.tmpl")
        examples = self.units.get("event_examples")
        schemas = self.units.get("event_schemas")
        sections = []
        for event_name in sorted(schemas):
            if not event_name.startswith("m.room"):
                continue
            sections.append(template.render(
                example=examples[event_name], 
                event=schemas[event_name]
            ))
        return "\n\n".join(sections)

    # pass through git ver so it'll be dropped in the input file
    def render_git_version(self):
        return self.units.get("git_version")

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


def load(env, units):
    store = AccessKeyStore()
    sections = Sections(env, units)
    section_dict = sections.get_sections()
    for section_key in section_dict:
        store.add(section_key, section_dict[section_key])
    return store