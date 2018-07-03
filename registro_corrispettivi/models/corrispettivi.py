# -*- coding: utf-8 -*-

from openerp import models, fields, api
import xlwt
import datetime
from calendar import monthrange
import collections
import string
from cStringIO import StringIO
import base64

class RegistroCorrispettivi(models.Model):
    _name = "registro.corrispettivi"

    date_start = fields.Datetime(string="Data inizio")
    date_end = fields.Datetime(string="Data Fine")
    name = fields.Char(string="Nome", compute="_get_my_name")

    file = fields.Binary(string="File")
    filename = fields.Char(string="Nome File", compute="_get_filename")

    @api.one
    def _get_my_name(self):
        month_date = datetime.datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S')
        self.name = 'Corrispettivi %s' % month_date.strftime("%B %Y")

    @api.one
    def _get_filename(self):
        month_date = datetime.datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S')
        self.filename = 'Corrispettivi_%s.xls' % month_date.strftime("%B_%Y")

    @api.one
    def get_corrispettivi(self):
        month_date = datetime.datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S')
        numberdays = monthrange(month_date.year, month_date.month)[1]
        numberdays = list(range(1, numberdays + 1))

        delivery_picking_type_ids = self.env['ir.values'].search([("name", "=", "delivery_picking_type_ids"), ("model", "=", "registro.corrispettivi.config")])
        delivery_picking_type_ids = delivery_picking_type_ids.value
        delivery_picking_type_ids = delivery_picking_type_ids.replace('[', '').replace(']', '')
        delivery_picking_type_ids = [int(x) for x in delivery_picking_type_ids.split(',')]

        refund_picking_type_ids = self.env['ir.values'].search([("name", "=", "refund_picking_type_ids"), ("model", "=", "registro.corrispettivi.config")])
        refund_picking_type_ids = refund_picking_type_ids.value
        refund_picking_type_ids = refund_picking_type_ids.replace('[', '').replace(']', '')
        refund_picking_type_ids = [int(x) for x in refund_picking_type_ids.split(',')]

        domain = [('state', '=', 'done'), ('date_done', '>=', self.date_start), ('date_done', '<=', self.date_end)]

        wb = xlwt.Workbook()
        # creo i fogli: uno per le spedizioni in uscita, uno per i resi
        delivery_sheet = wb.add_sheet('Vendite %s' % (month_date.strftime("%m - %Y")))
        refund_sheet = wb.add_sheet('Resi %s' % (month_date.strftime("%m - %Y")))

        # cerchiamo le spedizioni in uscita
        delivery_domain = domain + [('picking_type_id.id', 'in', delivery_picking_type_ids)]
        pickings = self.env['stock.picking'].search(delivery_domain)

        delivery_picks, tax_names = self.create_subdivision(pickings, numberdays, month_date)
        # in delivery_picks ho i dati che mi servono, fatturato e tasse divisi per giorno
        self.create_sheet(tax_names, delivery_sheet, delivery_picks, numberdays)

        # resi
        refund_domain = domain + [('picking_type_id.id', 'in', refund_picking_type_ids)]
        pickings = self.env['stock.picking'].search(refund_domain)
        refund_cost = self.env['ir.values'].search([("name", "=", "refund_delivery_cost"), ("model", "=", "registro.corrispettivi.config")])
        if refund_cost:
            refund_cost = refund_cost.value
        else:
            refund_cost = False
        refund_picks, tax_names = self.create_subdivision(pickings, numberdays, month_date, check_sale_id=False, check_sale_origin=True, refund_delivery_cost=refund_cost)
        # in refund_picks ho i dati che mi servono, fatturato e tasse divisi per giorno
        self.create_sheet(tax_names, refund_sheet, refund_picks, numberdays)

        fp = StringIO()
        wb.save(fp)
        fp.seek(0)
        self.file = base64.b64encode(fp.read()).decode()

    @api.model
    def create_subdivision(self, pickings, numberdays, month_date, check_sale_id=True, check_sale_origin=False, refund_delivery_cost=True):
        # check_sale_id: controlla se pick.sale_id è settato può servire per capire se è una spedizione associata ad un ordine di vendita
        # check_sale_origin: in alcuni casi (tipo su multiplayer.com) i nuovi tipi di spedizione non associano il campo sale_id, quindi serve di fare un'ulteriore
        #                    query per cercare l'ordine di vendita. se non esiste non è una spedizione valida.
        # delivery_cost: se False non conta i costi di spedizione nei resi.

        # qua vanno le tasse
        tax_names = []

        multidelivery = self.env['ir.values'].search([("name", "=", "multidelivery"), ("model", "=", "registro.corrispettivi.config")])
        if multidelivery:
            multidelivery = multidelivery.value
        else:
            multidelivery = False

        delivery_picks = {}
        for i in numberdays:
            delivery_picks[datetime.datetime.strptime('%s-%s-%s' % (month_date.year, month_date.month, str(i).zfill(2)), '%Y-%m-%d')] = {}

        delivery_picks = collections.OrderedDict(sorted(delivery_picks.items()))
        for pick in pickings:
            date_done = datetime.datetime.strptime(pick.date_done, '%Y-%m-%d %H:%M:%S')
            date_done = date_done.replace(minute=0, hour=0, second=0, microsecond=0)

            if check_sale_id:
                if pick.sale_id:
                    # se ha un ordine di vendita associato supponiamo sia una movimentazione per vendite
                    # raggruppo per giorno e tassa
                    for line in pick.move_lines:
                        tax = delivery_picks[date_done].get(line.product_id.taxes_id.name, False)
                        if not tax:
                            delivery_picks[date_done][line.product_id.taxes_id.name] = {}
                            delivery_picks[date_done][line.product_id.taxes_id.name]['value'] = line.procurement_id.sale_line_id.price_total
                            delivery_picks[date_done][line.product_id.taxes_id.name]['tax_value'] = line.procurement_id.sale_line_id.price_tax
                        else:
                            delivery_picks[date_done][line.product_id.taxes_id.name]['value'] += line.procurement_id.sale_line_id.price_total
                            delivery_picks[date_done][line.product_id.taxes_id.name]['tax_value'] += line.procurement_id.sale_line_id.price_tax

                        if line.product_id.taxes_id.name not in tax_names:
                            tax_names.append(line.product_id.taxes_id.name)
            else:
                # raggruppo per giorno e tassa
                for line in pick.move_lines:
                    tax = delivery_picks[date_done].get(line.product_id.taxes_id.name, False)
                    if check_sale_origin:
                        try:
                            origin = self.env['sale.order'].search([('name', '=', pick.origin)]).id
                        except:
                            origin = False
                        if origin:
                            move = self.env['stock.move'].search([('procurement_id.sale_line_id.order_id.id', '=', origin), ('product_id', '=', line.product_id.id)])
                            line = move
                    if not tax:
                        delivery_picks[date_done][line.product_id.taxes_id.name] = {}
                        delivery_picks[date_done][line.product_id.taxes_id.name]['value'] = line.procurement_id.sale_line_id.price_total
                        delivery_picks[date_done][line.product_id.taxes_id.name]['tax_value'] = line.procurement_id.sale_line_id.price_tax
                    else:
                        delivery_picks[date_done][line.product_id.taxes_id.name]['value'] += line.procurement_id.sale_line_id.price_total
                        delivery_picks[date_done][line.product_id.taxes_id.name]['tax_value'] += line.procurement_id.sale_line_id.price_tax
                    if line.product_id.taxes_id.name not in tax_names:
                        tax_names.append(line.product_id.taxes_id.name)
            if refund_delivery_cost:
                if multidelivery:
                    if pick.carrier_price > 0:
                        delivery_picks[date_done][pick.carrier_id.product_id.taxes_id.name]['value'] += pick.carrier_price
                        delivery_picks[date_done][pick.carrier_id.product_id.taxes_id.name]['tax_value'] += pick.carrier_id.product_id.taxes_id.compute_all(pick.carrier_price)['taxes'][0]['amount']
                else:
                    pass
                    # TODO : se metti multidelivery a false che faccio?

        return delivery_picks, tax_names

    @api.model
    def create_sheet(self, tax_names, delivery_sheet, delivery_picks, numberdays):
        # stili di excel
        headStyle = xlwt.easyxf('font: name Arial, color-index black, bold on')
        totalStyle = xlwt.easyxf('font: name Arial, color-index green, bold on')
        numStyle = xlwt.easyxf('font: name Arial, color-index black', num_format_str='#,##0.00')
        dateStyle = xlwt.easyxf('font: name Arial, color-index red, bold on', num_format_str='DD-MM-YYYY')

        position_tax = {}

        # n è la posizione orizzontale nel foglio, lascio degli spazi per renderlo leggibile
        n = 1
        for tax_name in tax_names:
            delivery_sheet.write(0, n, 'Fatturato %s' % tax_name, headStyle)
            position_tax[tax_name] = [n]
            n += 1
            delivery_sheet.write(0, n, 'Tasse %s' % tax_name, headStyle)
            position_tax[tax_name].append(n)
            n += 2

        total_horizontal = []
        delivery_sheet.write(0, n, 'Totale Fatturato', totalStyle)
        total_horizontal.append(n)
        n += 1
        delivery_sheet.write(0, n, 'Totale Tasse', totalStyle)
        total_horizontal.append(n)

        # scrivo i dati
        n = 1
        for line in delivery_picks:
            delivery_sheet.write(n, 0, line, dateStyle)
            for tax_name in tax_names:
                res = delivery_picks[line].get(tax_name, False)
                index = position_tax.get(tax_name, False)

                if res:
                    delivery_sheet.write(n, index[0], res['value'], numStyle)
                    delivery_sheet.write(n, index[1], res['tax_value'], numStyle)
                else:
                    delivery_sheet.write(n, index[0], 0, numStyle)
                    delivery_sheet.write(n, index[1], 0, numStyle)
            n += 1

        # metto i totali, prima quelli su colonna poi quelli su riga
        total_index = len(delivery_picks) + 2

        delivery_sheet.write(total_index, 0, 'Totale', totalStyle)

        letters = []
        for x, y in zip(range(0, 26), string.ascii_lowercase):
            letters.append(y)

        horizontal = {0: [], 1: []}
        for tax_name in tax_names:
            index = position_tax.get(tax_name, False)
            delivery_sheet.write(total_index, index[0], xlwt.Formula("SUM(%s1:%s%s)" % (letters[index[0]].upper(), letters[index[0]].upper(), total_index - 1)), totalStyle)
            delivery_sheet.write(total_index, index[1], xlwt.Formula("SUM(%s1:%s%s)" % (letters[index[1]].upper(), letters[index[1]].upper(), total_index - 1)), totalStyle)
            horizontal[0].append(letters[index[0]].upper())
            horizontal[1].append(letters[index[1]].upper())

        for i in numberdays:
            delivery_sheet.write(i, total_horizontal[0], xlwt.Formula("SUM(%s%s;%s%s)" % (horizontal[0][0], i + 1, horizontal[0][1], i + 1)))
            delivery_sheet.write(i, total_horizontal[1], xlwt.Formula("SUM(%s%s;%s%s)" % (horizontal[1][0], i + 1, horizontal[1][1], i + 1)))

