# Copyright 2016 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parent class for writing units."""
from . import AccessKeyStore
import inspect
import json
import os
import subprocess

class Units(object):

    @staticmethod
    def prop(obj, path):
        # Helper method to extract nested property values
        nested_keys = path.split("/")
        val = obj
        for key in nested_keys:
            val = val.get(key, {})
        return val


    def __init__(self, debug=False, substitutions=None):
        self.debug = debug

        if substitutions is None:
            self.substitutions = {}
        else:
            self.substitutions = substitutions

    def log(self, text):
        if self.debug:
            func_name = ""
            trace = inspect.stack()
            if len(trace) > 1 and len(trace[1]) > 2:
                func_name = trace[1][3] + ":"
            print "batesian:units:%s %s" % (func_name, text)

    def get_units(self, debug=False):
        unit_list = inspect.getmembers(self, predicate=inspect.ismethod)
        unit_dict = {}
        for (func_name, func) in unit_list:
            if not func_name.startswith("load_"):
                continue
            unit_key = func_name[len("load_"):]
            if len(inspect.getargs(func.func_code).args) > 1:
                unit_dict[unit_key] = func(self.substitutions)
            else:
                unit_dict[unit_key] = func()
            self.log("Generated unit '%s' : %s" % (
                unit_key, json.dumps(unit_dict[unit_key])[:50].replace(
                    "\n",""
                )
            ))
        return unit_dict
