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
            print "batesian:sections: %s" % text

    def get_sections(self):
        render_list = inspect.getmembers(self, predicate=inspect.ismethod)
        section_dict = {}
        for (func_name, func) in render_list:
            if not func_name.startswith("render_"):
                continue
            section_key = func_name[len("render_"):]
            self.log("Generating section '%s'" % section_key)
            section = func()
            if isinstance(section, basestring):
                if section_key in section_dict:
                    raise Exception(
                        ("%s : Section %s already exists. It must have been " +
                        "generated dynamically. Check which render_ methods " +
                        "return a dict.") %
                        (func_name, section_key)
                    )
                section_dict[section_key] = section
                self.log(
                    "  Generated. Snippet => %s" % section[:60].replace("\n","")
                )
            elif isinstance(section, dict):
                self.log("  Generated multiple sections:")
                for (k, v) in section.iteritems():
                    if not isinstance(k, basestring) or not isinstance(v, basestring):
                        raise Exception(
                            ("Method %s returned multiple sections as a dict but " +
                            "expected the dict elements to be strings but they aren't.") %
                            (func_name, )
                        )
                    if k in section_dict:
                        raise Exception(
                            "%s tried to produce section %s which already exists." %
                            (func_name, k)
                        )
                    section_dict[k] = v
                    self.log(
                        "  %s  =>  %s" % (k, v[:60].replace("\n",""))
                    )
            else:
                raise Exception(
                    "Section function '%s' didn't return a string/dict!" % func_name
                )
        return section_dict