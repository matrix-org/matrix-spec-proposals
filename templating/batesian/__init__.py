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
from sets import Set


class AccessKeyStore(object):
    """Storage for arbitrary data. Monitors get calls so we know if they
    were used or not."""

    def __init__(self, existing_data=None):
        if not existing_data:
            existing_data = {}
        self.data = existing_data
        self.accessed_set = Set()

    def keys(self):
        return self.data.keys()

    def add(self, key, unit_dict):
        self.data[key] = unit_dict

    def get(self, key):
        self.accessed_set.add(key)
        return self.data[key]

    def get_unaccessed_set(self):
        data_list = Set(self.data.keys())
        return data_list - self.accessed_set