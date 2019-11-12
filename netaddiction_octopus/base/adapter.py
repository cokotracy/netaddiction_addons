# -*- coding: utf-8 -*-

import logging
import re


_logger = logging.getLogger(__name__)


class Adapter():

    FIELD_PATTERN = r'\[([a-z]+)\] (.*)'

    def __init__(self, **fields):
        self.fields = fields
        self.field_pattern = re.compile(self.FIELD_PATTERN)

    def map(self, model, handler, item, categories, taxes):
        mapping = {
            'supplier_id': handler.partner.id,
            'company_id': handler.partner.company_id.id,
            'attribute_ids': [],
            'category_id': None,
            'sale_tax_id': None,
            'purchase_tax_id': None,
            'group_key': None,
            'group_name': None,
        }

        # Categories

        if handler.categories:
            chains = []

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
                _logger.debug('Prodotto non categorizzato: %s' % item)
                return None

        # Taxes

        if handler.categories:
            chains = []

            for field in handler.categories:
                value = item[field]

                if not value:
                    continue

                field_key = ('[field] %s: %s' % (item['_file'], field), value)
                if field_key in taxes:
                    chains.append(taxes[field_key])

            file_key = ('[file] %s' % item['_file'], None)

            if file_key in taxes:
                chains.append(taxes[file_key])

            if chains:
                mapping['sale_tax_id'] = chains[0]['sale_tax_id'].id
                mapping['purchase_tax_id'] = chains[0]['purchase_tax_id'].id

                if len(chains) > 1:
                    _logger.warning('Prodotto con più di una coppia di tasse: %s (%s)' % (item, chains))

            if not mapping['sale_tax_id'] or not mapping['purchase_tax_id']:
                _logger.warning('Prodotto senza tasse: %s' % item)
                return None

        # Group

        if handler.categories:
            group = handler.group(item)

            if group is not None:
                mapping['group_key'], mapping['group_name'] = group

        # Mapped fields

        valid_fields = model._fields.keys()

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
