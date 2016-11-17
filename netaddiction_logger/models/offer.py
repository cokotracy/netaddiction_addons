# -*- coding: utf-8 -*-

from openerp import api, models


class OfferCatalogLine(models.Model):
    """ registro i cambi di offer price
    """

    _inherit = "netaddiction.specialoffer.offer_catalog_line"

    @api.multi
    def write(self, values):
        if self.env.context.get('skip_offer_catalog_lines_log_tracking', False):
            return super(OfferCatalogLine, self).write(values)

        old_offer_price = {}
        log_line = self.env["netaddiction.log.line"]

        for offer in self:

            if 'active' in values and values['active'] != offer.active:
                old_offer_price[offer.id] = offer.product_id.offer_price
            if 'percent_discount' in values and values['percent_discount'] != offer.percent_discount:
                old_offer_price[offer.id] = offer.product_id.offer_price
            if 'fixed_price' in values and values['fixed_price'] != offer.fixed_price:
                old_offer_price[offer.id] = offer.product_id.offer_price
            if 'offer_type' in values and values['offer_type'] != offer.offer_type:
                old_offer_price[offer.id] = offer.product_id.offer_price

        ret = super(OfferCatalogLine, self).write(values)

        if old_offer_price:
            for offer in self:

                if offer.id in old_offer_price and offer.active and not offer.product_id.offer_catalog_lines or (offer.product_id.offer_catalog_lines and offer.product_id.offer_catalog_lines[0].priority < offer.priority):
                    new_price = offer._get_offer_price()
                    new_price = new_price[0] if isinstance(new_price, list) else new_price
                    log_line.sudo().create(log_line.create_tracking_values(old_offer_price[offer.id], new_price, 'offer_price', 'float', 'product.product', offer.product_id.id, self.env.uid, offer.offer_catalog_id.company_id.id, object_name=offer.product_id.name))
                elif offer.id in old_offer_price and not offer.active and offer.product_id.offer_catalog_lines and offer.product_id.offer_catalog_lines[0].id == offer.id:
                    if len(offer.product_id.offer_catalog_lines) > 1:
                        new_price = offer.product_id.offer_catalog_lines[1]._get_offer_price()
                        new_price = new_price[0] if isinstance(new_price, list) else new_price
                    else:
                        new_price = 0.0
                    log_line.sudo().create(log_line.create_tracking_values(old_offer_price[offer.id], new_price, 'offer_price', 'float', 'product.product', offer.product_id.id, self.env.uid, offer.offer_catalog_id.company_id.id, object_name=offer.product_id.name))

        return ret

    @api.one
    def _get_offer_price(self):
        return self.fixed_price if self.offer_type == 1 else (self.product_id.list_price - (self.product_id.list_price / 100) * self.percent_discount)
