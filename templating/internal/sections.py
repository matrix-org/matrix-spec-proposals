"""Contains all the sections for the spec."""
from . import AccessKeyStore
import os

def _render_section_room_events(env, units):
    template = env.get_template("events.tmpl")
    examples = units.get("event-examples")
    schemas = units.get("event-schemas")
    sections = []
    for event_name in schemas:
        if not event_name.startswith("m.room"):
            continue
        sections.append(template.render(
            example=examples[event_name], 
            event=schemas[event_name]
        ))
    return "\n\n".join(sections)

SECTION_DICT = {
    "room_events": _render_section_room_events
}

def load(env, units):
    store = AccessKeyStore()
    for section_key in SECTION_DICT:
        section = SECTION_DICT[section_key](env, units)
        print "Generated section '%s' : %s" % (
            section_key, section[:60].replace("\n","")
        )
        store.add(section_key, section)
    return store