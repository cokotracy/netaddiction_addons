# -*- coding: utf-8 -*-

from openerp import models
from openerp.addons.netaddiction_products.models.products import ProductOrderQuantityExceededLimitException, ProductOrderQuantityExceededException
from openerp.addons.netaddiction_special_offers.models.offers_product import QtyLimitException, QtyMaxBuyableException
import time

LIMIT_QTY_PER_PRODUCT = 20


class OrderUtilities(models.TransientModel):
    _name = "netaddiction.order.utilities"

    def get_cart(self, partner_id=None, order_id=None, create=False, from_customer=True):
        """
        Restiusce il carrello dell'utente (ordine in draft) identificato da partner_id, se non esiste lo crea.
        Se l'utente non esiste ritorna False
        """
        order_model = self.env['sale.order']

        if order_id is not None:
            query = [('id', '=', order_id)]

            if from_customer:
                query.append(('created_by_the_customer', '=', True))

            order = order_model.search(query)

            if order and order.state == 'draft':
                return order, False

        if partner_id is not None:
            partner = self.env['res.partner'].search([('id', '=', partner_id)])

            if not partner:
                raise Exception('Partner not found')

            query = [('partner_id', '=', partner_id)]

            if from_customer:
                query.append(('created_by_the_customer', '=', True))

            orders = order_model.search(query, order='create_date desc')

            if orders and orders[0].state == 'draft':
                return orders[0], False

        if create:
            cart = order_model.create({
                'created_by_the_customer': from_customer,
                'partner_id': partner_id or self.env.ref('base.public_user_res_partner').id,
                'state': 'draft',
            })

            return cart, True

        return None, False

    def check_quantity_b2b(self, order, product_id, qty):
        # controlla se l'ordine è b2b, eventualmente cerca se i lprodotto è presente in quel listino
        # se è presente nel listino assegnato allora controlla la quantità limite b2b
        if order.is_b2b:
            pricelist_line = self.env['product.pricelist.item'].search([('product_id', '=', product_id), ('pricelist_id', '=', order.pricelist_id.id)])
            if pricelist_line:
                product = self.env['product.product'].browse(product_id)
                qty_limit = pricelist_line.qty_lmit_b2b
                qty_residual = product.qty_available_now - qty_limit
                if product.qty_available_now - qty < qty_limit:
                    if qty_residual < 0:
                        qty_residual = 0
                    message = "Non puoi ordinare piu di %s pezzi per %s " % (qty_residual, product.display_name)
                    raise ProductOrderQuantityExceededLimitException(product_id, qty_residual, message)


    def add_to_cart(self, order, product_id, quantity, partner_id=None, bonus_list=None):
        u"""Aggiunge un prodotto al carrello di un utente, se il prodotto è già presente nel carrello ne aggiorna la quantità sommando.

        Parametri:
        - partner_id id dell'utente
        - order_id id del carrello dell'utente
        - product_id id del prodotto da aggiungere
        - quantity quantità del prodotto da aggiungere DEVE ESSERE POSITIVO
        - bonus_list = [(bonus_id, bonus_qty)]  bonus_id id del prodotto bonus, bonus_qty quantità del prodotto bonus
        Return:
        - {} se è andato tutto bene
        - {'id prodotto bonus' : (qty richiesta, qty disponibile settata sulla line)} se c'è stato qualche problema con le quantità dei bonus
        - false se non si trova l'ordine o non è associato al partner_id ricevuto o non è in draft

        Raises:
        -QtyLimitException: per qualche offerta carrello o vaucher viene superato il limite delle quantità
        -QtyMaxBuyableException nel caso in cui sia stata superata una qty_max_buyable per una offerta (catalogo,carrello o vaucher)
        -ProductOfferSoldOutAddToCartException: per qualche offerta catalogo viene superato il limite delle quantità
        -ProductNotActiveAddToCartException se il prodotto non è attivo
        -ProductSoldOutAddToCartException se il prodotto è esaurito
        -ProductOrderQuantityExceededException se è stata superata la quantità max per il prodotto epr singolo ordine
        -ProductOrderQuantityExceededLimitException se con questo ordine si supera la quantità (disponibile) limite per il prodotto
        -QuantityLessThanZeroException se quantity <= 0
        -BonusOfferException: se ci sono dei problemi con i bonus
        -QuantityOverLimitException se quantity > LIMIT_QTY_PER_PRODUCT e cliente non b2b
        
        """


        if quantity <= 0:
            raise QuantityLessThanZeroException()

        if partner_id is None:
            partner_id = self.env.ref('base.public_user_res_partner').id

        prod = self.env["product.product"].search([("id", "=", product_id)])

        if not prod or not prod.active:
            raise ProductNotActiveAddToCartException(product_id, "add_to_cart")


        if order and order.partner_id.id == partner_id and order.state == "draft":
            
            # se il prodotto è spento o esaurito eccezione
            if not prod.sale_ok:
                if not self.env.context.get('no_check_product_sold_out', False):
                    raise ProductSoldOutAddToCartException(product_id, prod.name, "prodotto %s  sale_ok: %s" % (prod.name, prod.sale_ok))

            if not order.partner_id.is_b2b and quantity > LIMIT_QTY_PER_PRODUCT:
                raise QuantityOverLimitException(prod.name) 

            order.reset_cart()
            order.reset_voucher()

            

            found = False
            ol = None
            start_time_quant = time.time()
            for line in order.order_line:
                if line.product_id.id == product_id:
                    self.check_quantity_b2b(order, product_id, line.product_uom_qty + quantity)
                    if not order.partner_id.is_b2b and line.product_uom_qty + quantity > LIMIT_QTY_PER_PRODUCT:
                        raise QuantityOverLimitException(line.product_id.name)
                    prod.check_quantity_product(line.product_uom_qty + quantity)
                    self._check_offers_catalog(prod, line.product_uom_qty + quantity)
                    line.product_uom_qty += quantity
                    line.product_uom_change()
                    ol = line
                    found = True
                    break
            total_time_quant = time.time() - start_time_quant

            
            if not found:
                start_time_b2b = time.time()
                self.check_quantity_b2b(order, product_id, quantity)
                total_time_b2b = time.time() - start_time_b2b
                start_time_check = time.time()
                prod.check_quantity_product(quantity)
                total_time_check = time.time() - start_time_check
                start_time_off = time.time()
                self._check_offers_catalog(prod, quantity)
                total_time_off = time.time() - start_time_off
                start_time_ol = time.time()
                ol = self.env["sale.order.line"].create({
                    "order_id": order.id,
                    "product_id": product_id,
                    "product_uom_qty": quantity,
                    "product_uom": prod.uom_id.id,
                    "name": prod.display_name,
                })
                total_time_ol = time.time() - start_time_ol
                start_time_change = time.time()
                ol.product_id_change()
                total_time_change = start_time_change - time.time()

            start_time_five = time.time()

            ret = {}
            if bonus_list:
                # controllo che il prodotto abbia bonus o che che lo se lo ha only one mi hanno passato un solo bonus
                if not prod.offer_with_bonus_lines or (prod.offer_with_bonus_lines[0].bonus_offer_id.only_one and len(bonus_list) > 1):
                    raise BonusOfferException(None)

                # lista degli id dei prodotti accettati come bonus
                correct_bonus_list = [bonus.product_id.id for bonus in prod.offer_with_bonus_lines[0].bonus_offer_id.bonus_products_list if bonus.active]
                for bonus_id, bonus_qty in bonus_list:
                    if bonus_id not in correct_bonus_list or bonus_qty > quantity:
                        raise BonusOfferException(bonus_id)
                    bonus_prod = self.env["product.product"].search([("id", "=", bonus_id)])

                    if bonus_prod:
                        found = False
                        for line in order.order_line:
                            if line.product_id.id == bonus_id and bonus_qty > 0:
                                # controllo che sia assegnata alla linea giusta
                                if line.bonus_father_id.id != ol.id:
                                    raise BonusOfferException(bonus_id)
                                try:
                                    bonus_prod.check_quantity_product(line.product_uom_qty + bonus_qty)
                                    line.product_uom_qty += bonus_qty
                                except (ProductOrderQuantityExceededLimitException, ProductOrderQuantityExceededException), e:
                                    ret[line.product_id.id] = (bonus_qty, e.remains_quantity)
                                    if e.remains_quantity > 0:
                                        line.product_uom_qty = e.remains_quantity
                                    else:
                                        line.unlink()
                                        found = True
                                        break
                                line.product_uom_change()
                                found = True
                                break

                        if not found:
                            try:
                                bonus_prod.check_quantity_product(bonus_qty)
                            except (ProductOrderQuantityExceededLimitException, ProductOrderQuantityExceededException), e:
                                ret[bonus_id] = (bonus_qty, e.remains_quantity)
                                bonus_qty = e.remains_quantity
                            if bonus_qty > 0:
                                ol_bonus = self.env["sale.order.line"].create({
                                    "order_id": order.id,
                                    "product_id": bonus_id,
                                    "product_uom_qty": bonus_qty,
                                    "bonus_father_id": ol.id,
                                    "product_uom": bonus_prod.uom_id.id,
                                    "name": bonus_prod.display_name,
                                })

                                ol_bonus.product_id_change()
            total_time_five = start_time_five - time.time()
            start_time_six = time.time()
            try:
                order.extract_cart_offers()
                order.apply_voucher()
            except ValueError as e:
                ol.product_uom_qty -= quantity
                if ol.product_uom_qty <= 0:
                    ol.unlink()
                raise e

            order._amount_all()

            total_time_six = start_time_six - time.time()

            message = "check_quantity_b2b: %s check_qty_product: %s _check_offers_catalog: %s Creazione OrderLine: %s product_id_change: %s Bonuslist ha valore: %s Six: %s" % (total_time_b2b, total_time_check, total_time_off, total_time_ol, total_time_change, bonus_list, total_time_six)
            self._send_debug_mail(message, "DEBUG TEMPI B2B")

            return ret

        return False

    def set_quantity(self, order, product_id, quantity, partner_id=None):
        """
        Aggiorna la quantità del prodotto product_id a quantity nell'ordine order_id
        Parametri:
        - partner_id id dell'utente
        - order_id id del carrello dell'utente
        - product_id id del prodotto da aggiungere
        - quantity quantità del prodotto da aggiornare DEVE ESSERE POSITIVO
        - bonus_list = [(bonus_id, bonus_qty)]  bonus_id id del prodotto bonus, bonus_qty quantità del prodotto bonus
        Return:
        - {} se è andato tutto bene
        - {'id prodotto bonus' : (qty richiesta, qty disponibile settata sulla line)} se c'è stato qualche problema con le quantità dei bonus
        - false se non si trova l'ordine o non è associato al partner_id ricevuto o non è in draft

        Raises:
        -QtyLimitException: per qualche offerta carrello o vaucher viene superato il limite delle quantità
        -QtyMaxBuyableException nel caso in cui sia stata superata una qty_max_buyable per una offerta (catalogo,carrello o vaucher)
        -ProductOfferSoldOutAddToCartException: per qualche offerta catalogo viene superato il limite delle quantità
        -ProductNotActiveAddToCartException se il prodotto non è attivo
        -ProductSoldOutAddToCartException se il prodotto è esaurito
        -ProductOrderQuantityExceededException se è stata superata la quantità max per il prodotto epr singolo ordine
        -ProductOrderQuantityExceededLimitException se con questo ordine si supera la quantità (disponibile) limite per il prodotto
        -QuantityOverLimitException se quantity > LIMIT_QTY_PER_PRODUCT e cliente non b2b


        """

        if partner_id is None:
            partner_id = self.env.ref('base.public_user_res_partner').id

        prod = self.env["product.product"].search([("id", "=", product_id)])

        if not prod or (quantity > 0 and not prod.active):
            raise ProductNotActiveAddToCartException(product_id, "add_to_cart")

        if order and order.partner_id.id == partner_id and order.state == "draft":

            # se il prodotto è spento o esaurito eccezione
            if quantity > 0 and not prod.sale_ok:
                if not self.env.context.get('no_check_product_sold_out', False):
                    raise ProductSoldOutAddToCartException(product_id, prod.name, "prodotto %s  sale_ok: %s" % (prod.name, prod.sale_ok))

            if quantity > 0 and not order.partner_id.is_b2b and quantity > LIMIT_QTY_PER_PRODUCT:
                raise QuantityOverLimitException(prod.name)

            self.check_quantity_b2b(order, product_id, quantity)

            order.reset_cart()

            order.reset_voucher()
            ret = {}
            found = False
            ol = None
            prev_qty = 0
            for line in order.order_line:
                if line.product_id.id == product_id:
                    if quantity > 0:
                        prod.check_quantity_product(quantity)
                        self._check_offers_catalog(prod, quantity)
                        prev_qty = line.product_uom_qty
                        line.product_uom_qty = quantity
                        line.product_uom_change()
                        ol = line
                    else:
                        line.unlink()
                    found = True
                    break

            if found and ol:
                for bonus_ol in ol.bonus_order_line_ids:
                    if quantity > 0:
                        try:
                            bonus_ol.product_id.check_quantity_product(quantity)
                            bonus_ol.product_uom_qty = quantity
                        except (ProductOrderQuantityExceededLimitException, ProductOrderQuantityExceededException), e:
                            bonus_ol.product_uom_qty = e.remains_quantity
                            ret[bonus_ol.product_id.id] = (quantity, e.remains_quantity)
                    else:
                        bonus_ol.unlink()

            try:
                order.extract_cart_offers()
                order.apply_voucher()
            except ValueError as e:
                ol.product_uom_qty = prev_qty
                if ol.product_uom_qty <= 0:
                    ol.unlink()
                raise e
            # ricalcola gift e totale
            order._amount_all()

            return ret

        return False

    def check_cart(self, order):
        u"""Controlla che lo stato del carrello sia consistente con quantità prodotto e offerte.

        Raises:
        -QtyLimitException: per qualche offerta carrello o vaucher viene superato il limite delle quantità
        -QtyMaxBuyableException nel caso in cui sia stata superata una qty_max_buyable per una offerta (catalogo,carrello o vaucher)
        -ProductOfferSoldOutAddToCartException: per qualche offerta catalogo viene superato il limite delle quantità
        -ProductNotActiveAddToCartException se il prodotto non è attivo
        -ProductSoldOutAddToCartException se il prodotto è esaurito
        -ProductOrderQuantityExceededException se è stata superata la quantità max per il prodotto epr singolo ordine
        -ProductOrderQuantityExceededLimitException se con questo ordine si supera la quantità (disponibile) limite per il prodotto
        -CatalogOfferCancelledException se nel carrello c'è una offerta catalogo cancellata
        -CartOfferCancelledException se nel carrello c'è una offerta carrello cancellata
        -VaucherOfferCancelledException se nel carrello c'è una offerta vaucher cancellata
        -BonusOfferException se nel carrello c'è una offerta bonus cancellata

        """
        for line in order.order_line:
            if not line.product_id or not line.product_id.active:
                prod_name = line.product_id.name
                line.unlink()
                raise ProductNotActiveAddToCartException(prod_name, "add_to_cart")
            if not line.product_id.sale_ok:
                if not self.env.context.get('no_check_product_sold_out', False):
                    prod_id = line.product_id.id
                    prod_name = line.product_id.name
                    prod_sale_ok = line.product_id.sale_ok
                    line.unlink()
                    raise ProductSoldOutAddToCartException(prod_id, prod_name, "prodotto %s  sale_ok: %s" % (prod_name, prod_sale_ok))
            try:
                self.check_quantity_b2b(order, line.product_id.id, line.product_uom_qty)
                line.product_id.check_quantity_product(line.product_uom_qty)
            except (ProductOrderQuantityExceededLimitException, ProductOrderQuantityExceededException), e:
                if line.bonus_father_id:
                    # è un bonus cambio la quantità e bon
                    line.product_uom_qty = e.remains_quantity
                else:
                    # è un prodotto vero, devo lanciare l'eccezione    
                    e.product_id = line.product_id.name
                    raise e
            if line.offer_type and not line.negate_offer:
                if len(line.product_id.offer_catalog_lines) > 0:
                    self._check_offers_catalog(line.product_id, line.product_uom_qty)
                else:
                    prod_id = line.product_id.id
                    offer_type = line.offer_type
                    prod_name = line.product_id.name
                    line.unlink()
                    raise CartOfferCancelledException(prod_id, offer_type, prod_name)

            # lista degli id dei prodotti accettati come bonus
            correct_bonus_list = []
            if line.product_id.offer_with_bonus_lines:
                correct_bonus_list = [bonus.product_id.id for bonus in line.product_id.offer_with_bonus_lines[0].bonus_offer_id.bonus_products_list if bonus.active]
            for ol_bonus in line.bonus_order_line_ids:
                if ol_bonus.product_id.id not in correct_bonus_list or ol_bonus.product_uom_qty > line.product_uom_qty:
                    prod_name = ol_bonus.product_id.name
                    ol_bonus.unlink()
                    raise BonusOfferException(prod_name)

        problem = False
        for och in order.offers_cart:
            if not och.offer_cart_line or not och.offer_cart_line.active or (och.offer_cart_line.qty_limit > 0 and och.offer_cart_line.qty_selled + och.qty > och.offer_cart_line.qty_limit) or (och.offer_cart_line.qty_max_buyable > 0 and och.qty > och.offer_cart_line.qty_max_buyable):
                # se: l'offerta non è più attiva o è stata superata la quantità limite o è stata superata la quantità massima per singolo ordine
                problem = True
                break
        if problem:
            order.reset_cart()
            raise CatalogOfferCancelledException(och.product_id.id, och.offer_type, och.product_id.name)
            # order.extract_cart_offers()

        problem = False
        for ovh in order.offers_voucher:
            if not ovh.offer_id or not ovh.offer_id.active or (ovh.offer_id.qty_limit > 0 and ovh.offer_id.qty_selled + ovh.qty > ovh.offer_id.qty_limit):
                # se: l'offerta non è più attiva o è stata superata la quantità limite o è stata superata la quantità massima per singolo ordine
                problem = True
                break
        if problem:
            order.reset_voucher()
            raise VaucherOfferCancelledException(ovh.product_id.id, ovh.offer_id, ovh.product_id.name)
            # order.apply_voucher()
        

    def _check_offers_catalog(self, product, qty_ordered):
        """controlla le offerte catalogo e aggiorna le quantità vendute.
        raise Exception se qualche prodotto ha superato la qty_limit per la sua offerta catalogo corrispondente
        """
        offer_line = product.offer_catalog_lines[0] if len(product.offer_catalog_lines) > 0 else None
        if offer_line:
            if offer_line.qty_limit > 0 and offer_line.qty_selled + qty_ordered > offer_line.qty_limit:
                raise QtyLimitException(product.name, product.id, offer_line.offer_catalog_id.id, offer_line.qty_limit, qty_ordered, offer_line.qty_selled)
            elif offer_line.qty_max_buyable > 0 and qty_ordered > offer_line.qty_max_buyable:
                raise QtyMaxBuyableException(product.name, product.id, offer_line.offer_catalog_id.id, offer_line.qty_max_buyable, qty_ordered)

    def _send_debug_mail(self, body, subject):
        """
        utility invio mail tempi
        """
        values = {
            'subject': subject,
            'body_html': body,
            'email_from': "shopping@multiplayer.com",
            # TODO 'email_to': "ecommerce-servizio@netaddiction.it",
            'email_to': "andrea.bozzi@netaddiction.it, matteo.piciucchi@netaddiction.it",
        }

        email = self.env['mail.mail'].create(values)
        email.send()


