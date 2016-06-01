# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class OrderUtilities(models.TransientModel):

    _name = "netaddiction.order.utilities"


    @api.one
    def get_cart(self,user_id):
        usr = self.env["res.partner"].search([("id","=",user_id)])
        if not usr:
            return False

        if len(usr.sale_order_ids) > 0:
            ord_lst = self.env["sale.order"].search([("partner_id","=",user_id)],order="create_date desc")
            if ord_lst and ord_lst[0].state == "draft":
                return ord_lst[0]

        return self.env["sale.order"].create({"partner_id":user_id, "state":"draft"})


    @api.one
    def add_to_cart(self,user_id,order_id,product_id,qty,bonus_list=None):
        order = self.env["sale.order"].search([("id","=",order_id)])
        prod = self.env["product.product"].search([("id","=",product_id)])
        if order and order.partner_id.id == user_id and order.state == "draft" and prod:
            ol = self.env["sale.order.line"].create({"order_id":order_id,"product_id":product_id,"product_uom_qty":qty, "product_uom":prod.uom_id.id,"name":prod.display_name})
            ol.product_id_change()
            if bonus_list:
                for bonus_id, bonus_qty in bonus_list:
                    bonus_prod = self.env["product.product"].search([("id","=",bonus_id)])
                    if bonus_prod:
                        ol_bonus = self.env["sale.order.line"].create({"order_id":order_id,"product_id":bonus_id,"product_uom_qty":bonus_qty,"bonus_father_id":ol.id,"product_uom":bonus_prod.uom_id.id,"name":bonus_prod.display_name})
            return True
        else:
            return False