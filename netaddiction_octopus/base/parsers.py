import csv
import logging
import re

from io import StringIO


_logger = logging.getLogger(__name__)


class Parser():

    def parse(self):
        raise NotImplementedError()


class CSVParser(Parser):

    EMPTY = '__empty__'

    class UndefinedField(object):
        KEY = '__undefined_field__'

    def __init__(self, skip_first=False, delimiter=',', enclosure='"',
                 escape='\\', linebreak='\r\n'):
        self.skip_first = skip_first
        self.delimiter = delimiter
        self.enclosure = enclosure
        self.escape = escape
        self.linebreak = linebreak

    def parse(self, source, mapping, group_by=None):
        source = StringIO(source)
        output = {}
        reader = csv.DictReader(
            source,
            mapping,
            delimiter=self.delimiter,
            quotechar=self.enclosure,
            escapechar=self.escape,
            lineterminator=self.linebreak,
            restkey=self.UndefinedField.KEY,
            restval=self.UndefinedField
        )
        if self.skip_first:
            next(reader)
        corrupted_items = 0
        for i, item in enumerate(reader):
            if self.EMPTY in item:
                del item[self.EMPTY]
            if self.UndefinedField.KEY in item \
                    or self.UndefinedField in item.values():
                corrupted_items += 1
                _logger.debug('Elemento corrotto: %s' % item)
                continue
            key = i if group_by is None else item[group_by]
            output[key] = item
        if corrupted_items:
            _logger.warning('%s elementi corrotti' % corrupted_items)
        return output


class RegexParser(Parser):

    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def parse(self, source, mapping, group_by=None):
        output = {}
        lines = self.pattern.findall(source)
        for i, line in enumerate(lines):
            item = dict(zip(mapping, line))
            key = i if group_by is None else item[group_by]
            output[key] = item
        return output