class ProductNotActiveAddToCartException(Exception):
    def __init__(self, product_id, err_str):
        super(ProductNotActiveAddToCartException, self).__init__(product_id)
        self.var_name = 'product_not_active'
        self.err_str = err_str
        self.product_id = product_id

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s


class ProductSoldOutAddToCartException(Exception):
    def __init__(self, product_id, prod_name, err_str):
        super(ProductSoldOutAddToCartException, self).__init__(product_id)
        self.var_name = 'product_sold_out'
        self.err_str = err_str
        self.product_id = product_id
        self.prod_name = prod_name

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s : %s" % (self.product_id, self.err_str)
        return s


class ProductOfferSoldOutAddToCartException(Exception):
    def __init__(self, product_id, offer_id, offer_limit, qty_selled, qty_to_add, prod_name, err_str):
        super(ProductOfferSoldOutAddToCartException, self).__init__(product_id)
        self.var_name = 'product_offer_sold_out'
        self.err_str = err_str
        self.product_id = product_id
        self.offer_id = offer_id
        self.offer_limit = offer_limit
        self.qty_selled = qty_selled
        self.qty_to_add = qty_to_add
        self.prod_name = prod_name

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta: %s  quantita limite: %s quantita venduta: %s quantita richiesta: %s   : %s" % (self.product_id, self.offer_id, self.offer_limit, self.qty_selled, self.qty_to_add, self.err_str)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta: %s  quantita limite: %s quantita venduta: %s quantita richiesta: %s   : %s" % (self.product_id, self.offer_id, self.offer_limit, self.qty_selled, self.qty_to_add, self.err_str)
        return s


