# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
import datetime
import pickle
import base64
import os
from ftplib import FTP

import StringIO
import io

def replace_vowels(text):
    """
    Sostituisce le vocali accentate con le corrispondenti non accentate
    """         
    return text.replace(u"à", u'a'
        ).replace(u"á", u'a'
        ).replace(u"ä", u'a'
        ).replace(u"ã", u"a"
        ).replace(u"â", u"a"
        ).replace(u"è", u"e"
        ).replace(u"é", u"e"
        ).replace(u"ë", u"e"
        ).replace(u"ê", u"e"
        ).replace(u"ì", u"i"
        ).replace(u"î", u"i"
        ).replace(u"í", u"i"
        ).replace(u"ï", u"i"
        ).replace(u"ò", u"o"
        ).replace(u"ô", u"o"
        ).replace(u"ó", u"o"
        ).replace(u"õ", u"o"
        ).replace(u"ö", u"o"
        ).replace(u"ù", u'u' 
        ).replace(u"û", u'u' 
        ).replace(u"ü", u"u"
        ).replace(u"°", u''
        ).replace(u"č", u"c"
        ).replace(u"ú", u"u"
        ).replace(u'È', u'E'
        ).replace(u'É', u'E'
        ).replace(u'À', u'A'
        ).replace(u'Ù', u'U'
        ).replace(u'Ò', u'O'
        ).replace(u'Ì', u'I')


def cleanWinChars(text):
    """
    Ritorna il testo con i caratteri winlatin convertiti in cose normali.
    Windows sucks.
    """
    return text.replace(u"\u201d", u'"'
        ).replace(u"\u201e", u'""'
        ).replace(u"\u201c", u'"'
        ).replace(u"\u2018", u"'"
        ).replace(u"\u2019", u"'"
        ).replace(u"\u00b4", u"'"
        ).replace(u"\u0060", u"'"
        ).replace(u"\u2013", u"-"
        ).replace(u"\u2014", u"-"
        ).replace(u"\u00ab", u'"' # in realtà sarebbe >>
        ).replace(u"\u00bb", u'"' # in realtà sarebbe <<
        ).replace(u"\u2026", u"..."
        )