# Callse per la configurazione dei corrispettivi
class PubProductConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'registro.corrispettivi.config'

    delivery_picking_type_ids = fields.Many2many(string="Spedizioni ai clienti/Vendite", comodel_name="stock.picking.type")
    refund_picking_type_ids = fields.Many2many(string="Resi", comodel_name="stock.picking.type", relation="corrispettivi_config_refund_type")
    multidelivery = fields.Boolean(string="Calcola su carrier_price (usato per le multispedizioni)")
    refund_delivery_cost = fields.Boolean(string="Contare le spese di spedizione nei Resi")

    @api.model
    def get_default_refund_delivery_cost(self, fields):
        value = self.env['ir.values'].search([("name", "=", "refund_delivery_cost"), ("model", "=", "registro.corrispettivi.config")])
        if not value:
            return {'refund_delivery_cost': False}

        return {'refund_delivery_cost': value.value}

    @api.model
    def set_default_refund_delivery_cost(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "refund_delivery_cost"), ("model", "=", "registro.corrispettivi.config")])
        if values:
            values.value = res.refund_delivery_cost
            return True

        return self.env['ir.values'].create({'name': 'refund_delivery_cost', 'value': res.refund_delivery_cost, 'model': 'registro.corrispettivi.config'})

    @api.model
    def get_default_multidelivery(self, fields):
        value = self.env['ir.values'].search([("name", "=", "multidelivery"), ("model", "=", "registro.corrispettivi.config")])
        if not value:
            return {'multidelivery': False}

        return {'multidelivery': value.value}

    @api.model
    def set_default_multidelivery(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "multidelivery"), ("model", "=", "registro.corrispettivi.config")])
        if values:
            values.value = res.multidelivery
            return True

        return self.env['ir.values'].create({'name': 'multidelivery', 'value': res.multidelivery, 'model': 'registro.corrispettivi.config'})

    @api.model
    def get_default_delivery_picking_type_ids(self, fields):
        value = self.env['ir.values'].search([("name", "=", "delivery_picking_type_ids"), ("model", "=", "registro.corrispettivi.config")])

        if not value:
            return {'delivery_picking_type_ids': False}
        s = value.value
        s = s.replace('[', '').replace(']', '')
        l = s.split(',')
        ids = [int(x) for x in l]
        return {'delivery_picking_type_ids': [(6, False, ids)]}

    @api.one
    def set_delivery_picking_type_ids(self, values):
        values = self.env['ir.values'].search([("name", "=", "delivery_picking_type_ids"), ("model", "=", "registro.corrispettivi.config")])

        if values:
            values.value = self.delivery_picking_type_ids.ids
            return True

        return self.env['ir.values'].create({'name': 'delivery_picking_type_ids', 'value': self.delivery_picking_type_ids.ids, 'model': 'registro.corrispettivi.config'})

    @api.model
    def get_default_refund_picking_type_ids(self, fields):
        value = self.env['ir.values'].search([("name", "=", "refund_picking_type_ids"), ("model", "=", "registro.corrispettivi.config")])

        if not value:
            return {'refund_picking_type_ids': False}
        s = value.value
        s = s.replace('[', '').replace(']', '')
        l = s.split(',')
        ids = [int(x) for x in l]
        return {'refund_picking_type_ids': [(6, False, ids)]}

    @api.one
    def set_refund_picking_type_ids(self, values):
        values = self.env['ir.values'].search([("name", "=", "refund_picking_type_ids"), ("model", "=", "registro.corrispettivi.config")])

        if values:
            values.value = self.refund_picking_type_ids.ids
            return True

        return self.env['ir.values'].create({'name': 'refund_picking_type_ids', 'value': self.refund_picking_type_ids.ids, 'model': 'registro.corrispettivi.config'})
