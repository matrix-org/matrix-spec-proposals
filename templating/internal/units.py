"""Contains all the units for the spec."""
from . import AccessKeyStore
import os

def _load_examples():
    path = "../event-schemas/examples"
    examples = {}
    for filename in os.listdir(path):
        with open(filename, "r") as f:
            print filename
    return examples


UNIT_DICT = {
    "event-examples": _load_examples
}


def load():
    store = AccessKeyStore()
    for unit_key in UNIT_DICT:
        unit = UNIT_DICT[unit_key]()
        store.add(unit_key, unit)
    return store
