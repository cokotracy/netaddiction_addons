# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class OrderUtilities(models.TransientModel):

    _name = "netaddiction.order.utilities"


    @api.one
    def get_cart(self,user_id=False, order_id=False):
        """
        Restiusce il carrello dell'utente(ordine in draft) identificato da user_id, se non esiste lo crea.
        Se l'utente non esiste ritorna False
        """
        if order_id :
            order = self.env["sale.order"].search([("id","=",order_id)])
            if order.state == 'draft':
                return order
            else:
                user_id =False

        if not user_id:
            #get user
            pub_user_id = self.env['ir.model.data'].get_object('netaddiction_orders', 'public_user').id
            return self.env["sale.order"].create({"partner_id":pub_user_id, "state":"draft"}) 
            
        usr = self.env["res.partner"].search([("id","=",user_id)])
        if not usr:
            pub_user_id = self.env['ir.model.data'].get_object('netaddiction_orders', 'public_user').id
            return self.env["sale.order"].create({"partner_id":pub_user_id, "state":"draft"})

        if len(usr.sale_order_ids) > 0:
            ord_lst = self.env["sale.order"].search([("partner_id","=",user_id)],order="create_date desc")
            if ord_lst and ord_lst[0].state == "draft":
                return ord_lst[0]

        return self.env["sale.order"].create({"partner_id":user_id, "state":"draft"})


    @api.one
    def add_to_cart(self,user_id,order_id,product_id,qty,bonus_list=None):
        """
        Aggiunge un prodotto al carrello di un utente
        Parametri:
        - user_id id dell'utente
        - order_id id del carrello dell'utente
        - product_id id del prodotto da aggiungere
        - qty quantità del prodotto da aggiungere
        - bonus_list = [(bonus_id, bonus_qty)]  bonus_id id del prodotto bonus, bonus_qty quantità del prodotto bonus
        Return:
        - true se è andato tutto bene
        - false altrimenti

        NB: non viene fatto alcun controllo sul fatto che i bonus siano effettivamente bonus del prodotto user_id
        """
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
                        ol_bonus.product_id_change()
            return True
        else:
            return False