from odoo import models
from odoo.tools.safe_eval import safe_eval


class CustomFacebookMerchantShop(models.Model):
    _inherit = "fb.facebook.shop"

    def create_xml(self, **kw):
        final_xml = self._get_dict()
        self._store_data(final_xml)
        message = "Attachment is Created Please enter the following URL to the Facebook Catalog :-" + self.feed_url
        if not kw.get("cron"):
            return self.env["wk.wizard.message"].genrated_message(message=message, name="Message")
        else:
            pass

    def _get_dict(self):
        field_mapping_lines_ids = self.field_mapping_id.field_mapping_line_ids
        final_dict = {}
        final_dict["title"] = self.with_context(lang=self.content_language_id.code).name
        final_dict["link"] = self.shop_url
        products = self._get_product_detail(field_mapping_lines_ids.ids)
        final_dict["entry"] = self._get_product_mapping(products, field_mapping_lines_ids)

        return self._wrap2xml(final_dict)

    def _get_product_detail(self, field_mapping_lines_ids):
        sel_type = self.product_selection_type
        context = self._context.copy()
        context.update(
            {
                "pricelist": self.pricelist_id.id,
                "website_id": self.website_id.id,
                "lang": self.content_language_id.code,
                "warehouse": self.warehouse_id.id if self.warehouse_id else False,
            }
        )
        limit = 0
        if sel_type == "domain":
            domain = safe_eval(self.domain_input)
            final_domain = self._get_final_domain(domain=domain)
            limit = self.limit
        elif sel_type == "manual":
            return self.product_ids_rel.with_context(context)
        elif sel_type == "category":
            categ_ids = self.public_categ_ids.ids
            categ_domain = [("public_categ_ids", "child_of", categ_ids)]
            final_domain = self._get_final_domain(domain=categ_domain)
        else:
            return False
        if limit > 0:
            return self.env["product.product"].with_context(context).search(final_domain, limit=limit)
        return self.env["product.product"].with_context(context).search(final_domain)
