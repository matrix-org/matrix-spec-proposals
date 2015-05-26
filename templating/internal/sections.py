"""Contains all the sections for the spec."""
from . import AccessKeyStore
import inspect
import os


class Sections(object):
    """A class which creates sections for each method starting with "render_".
    The key for the section is the text after "render_"
    e.g. "render_room_events" has the section key "room_events"
    """

    def __init__(self, env, units):
        self.env = env
        self.units = units

    def render_room_events(self):
        template = self.env.get_template("events.tmpl")
        examples = self.units.get("event-examples")
        schemas = self.units.get("event-schemas")
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
        return self.units.get("git-version")

    def _render_ce_type(self, type):
        template = self.env.get_template("common-event-fields.tmpl")
        ce_types = self.units.get("common-event-fields")
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
    render_list = inspect.getmembers(sections, predicate=inspect.ismethod)
    for (func_name, func) in render_list:
        if not func_name.startswith("render_"):
            continue
        section_key = func_name[len("render_"):]
        section = func()
        print "Generated section '%s' : %s" % (
            section_key, section[:60].replace("\n","")
        )
        store.add(section_key, section)
    return store