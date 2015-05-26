"""Contains all the sections for the spec."""
from . import AccessKeyStore
import os

def _render_section_room_events(env, units):
    template = env.get_template("events.tmpl")
    examples = units.get("event-examples")
    schemas = units.get("event-schemas")
    sections = []
    for event_name in sorted(schemas):
        if not event_name.startswith("m.room"):
            continue
        sections.append(template.render(
            example=examples[event_name], 
            event=schemas[event_name]
        ))
    return "\n\n".join(sections)

def _render_ce_type(env, units, type):
    template = env.get_template("common-event-fields.tmpl")
    ce_types = units.get("common-event-fields")
    return template.render(common_event=ce_types[type])

def _render_ce_fields(env, units):
    return _render_ce_type(env, units, "event")

def _render_cre_fields(env, units):
    return _render_ce_type(env, units, "room_event")

def _render_cse_fields(env, units):
    return _render_ce_type(env, units, "state_event")

SECTION_DICT = {
    "room_events": _render_section_room_events,
    "common_event_fields": _render_ce_fields,
    "common_state_event_fields": _render_cse_fields,
    "common_room_event_fields": _render_cre_fields
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