class CatalogOfferCancelledException(Exception):
    def __init__(self, product_id, offer_type, prod_name):
        super(CatalogOfferCancelledException, self).__init__(product_id)
        self.var_name = 'catalog_offer_cancelled'
        self.product_id = product_id
        self.offer_type = offer_type
        self.prod_name = prod_name

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta catalogo di tipo: %s che non è piu attiva" % (self.product_id, self.offer_type)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta vatalogo di tipo: %s che non è piu attiva" % (self.product_id, self.offer_type)
        return s


class CartOfferCancelledException(Exception):
    def __init__(self, product_id, offer_type, prod_name):
        super(CartOfferCancelledException, self).__init__(product_id)
        self.var_name = 'cart_offer_cancelled'
        self.product_id = product_id
        self.offer_type = offer_type
        self.prod_name = prod_name

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta carrello di tipo: %s che non è piu attiva" % (self.product_id, self.offer_type)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta carrello di tipo: %s che non è piu attiva" % (self.product_id, self.offer_type)
        return s


class VaucherOfferCancelledException(Exception):
    def __init__(self, product_id, offer_id, prod_name):
        super(VaucherOfferCancelledException, self).__init__(product_id)
        self.var_name = 'vaucher_offer_cancelled'
        self.product_id = product_id
        self.offer_id = offer_id
        self.prod_name = prod_name

    def __str__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta vaucher di tipo: %s che non è piu attiva" % (self.product_id, self.offer_id)
        return s

    def __repr__(self):
        s = u"Errore aggiungendo all'ordine il prodotto: %s per l'offerta vaucher di tipo: %s che non è piu attiva" % (self.product_id, self.offer_id)
        return s


class BonusOfferException(Exception):
    def __init__(self, product_id):
        super(BonusOfferException, self).__init__(product_id)
        self.var_name = 'vaucher_offer_cancelled'
        self.product_id = product_id
        
    def __str__(self):
        s = u"Errore sui bonus del prodotto: %s " % (self.product_id)
        return s

    def __repr__(self):
        s = u"Errore sui bonus del prodotto: %s " % (self.product_id)
        return s


class QuantityLessThanZeroException(Exception):
    def __init__(self):
        super(QuantityLessThanZeroException, self).__init__()
        self.var_name = 'quantity_less_than_zero'

    def __str__(self):
        s = u"quantity < 0"
        return s

    def __repr__(self):
        s = u"quantity < 0"
        return s


class QuantityOverLimitException(Exception):
    def __init__(self, prod_name):
        super(QuantityOverLimitException, self).__init__()
        self.var_name = 'quantity_over_limit'
        self.prod_name = prod_name

    def __str__(self):
        s = u"Quantità sopra il limite per il prodotto %s. Il limite è %s" % (self.prod_name, LIMIT_QTY_PER_PRODUCT)
        return s

    def __repr__(self):
        s = u"quantity < 0"
        return s
