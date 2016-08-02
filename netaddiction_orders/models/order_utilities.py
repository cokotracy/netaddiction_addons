# -*- coding: utf-8 -*-

from openerp import models


class OrderUtilities(models.TransientModel):
    _name = "netaddiction.order.utilities"

    def get_cart(self, partner_id=None, order_id=None, create=False):
        """
        Restiusce il carrello dell'utente (ordine in draft) identificato da partner_id, se non esiste lo crea.
        Se l'utente non esiste ritorna False
        """
        order_model = self.env['sale.order']

        if order_id is not None:
            order = order_model.search([('id', '=', order_id)])

            if order and order.state == 'draft':
                return order, False

        if partner_id is not None:
            partner = self.env['res.partner'].search([('id', '=', partner_id)])

            if not partner:
                raise Exception('Partner not found')

            orders = order_model.search([('partner_id', '=', partner_id)], order='create_date desc')

            if orders and orders[0].state == 'draft':
                return orders[0], False

        if create:
            cart = order_model.create({
                'partner_id': partner_id or self.env.ref('base.public_user_res_partner').id,
                'state': 'draft',
            })

            return cart, True

        return None, False

    def add_to_cart(self, order, product_id, quantity, partner_id=None, bonus_list=None):
        """
        Aggiunge un prodotto al carrello di un utente, se il prodotto è già presente nel carrello ne aggiorna la quantità sommando
        Parametri:
        - partner_id id dell'utente
        - order_id id del carrello dell'utente
        - product_id id del prodotto da aggiungere
        - quantity quantità del prodotto da aggiungere DEVE ESSERE POSITIVO
        - bonus_list = [(bonus_id, bonus_qty)]  bonus_id id del prodotto bonus, bonus_qty quantità del prodotto bonus
        Return:
        - true se è andato tutto bene
        - false altrimenti

        NB: non viene fatto alcun controllo sul fatto che i bonus siano effettivamente bonus del prodotto partner_id
        """
        if quantity < 0:
            return

        if partner_id is None:
            partner_id = self.env.ref('base.public_user_res_partner').id

        prod = self.env["product.product"].search([("id", "=", product_id)])

        if order and order.partner_id.id == partner_id and order.state == "draft" and prod:

            order.reset_cart()
            order.reset_voucher()

            found = False
            for line in order.order_line:
                if line.product_id.id == product_id:
                    line.product_uom_qty += quantity
                    line.product_uom_change()
                    found = True
                    break

            if not found:
                ol = self.env["sale.order.line"].create({
                    "order_id": order.id,
                    "product_id": product_id,
                    "product_uom_qty": quantity,
                    "product_uom": prod.uom_id.id,
                    "name": prod.display_name,
                })

                ol.product_id_change()

            if bonus_list:
                for bonus_id, bonus_qty in bonus_list:
                    bonus_prod = self.env["product.product"].search([("id", "=", bonus_id)])

                    if bonus_prod:
                        found = False
                        for line in order.order_line:
                            if line.product_id.id == bonus_id and bonus_qty > 0:
                                line.product_uom_qty += bonus_qty
                                line.product_uom_change()
                                found = True
                                break

                        if not found:
                            ol_bonus = self.env["sale.order.line"].create({
                                "order_id": order.id,
                                "product_id": bonus_id,
                                "product_uom_qty": bonus_qty,
                                "bonus_father_id": ol.id,
                                "product_uom": bonus_prod.uom_id.id,
                                "name": bonus_prod.display_name,
                            })

                            ol_bonus.product_id_change()

            order.extract_cart_offers()
            order.apply_voucher()

            return True

        return False

    def set_quantity(self, order, product_id, quantity, partner_id=None, bonus_list=None):
        """
        Aggiorna la quantità del prodotto product_id a quantity nell'ordine order_id
        Parametri:
        - partner_id id dell'utente
        - order_id id del carrello dell'utente
        - product_id id del prodotto da aggiungere
        - quantity quantità del prodotto da aggiornare
        - bonus_list = [(bonus_id, bonus_qty)]  bonus_id id del prodotto bonus, bonus_qty quantità del prodotto bonus
        Return:
        - true se è stata aggiornata una quantità
        - false altrimenti

        NB: non viene fatto alcun controllo sul fatto che i bonus siano effettivamente bonus del prodotto partner_id
        """
        if partner_id is None:
            partner_id = self.env.ref('base.public_user_res_partner').id

        prod = self.env["product.product"].search([("id", "=", product_id)])

        if order and order.partner_id.id == partner_id and order.state == "draft" and prod:
            print "1"
            order.reset_cart()
            print "2"
            order.reset_voucher()
            print "3"

            found = False
            found_bonus = False
            for line in order.order_line:
                print "4"
                if line.product_id.id == product_id:
                    print "5"
                    if quantity > 0:
                        line.product_uom_qty = quantity
                        line.product_uom_change()
                    else:
                        line.unlink()
                    found = True
                    break
            print "6"
            if bonus_list:
                for bonus_id, bonus_qty in bonus_list:
                    bonus_prod = self.env["product.product"].search([("id", "=", bonus_id)])

                    if bonus_prod:
                        for line in order.order_line:
                            if line.product_id.id == bonus_id:
                                if bonus_qty > 0:
                                    line.product_uom_qty = bonus_qty
                                    line.product_uom_change()
                                else:
                                    line.unlink()
                                found_bonus = True
                                break
            print "7"
            order.extract_cart_offers()
            print "8"
            order.apply_voucher()
            print "9"

            return found or (bonus_list and found_bonus)

        return False