class NetaddictionManifest(models.Model):
    _inherit = 'netaddiction.manifest'

    @api.one
    def create_manifest_groupon(self):

        result = self.env['ir.values'].search([('name', '=', 'contrassegno_id')])
        payment_contrassegno = False
        for r in result:
            payment_contrassegno = int(r.value)

        groupon_type = self.env.ref('netaddiction_groupon.groupon_customer_type_out').id

        if payment_contrassegno is False:
            raise ValidationError("Non sono state effettuate le configurazioni del Manifest SDA")

        name1 = datetime.datetime.now().strftime('%Y%m%d%H%M')

        file1 = StringIO.StringIO()

        for delivery in self.delivery_ids:
            if delivery.delivery_read_manifest:
                payment = delivery.sale_order_payment_method

                riga = 'CLI120522416'
                riga += ' ' * 30
                riga += 'NN'
                riga += 'S'

                riga += delivery.delivery_barcode
                count = 25 - len(delivery.delivery_barcode)

                riga += ' ' * count
                riga += datetime.date.today().strftime('%Y%m%d')
                riga += 'P'
                riga += ' ' * 6
                riga += ' ' * 14
                if delivery.picking_type_id.id == groupon_type:
                    azienda = 'Groupon c/o Fercam'
                    riga += azienda
                    count = 40 - len(azienda)
                    riga += ' ' * count
                    riga += ' ' * 20
                    riga += 'Via  '
                    via = 'Cairoli'
                    riga += via
                    count = 30 - len(via)
                    riga += ' ' * count
                    riga += '50'
                    riga += ' ' * 3
                    riga += ' ' * 15
                    cap = '27030'
                    riga += cap
                    count = 9 - len(cap)
                    riga += ' ' * count
                    citta = 'Ottobiano'
                    riga += citta
                    count = 30 - len(citta)
                    riga += ' ' * count
                    riga += 'PV'
                    riga += ' ' * 18

                    if delivery.partner_id.name:
                        company = delivery.partner_id.name[0:40]
                        company = cleanWinChars(company)
                        company = replace_vowels(company)
                    else:
                        company = ' '
                    riga += ' ' * 2
                    riga += company
                    count = 40 - len(company)
                    riga += ' ' * count

                    if delivery.partner_id.name:
                        name = delivery.partner_id.name[0:20]
                        name = cleanWinChars(name)
                        name = replace_vowels(name)
                    else:
                        name = ' '

                    riga += name
                    count = 20 - len(name)
                    riga += ' ' * count

                    if delivery.partner_id.street:
                        address = delivery.partner_id.street[0:30] + ' ' + delivery.partner_id.street2
                        address = cleanWinChars(address)
                        address = replace_vowels(address)
                    else:
                        address = ' '

                    address = address[0:40]
                    riga += address
                    count = 40 - len(address)
                    riga += ' ' * count

                    if delivery.partner_id.mobile:
                        mobile = delivery.partner_id.mobile.replace(' ', '')
                        mobile = mobile.replace('+39', '')
                        mobile = mobile[0:15]
                    else:
                        mobile = ' ' * 15

                    riga += mobile
                    count = 15 - len(mobile)
                    riga += ' ' * count

                    if delivery.partner_id.zip:
                        cap = delivery.partner_id.zip[0:9]
                        riga += cap
                    else:
                        cap = ' '

                    count = 9 - len(cap)
                    riga += ' ' * count

                    if delivery.partner_id.city:
                        citta = delivery.partner_id.city[0:30]
                        citta = cleanWinChars(citta)
                        citta = replace_vowels(citta)
                    else:
                        citta = ' '

                    riga += citta
                    count = 30 - len(citta)
                    riga += ' ' * count

                    if delivery.partner_id.state_id.code:
                        riga += str(delivery.partner_id.state_id.code)
                        count = 2 - len(str(delivery.partner_id.state_id.code))
                    else:
                        riga += ' '
                        count = 2 - len(' ')
                else:
                    azienda = 'NetAddiction srl'
                    riga += azienda
                    count = 40 - len(azienda)
                    riga += ' ' * count
                    capo = 'Riccardo Ioni'
                    riga += capo
                    count = 20 - len(capo)
                    riga += ' ' * count
                    riga += 'Via  '
                    via = 'A.M.Angelini'
                    riga += via
                    count = 30 - len(via)
                    riga += ' ' * count
                    riga += '12'
                    riga += ' ' * 3
                    tel = '07442462'
                    riga += tel
                    count = 15 - len(tel)
                    riga += ' ' * count
                    cap = '05100'
                    riga += cap
                    count = 9 - len(cap)
                    riga += ' ' * count
                    citta = "Terni"
                    riga += citta
                    count = 30 - len(citta)
                    riga += ' ' * count
                    riga += 'TR'
                    riga += ' ' * 18

                    if delivery.sale_id.partner_shipping_id.name:
                        company = delivery.sale_id.partner_shipping_id.name[0:40]
                        company = cleanWinChars(company)
                        company = replace_vowels(company)
                    else:
                        company = ' '

                    riga += ' ' * 2
                    riga += company
                    count = 40 - len(company)
                    riga += ' ' * count

                    if delivery.sale_id.partner_shipping_id.name:
                        name = delivery.sale_id.partner_shipping_id.name[0:20]
                        name = cleanWinChars(name)
                        name = replace_vowels(name)
                    else:
                        name = ' '

                    riga += name
                    count = 20 - len(name)
                    riga += ' ' * count

                    if delivery.sale_id.partner_shipping_id.street:
                        address = delivery.sale_id.partner_shipping_id.street[0:30] + ' ' + delivery.sale_id.partner_shipping_id.street2
                        address = cleanWinChars(address)
                        address = replace_vowels(address)
                    else:
                        address = ' '

                    address = address[0:40]
                    riga += address
                    count = 40 - len(address)
                    riga += ' ' * count

                    if delivery.sale_id.partner_id.mobile:
                        mobile = delivery.sale_id.partner_id.mobile.replace(' ', '')
                        mobile = mobile.replace('+39', '')
                        mobile = mobile[0:15]
                    else:
                        mobile = ' ' * 15

                    riga += mobile
                    count = 15 - len(mobile)
                    riga += ' ' * count

                    if delivery.sale_id.partner_shipping_id.zip:
                        cap = delivery.sale_id.partner_shipping_id.zip[0:9]
                        riga += cap
                    else:
                        cap = ' '

                    count = 9 - len(cap)
                    riga += ' ' * count

                    if delivery.sale_id.partner_shipping_id.city:
                        citta = delivery.sale_id.partner_shipping_id.city[0:30]
                        citta = cleanWinChars(citta)
                        citta = replace_vowels(citta)
                    else:
                        citta = ' '

                    riga += citta
                    count = 30 - len(citta)
                    riga += ' ' * count

                    if delivery.sale_id.partner_shipping_id.state_id.code:
                        riga += str(delivery.sale_id.partner_shipping_id.state_id.code)
                        count = 2 - len(str(delivery.sale_id.partner_shipping_id.state_id.code))
                    else:
                        riga += ' '
                        count = 2 - len(' ')

                riga += ' ' * count
                riga += "001"
                riga += "0001000"
                riga += '0' * 15
                riga += 'EXT'
                riga += ' ' * 40
                riga += 'EU'

                if payment:
                    if payment.id == payment_contrassegno:
                        t = str(round(delivery.total_import, 2))
                        split = t.split('.')
                        c = 2 - len(split[1])
                        total = split[0] + '.' + split[1] + '0' * c
                        total = total.zfill(9)
                        riga += total
                        riga += 'CON'
                    else:
                        riga += ' ' * 12
                else:
                    riga += ' ' * 12

                riga += ' ' * 30
                riga += "0000516.46"
                riga += delivery.delivery_barcode
                count = 25 - len(delivery.delivery_barcode)
                riga += ' ' * count
                riga += 'TR'
                riga += 'Varie'
                count = 30 - len('Varie')
                riga += ' ' * count
                riga += 'P'
                riga += ' ' * 3
                riga += ' ' * 3
                riga += ' ' * 10
                riga += 'MGCS'
                riga += ' ' * 5
                riga += ' '
                riga += '03'
                riga += ' ' * 20
                riga += '\r\n'
                file1.write(riga)

        self.manifest_file1 = base64.b64encode(file1.getvalue().encode("utf8"))
        self.manifest_file2 = None
        file1.close()
