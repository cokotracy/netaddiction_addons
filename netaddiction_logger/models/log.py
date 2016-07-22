# -*- coding: utf-8 -*-
from datetime import datetime

from openerp import api, fields, models, tools


class LogLine(models.Model):
    _name = 'netaddiction.log.line'
    _description = 'Log per il cambiamento di un valore'

    author_id = fields.Many2one(comodel_name='res.users',string='Autore modifica', required=True)

    field = fields.Char('Field Modificato', required=True, readonly=1)
    field_type = fields.Char('Tipo Field', required=True, readonly=1)

    model_name = fields.Char('Modello del field', required=True, readonly=1)
    object_name = fields.Char('Nome dell oggetto a cui appartiene il field', required=True, readonly=1)
    object_id = fields.Integer('ID dell oggetto a cui appartiene il field', readonly=1)

    old_value_integer = fields.Integer('Vecchio valore Integer', readonly=1)
    old_value_float = fields.Float('Vecchio valore Float', readonly=1)
    old_value_monetary = fields.Float('Vecchio valore Monetary', readonly=1)
    old_value_char = fields.Char('Vecchio valore Char', readonly=1)
    old_value_text = fields.Text('Vecchio valore Text', readonly=1)
    old_value_datetime = fields.Datetime('Vecchio valore DateTime', readonly=1)

    new_value_integer = fields.Integer('Nuovo valore Integer', readonly=1)
    new_value_float = fields.Float('Nuovo valore Float', readonly=1)
    new_value_monetary = fields.Float('Nuovo valore Monetary', readonly=1)
    new_value_char = fields.Char('Nuovo valore Char', readonly=1)
    new_value_text = fields.Text('Nuovo valore Text', readonly=1)
    new_value_datetime = fields.Datetime('Nuovo valore Datetime', readonly=1)



    @api.model
    def create_tracking_values(self, initial_value, new_value, col_name, col_type, model_name, object_id, author_id, object_name='', col_selection={}):
        """
        ritorna un dizionario da usare per creare  una netadddiction.log.line
        Parametri:
        - initial_value: vecchio valore del campo
        - new_value: Nuovo valore del campo
        - col_name: nome del campo
        - col_type: tipo del campo (stringa)
        - col_selection: se il campo in questione è una selection inserire qui tutti i possibili valori della selection

        """
        tracked = True
        values = {'field': col_name,  'field_type': col_type,'model_name': model_name,'object_id':object_id,'object_name':object_name, 'author_id':author_id}

        if col_type in ['integer', 'float', 'char', 'text', 'datetime', 'monetary']:
            values.update({
                'old_value_%s' % col_type: initial_value,
                'new_value_%s' % col_type: new_value
            })
        elif col_type == 'date':
            values.update({
                'old_value_datetime': initial_value and datetime.strftime(datetime.combine(datetime.strptime(initial_value, tools.DEFAULT_SERVER_DATE_FORMAT), datetime.min.time()), tools.DEFAULT_SERVER_DATETIME_FORMAT) or False,
                'new_value_datetime': new_value and datetime.strftime(datetime.combine(datetime.strptime(new_value, tools.DEFAULT_SERVER_DATE_FORMAT), datetime.min.time()), tools.DEFAULT_SERVER_DATETIME_FORMAT) or False,
            })
        elif col_type == 'boolean':
            values.update({
                'old_value_integer': initial_value,
                'new_value_integer': new_value
            })
        elif col_type == 'selection':
            values.update({
                'old_value_char': initial_value and dict(col_selection)[initial_value] or '',
                'new_value_char': new_value and dict(col_selection)[new_value] or ''
            })
        elif col_type == 'many2one':
            values.update({
                'old_value_integer': initial_value and initial_value.id or 0,
                'new_value_integer': new_value and new_value.id or 0,
                'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
                'new_value_char': new_value and new_value.name_get()[0][1] or ''
            })
        else:
            tracked = False

        if tracked:
            return values
        return {}


    @api.one
    def unlink(self):
        return