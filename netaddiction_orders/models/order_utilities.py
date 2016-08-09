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
        u"""Aggiunge un prodotto al carrello di un utente, se il prodotto è già presente nel carrello ne aggiorna la quantità sommando.

        Parametri:
        - partner_id id dell'utente
        - order_id id del carrello dell'utente
        - product_id id del prodotto da aggiungere
        - quantity quantità del prodotto da aggiungere DEVE ESSERE POSITIVO
        - bonus_list = [(bonus_id, bonus_qty)]  bonus_id id del prodotto bonus, bonus_qty quantità del prodotto bonus
        Return:
        - true se è andato tutto bene
        - false altrimenti

        Raises:
        -QtyLimitException: per qualche offerta carrello o vaucher viene superato il limite delle quantità
        -QtyMaxBuyableException nel caso in cui sia stata superata una qty_max_buyable per una offerta (catalogo,carrello o vaucher)
        -ProductOfferSoldOutAddToCart: per qualche offerta catalogo viene superato il limite delle quantità
        -ProductNotActiveAddToCartException se il prodotto non è attivo
        -ProductSoldOutAddToCartException se il prodotto è esaurito
        -ProductOrderQuantityExceededException se è stata superata la quantità max per il prodotto epr singolo ordine
        -ProductOrderQuantityExceededLimitException se con questo ordine si supera la quantità (disponibile) limite per il prodotto

        NB: non viene fatto alcun controllo sul fatto che i bonus siano effettivamente bonus del prodotto partner_id
        """
        if quantity < 0:
            return

        if partner_id is None:
            partner_id = self.env.ref('base.public_user_res_partner').id

        prod = self.env["product.product"].search([("id", "=", product_id)])

        if not prod or not prod.active:
            raise ProductNotActiveAddToCartException(product_id, "add_to_cart")

        if order and order.partner_id.id == partner_id and order.state == "draft":

            # se il prodotto è spento o esaurito eccezione
            if not prod.sale_ok:
                if not self.env.context.get('no_check_product_sold_out', False):
                    raise ProductSoldOutAddToCartException(product_id, "prodotto %s  sale_ok: %s" % (prod.name, prod.sale_ok))

            order.reset_cart()
            order.reset_voucher()

            found = False
            for line in order.order_line:
                if line.product_id.id == product_id:
                    prod.check_quantity_product(line.product_uom_qty + quantity)
                    self._check_offers_catalog(prod, line.product_uom_qty + quantity)
                    line.product_uom_qty += quantity
                    line.product_uom_change()
                    found = True
                    break

            if not found:
                prod.check_quantity_product(quantity)
                self._check_offers_catalog(prod, quantity)
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

            order._amount_all()

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

        if not prod or not prod.active:
            raise ProductNotActiveAddToCartException(product_id, "add_to_cart")

        if order and order.partner_id.id == partner_id and order.state == "draft":

            # se il prodotto è spento o esaurito eccezione
            if not prod.sale_ok:
                if not self.env.context.get('no_check_product_sold_out', False):
                    raise ProductSoldOutAddToCartException(product_id, "prodotto %s  sale_ok: %s" % (prod.name, prod.sale_ok))

            order.reset_cart()

            order.reset_voucher()

            found = False
            found_bonus = False
            for line in order.order_line:
                if line.product_id.id == product_id:
                    if quantity > 0:
                        prod.check_quantity_product(quantity)
                        self._check_offers_catalog(prod, quantity)
                        line.product_uom_qty = quantity
                        line.product_uom_change()
                    else:
                        line.unlink()
                    found = True
                    break

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

            order.extract_cart_offers()
            order.apply_voucher()
            # ricalcola gift e totale
            order._amount_all()

            return found or (bonus_list and found_bonus)

        return False

    def check_cart(self, order):
        """
        """
        for line in order.order_line:
            if not line.product_id or not line.product_id.active:
                raise ProductNotActiveAddToCartException(line.product_id, "add_to_cart")
            if not line.product_id.sale_ok:
                if not self.env.context.get('no_check_product_sold_out', False):
                    raise ProductSoldOutAddToCartException(line.product_id, "prodotto %s  sale_ok: %s" % (line.product_id.name, line.product_id.sale_ok))
            line.product_id.check_quantity_product(line.product_uom_qty)
            self._check_offers_catalog(line.product_id, line.product_uom_qty)

        problem = False
        for och in order.offers_cart:
            if not och.offer_cart_line or not och.offer_cart_line.active or (och.offer_cart_line.qty_limit > 0 and och.offer_cart_line.qty_selled + och.qty > och.offer_cart_line.qty_limit) or (och.offer_cart_line.qty_max_buyable > 0 and och.qty > och.offer_cart_line.qty_max_buyable):
                # se: l'offerta non è più attiva o è stata superata la quantità limite o è stata superata la quantità massima per singolo ordine
                problem = True
                break
        if problem:
            order.reset_cart()
            problem.extract_cart_offers()

        problem = False
        for ovh in order.offers_voucher:
            if not ovh.offer_id or not ovh.offer_id.active or (ovh.offer_id.qty_limit > 0 and ovh.offer_id.qty_selled + ovh.qty > ovh.offer_id.qty_limit) or (ovh.offer_id.qty_max_buyable > 0 and ovh.qty > ovh.offer_id.qty_max_buyable):
                # se: l'offerta non è più attiva o è stata superata la quantità limite o è stata superata la quantità massima per singolo ordine
                problem = True
                break
        if problem:
            order.reset_voucher()
            problem.apply_voucher()

    def _check_offers_catalog(self, product, qty_ordered):
        """controlla le offerte catalogo e aggiorna le quantità vendute.
        raise Exception se qualche prodotto ha superato la qty_limit per la sua offerta catalogo corrispondente
        """
        offer_line = product.offer_catalog_lines[0] if len(product.offer_catalog_lines) > 0 else None
        if(offer_line and offer_line.qty_limit > 0 and offer_line.qty_selled + qty_ordered > offer_line.qty_limit):
            raise ProductOfferSoldOutAddToCart(product.id, offer_line.offer_catalog_id.id, offer_line.qty_limit, offer_line.qty_selled, qty_ordered, offer_line.offer_catalog_id.name)


class ProductNotActiveAddToCartException(Exception):
    def __init__(self, product_id, err_str):
        super(ProductNotActiveAddToCartException, self).__init__(product_id)
        self.var_name = 'confirm_exception'
        self.err_str = err_str
        self.product_id = product_id

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s


class ProductSoldOutAddToCartException(Exception):
    def __init__(self, product_id, err_str):
        super(ProductSoldOutAddToCartException, self).__init__(product_id)
        self.var_name = 'confirm_exception'
        self.err_str = err_str
        self.product_id = product_id

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s


class ProductOfferSoldOutAddToCart(Exception):
    def __init__(self, product_id, offer_id, offer_limit, qty_selled, qty_to_add, err_str):
        super(ProductOfferSoldOutAddToCart, self).__init__(product_id)
        self.var_name = 'confirm_exception'
        self.err_str = err_str
        self.product_id = product_id
        self.offer_id = offer_id
        self.offer_limit = offer_limit
        self.qty_selled = qty_selled
        self.qty_to_add = qty_to_add

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta: %s  quantita limite: %s quantita venduta: %s quantita richiesta: %s   : %s" % (self.product_id, self.offer_id, self.offer_limit, self.qty_selled, self.qty_to_add, self.err_str)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta: %s  quantita limite: %s quantita venduta: %s quantita richiesta: %s   : %s" % (self.product_id, self.offer_id, self.offer_limit, self.qty_selled, self.qty_to_add, self.err_str)
        return s
