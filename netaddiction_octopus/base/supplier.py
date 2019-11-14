from datetime import date, timedelta

from .downloaders import Downloader
from .parsers import Parser


class RequiredValue():

    def __init__(self, child_of=None):
        self.child_of = child_of

    def __call__(self, value):
        return self.child_of is None or isinstance(value, self.child_of)


class DefaultValue():

    def __init__(self, default):
        self.default = default


class Supplier():

    files = []
    categories = ()

    def __init__(self, partner=None):
        self.partner = partner

    def retrieve(self, files):
        data = []
        parameters = {
            'today': date.today().strftime('%Y%m%d'),
            'yesterday': (date.today() - timedelta(days=1)).strftime('%Y%m%d'),
        }
        join = files.get('join', None)
        for location, mapping in files['mapping']:
            source = self.downloader.download(location % parameters)
            parsed = self.parser.parse(source, mapping, join)
            for k, v in parsed.items():
                parsed[k]['_file'] = files['name']
            data.append(parsed)
        return data

    def merge(self, files):
        merged = {}
        value_keys = set([])

        for f in files:
            if len(f):
                value_keys.update(f[list(f.keys())[0]].keys())

        for i, f in enumerate(files):
            for key, value in f.items():
                for value_key in value_keys:
                    if value_key not in value:
                        value[value_key] = None

                if key not in merged:
                    if i > 0:
                        continue

                    merged[key] = {}

                for k, v in value.items():
                    if merged[key].get(k) is None:
                        merged[key][k] = v

        return merged.values()

    def pull(self):
        data = []
        for files in self.files:
            file_data = self.retrieve(files)
            file_data = self.merge(file_data)
            data += file_data
        return data

    def validate(self, item):
        assert True

    def group(self, item):
        return None
