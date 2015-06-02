"""Parent class for writing sections."""
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
            self.log("Generating section '%s'" % section_key)
            section = func()
            if not isinstance(section, basestring):
                raise Exception(
                    "Section function '%s' didn't return a string!" % func_name
                )
            section_dict[section_key] = section
            self.log(
                "  Generated. Snippet => %s" % section[:60].replace("\n","")
            )
        return section_dict