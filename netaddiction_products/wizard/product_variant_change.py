from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductVariantChange(models.TransientModel):
    _name = "product.variant.change"
    _description = "Modello Transient per aggiungere/rimuovere gli attributi nelle varianti."

    variant_id = fields.Many2one(
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
    attribute_id = fields.Many2one("product.attribute.value", string="Attributi Valore", required=True)

    def _get_combination_id(self):
        self.env.cr.execute(
            """SELECT ptav.id
                FROM
                    product_template_attribute_value ptav
                    JOIN
                        product_product pp
                        ON pp.product_tmpl_id = ptav.product_tmpl_id
                WHERE
                    product_attribute_value_id = %s
                    AND ptav.product_tmpl_id = %s
                    AND pp.id = %s;
            """,
            (self.attribute_id.id, self.variant_id.product_tmpl_id.id, self.variant_id.id),
        )
        try:
            return self.env.cr.fetchone()[0]
        except Exception:
            raise UserError("Impossibile trovare la combinazione con l'attributo e la variante selezionati")

    def do_action(self):
        comb_id = self._get_combination_id()
        if self.operation == "add":
            self.env.cr.execute(
                "INSERT INTO product_variant_combination VALUES(%s, %s);", (comb_id, self.variant_id.id)
            )
        elif self.operation == "remove":
            self.env.cr.execute(
                "DELETE FROM product_variant_combination WHERE product_template_attribute_value_id=%s AND product_product_id=%s;",
                (comb_id, self.variant_id.id),
            )
        self.env["product.product"].browse(self.variant_id.id)._compute_combination_indices()
