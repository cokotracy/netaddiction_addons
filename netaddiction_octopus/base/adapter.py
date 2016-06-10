import logging
import re


_logger = logging.getLogger(__name__)


class Adapter(object):
    FIELD_PATTERN = r'\[([a-z]+)\] (.*)'

    def __init__(self, **fields):
        self.fields = fields
        self.field_pattern = re.compile(self.FIELD_PATTERN)

    def map(self, model, handler, item, categories):
        mapping = {
            'supplier_id': handler.partner.id,
            'company_id': handler.partner.company_id.id,
            'attribute_ids': [],
            'category_id': None,
        }

        chains = []
        valid_fields = model._fields.keys()

        for field in handler.categories:
            value = item[field]

            if not value:
                continue

            field_key = ('[field] %s: %s' % (item['_file'], field), value)

            if field_key in categories:
                chains.append(categories[field_key])
            else:
                _logger.warning('Categoria non gestita: %s' % str(field_key))

        file_key = ('[file] %s' % item['_file'], None)

        if file_key in categories:
            chains.append(categories[file_key])

        for chain in chains:
            if chain['type'] == 'trash':
                return None
            elif chain['type'] == 'attribute':
                mapping['attribute_ids'].append((4, chain['attribute_id'].id, None))
            elif chain['type'] == 'category':
                if mapping['category_id'] is None:
                    mapping['category_id'] = chain['category_id'].id
                elif mapping['category_id'] != chain['category_id'].id:
                    _logger.warning('Categorie multiple per %s' % item)

        if not mapping['category_id']:
            _logger.warning('Prodotto non categorizzato: %s' % item)
            return None

        for field, match in self.fields.items():
            if field not in valid_fields:
                raise AttributeError("Unknown field '%s' in '%s'" % (field, model.__name__))

            if match in item:
                mapping[field] = item[match]
            elif hasattr(match, '__call__'):
                mapping[field] = match(handler, item)
            else:
                mapping[field] = match

        return mapping
