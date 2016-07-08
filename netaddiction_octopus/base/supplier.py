from datetime import date, timedelta

from .downloaders import Downloader
from .parsers import Parser
from .registry import registry


class RequiredValue(object):
    def __init__(self, child_of=None):
        self.child_of = child_of

    def __call__(self, value):
        return self.child_of is None or isinstance(value, self.child_of)


class DefaultValue(object):
    def __init__(self, default):
        self.default = default


class SupplierBase(type):
    attrs = {
        'files': list,
        'categories': DefaultValue(()),
        'downloader': RequiredValue(Downloader),
        'parser': RequiredValue(Parser),
        'mapping': dict,
        'validate': callable,
        'group': callable,
    }

    def __new__(cls, name, bases, attrs):
        super_new = super(SupplierBase, cls).__new__

        parents = [b for b in bases if isinstance(b, SupplierBase)]

        if not parents:
            return super_new(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})

        for key, value in cls.attrs.items():
            if isinstance(value, RequiredValue):
                if key not in attrs:
                    raise AttributeError("Missing required attribute '%s' for '%s'" % (key, name))
                elif not value(attrs[key]):
                    raise AttributeError("Wrong type for attribute '%s' of '%s'. Expected '%s', found '%s'" % (
                        key, name, value.child_of, type(attrs[key])))
            elif isinstance(value, DefaultValue):
                if key not in attrs:
                    attrs[key] = value.default

            setattr(new_class, key, attrs.get(key, value))

        registry.register(new_class)

        return new_class


class Supplier(object):
    __metaclass__ = SupplierBase

    def __init__(self, partner):
        self.partner = partner

    def retrieve(self, files):
        data = []
        parameters = {
            'today': date.today().strftime('%Y%m%d'),
            'yesterday': (date.today() - timedelta(days=1)).strftime('%Y%m%d'),
        }

        join = files.get('join')

        for location, mapping in files['mapping'].items():
            source = self.downloader.download(location % parameters)
            parsed = self.parser.parse(source, mapping, join)

            for k, v in parsed.items():
                parsed[k]['_file'] = files['name']

            data.append(parsed)

        return data

    def merge(self, files):
        merged = {}

        for f in files:
            for key, value in f.items():
                if key not in merged:
                    merged[key] = {}

                merged[key].update(value)

        length = max([len(m) for m in merged.values()])

        return [m for m in merged.values() if len(m) == length]

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
