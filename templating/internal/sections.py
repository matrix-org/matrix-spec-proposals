"""Contains all the sections for the spec."""
from . import AccessKeyStore
import os

def _render_section_room_events(env, units):
    template = env.get_template("events.tmpl")
    return template.render(example=example, event=event)

SECTION_DICT = {
    "room-events": _render_section_room_events
}

def load(env, units):
    store = AccessKeyStore()
    for unit_key in SECTION_DICT:
        unit = SECTION_DICT[unit_key](env, units)
        store.add(unit_key, unit)
    return store