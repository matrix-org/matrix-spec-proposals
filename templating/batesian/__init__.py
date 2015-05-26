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