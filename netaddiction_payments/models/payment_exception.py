# -*- coding: utf-8 -*-

PAYPAL = "Paypal"
CREDITCARD = "Carta di credito"
CONTRASSEGNO = "Contrazzegno"
ZERO = "Pagamento a Zero"
SOFORT = "Sofort"
CASH = "Contanti"

class PaymentException(Exception):
    def __init__(self, payment_type,err_str):
        super(PaymentException, self).__init__(payment_type)
        self.var_name = 'payment_exception'
        self.err_str = err_str
        self.type = payment_type

        
    def __str__(self):
        s = u"Errore sul pagamento di tipo %s : %s " %(self.type, self.err_str)
        return s
    def __repr__(self):
        s = u"Errore sul pagamento di tipo %s : %s " %(self.type, self.err_str)
        return s