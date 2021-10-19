from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductVariantChange(models.TransientModel):
    _name = "product.variant.change"
    _description = "Modello Transient per aggiungere/rimuovere gli attributi nelle varianti."

    variant = fields.Many2one(
        "product.product",
        string="Varianti Prodotto",
        domain=lambda self: f"[('product_tmpl_id', 'in', {self.env.context.get('active_ids', [])})]",
        required=True,
    )
    operation = fields.Selection(
        [("add", "Aggiungi Attributo"), ("remove", "Rimuovi Attributo")],
        required=True,
        default="add",
        string="Operazione",
    )
    attribute = fields.Many2one("product.attribute.value", string="Attributi Valore", required=True)

    def _get_combination_id(self):
        q = f"""SELECT ptav.id
                FROM
                    product_template_attribute_value ptav
                    JOIN
                        product_product pp
                        ON pp.product_tmpl_id = ptav.product_tmpl_id
                WHERE
                    product_attribute_value_id = {self.attribute.id}
                    AND ptav.product_tmpl_id = {self.variant.product_tmpl_id.id}
                    AND pp.id = {self.variant.id};
            """
        self.env.cr.execute(q)
        try:
            return self.env.cr.fetchone()[0]
        except Exception:
            raise UserError("Impossibile trovare la combinazione con l'attributo e la variante selezionati")

    def do_action(self):
        comb_id = self._get_combination_id()
        if self.operation == "add":
            self.env.cr.execute(f"INSERT INTO product_variant_combination VALUES({comb_id}, {self.variant.id});")
        if self.operation == "remove":
            self.env.cr.execute(
                f"DELETE FROM product_variant_combination WHERE product_template_attribute_value_id={comb_id} AND product_product_id={self.variant.id};"
            )
        self.env["product.product"].browse(self.variant.id)._compute_combination_indices()
