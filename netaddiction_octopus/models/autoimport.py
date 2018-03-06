# -*- coding: utf-8 -*-

from openerp import api, models, fields

class AutoImportProduct(models.Model):
    _name = 'netaddiction_octopus.autoimport.product'

    supplier_id = fields.Many2one('netaddiction_octopus.supplier', string='Fornitore', required=True)
    category_ids = fields.Many2many('product.category', string='Categorie da Importare')

class Cron(models.Model):
    _name = 'netaddiction_octopus.cron.autoimport'

    @api.model
    def run_import(self):
        autoimport = self.env['netaddiction_octopus.autoimport.product'].search([])

        # per ogni fornitore configurato mi prendo i prodotti octopus con quelle categorie di quel fornitore
        for auto in autoimport:
            results = self.env['netaddiction_octopus.product'].search([('supplier_id.id', '=', auto.supplier_id.partner_id.id), ('category_id.id', 'in', auto.category_ids.ids), ('is_new', '=', True)])
            for res in results:
                if not res.image:
                    res.search_image_qwant()

                new_product = False
                # se la categoria è abbigliamento
                if res.category_id.id == 11:
                    if res.image:
                        for attribute in res.attribute_ids:
                            # se ha la taglia lo importo
                            if attribute.attribute_id.id == 20:
                                new_product = res.import_product()
                                created = self.env['product.product'].browse(new_product['res_id'])
                                created.active = True
                else:
                    if res.image:
                        new_product = res.import_product()
                        created = self.env['product.product'].browse(new_product['res_id'])
                        created.active = True

                if new_product:
                    attr = {
                        'res_id': new_product['res_id'],
                        'model': 'product.product',
                        'message_type': 'notification',
                        'subtype_id': 2,
                        'body': 'Prodotto importato automaticamente da octopus',
                    }
                    self.env['mail.message'].create(attr)
