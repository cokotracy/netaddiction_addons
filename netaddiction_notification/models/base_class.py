# -*- coding: utf-8 -*-
from difflib import SequenceMatcher

class Notification():

    def message_related_field(self,old,new):
        """
        metodo da fare override per ogni modello
        scrive il messaggio da loggare per i campi many2many,many2one,one2many specifici.
        """
        return ''


    def _notify_active(self,odoo):
        """
        prendo il valore setting di active
        con i modelli transient i valori sono temporanei,
        se si usa il nome default_xxx il valore xxx viene salvato nella tabella ir_values
        """
        result=odoo.env['ir.values'].search([('name','=','active'),
            ('model','=','netaddiction.notification.settings'),('key','=','default')])
        if 'I00' in result.value:
            return False
        else:
            return True

    def _model_active(self,odoo):
        """
        varifica che sia abilitato il log per questo modello
        """
        name = odoo._name.replace('.','_')
        result=odoo.env['ir.values'].search([('name','=',name),
            ('model','=','netaddiction.notification.settings'),('key','=','default')])
        if 'I00' in result.value:
            return False
        else:
            return True


    def _save_msg(self,odoo,values):
        """
        salva il log della modifica
        """
        #nome del modello in uso
        model_name = odoo._name

        if self._notify_active(odoo) and self._model_active(odoo):
            #ciclo perchè le write dei modelli generalmente sono @api.multi
            for obj in odoo:
                msg = ''
                for key,value in values.items():
                    field_name = self._get_field_name(odoo,key,model_name)
                    change = self._get_data_field(odoo,obj,key,value)

                    msg = msg + "<p><b>"+field_name+"</b>: "+change+"</p>"

                attr = {
                    'subtype_id' : 2,
                    'res_id' : obj.id,
                    'body' : msg,
                    'model' : 'product.product',
                    'author_id' : odoo.env.user.partner_id.id,
                    'message_type' : 'comment',
                }
                odoo.env['mail.message'].create(attr)

    def _get_field_name(self,odoo,field_name,model_name):
        """
        Dato il nome del modello e il nome del field ritorna la descrizione di quest'ultimo
        """
        search=[
            ('model','=',model_name),
            ('name','=',field_name),
        ]
        result=odoo.env['ir.model.fields'].search(search)
        return result.field_description

    def _get_data_field(self,odoo,obj,field_name,new_value):
        """
        in base al tipo del field stabilisce come scrivere il report
        """
        search = [
            ('model','=',odoo._name),
            ('name','=',field_name)
        ]
        result=odoo.env['ir.model.fields'].search(search)

        msg = ''

        if result.ttype in ('text','html'):
            old = self._html2list(obj[field_name])
            new = self._html2list(new_value)
            msg = self._ge_diff_html(old,new)
        elif result.ttype in ('boolean','char','integer','float','selection'):
            msg = str(obj[field_name]) + " <b>=></b> " + str(new_value)
        elif result.ttype in ('date','datetime'):
            msg = str(obj[field_name]) + " <b>=></b> " + str(new_value)
        elif result.ttype in ('many2one','many2many','one2many'):
            msg = self.message_related_field(obj[field_name],new_value)

        return msg

    def _wrap(self, text, mode=None):
        text = ''.join(text)
        if mode is not None:
            start = '<span><b>%s</b> ' % mode
            end = '</span>'
            text = text.replace('<p>', end + '<p>' + start)
            text = text.replace('</p>', end + '</p>' + start)
            text = start + text + end
            text = text.replace(start + end, '')
        return text

    def _ge_diff_html(self, old, new):
        diff = SequenceMatcher(None, old, new)
        output = []

        for opcode, a0, a1, b0, b1 in diff.get_opcodes():

            if opcode == 'equal':
                pass
                #line = self._wrap(diff.a[a0:a1])
            elif opcode == 'insert':
                line = self._wrap(diff.b[b0:b1], '+')
                output.append(line)
            elif opcode == 'delete':
                line = self._wrap(diff.a[a0:a1], '-')
                output.append(line)
            elif opcode == 'replace':
                line = ' '.join([self._wrap(diff.a[a0:a1], '-'),
                    self._wrap(diff.b[b0:b1], '+')])
                output.append(line)

        return ''.join(output)

    def _html2list(self, x, b=0):
        import string
        mode = 'char'
        cur = ''
        out = []
        for c in x:
            if mode == 'tag':
                if c == '>':
                    if b: cur += ']'
                    else: cur += c
                    out.append(cur); cur = ''; mode = 'char'
                else: cur += c
            elif mode == 'char':
                if c == '<':
                    out.append(cur)
                    if b: cur = '['
                    else: cur = c
                    mode = 'tag'
                elif c in string.whitespace: out.append(cur+c); cur = ''
                else: cur += c
        out.append(cur)
        return filter(lambda x: x is not '', out)
