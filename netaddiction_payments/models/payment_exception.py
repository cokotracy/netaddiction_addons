# -*- coding: utf-8 -*-

PAYPAL = "Paypal"
CREDITCARD = "Carta di credito"
CONTRASSEGNO = "Contrazzegno"
ZERO = "Pagamento a Zero"
SOFORT = "Sofort"

class PaymentException(Exception):
    def __init__(self, payment_type,err_str):
        self.var_name = 'payment_exception'
        self.err_str = err_str
        self.type = payment_type
        
    def __str__(self):
        s = u"Quantity massima acquistabile in offerta ecceduta %s id: %s " %(self.payment_type, self.err_str)
        return s
    def __repr__(self):
        s = u"Quantity massima acquistabile in offerta ecceduta %s id: %s" %(self.prod, self.prod_id)
        return s