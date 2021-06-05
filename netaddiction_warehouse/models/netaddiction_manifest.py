import datetime
import base64
import io

from ftplib import FTP

from odoo import fields, models
from odoo.exceptions import ValidationError

SPECIAL_CHARS = {
    # GRAVE
    'À': 'A',
    'È': 'E',
    'Ì': 'I',
    'Ò': 'O',
    'Ù': 'U',
    'à': 'a',
    'è': 'e',
    'ì': 'i',
    'ò': 'o',
    'ù': 'u',
    # ACUTE
    'Á': 'A',
    'É': 'E',
    'Í': 'I',
    'Ó': 'O',
    'Ú': 'U',
    'Ý': 'Y',
    'á': 'a',
    'é': 'e',
    'í': 'i',
    'ó': 'o',
    'ú': 'u',
    'ý': 'y',
    # CIRCUMFLEX
    'Â': 'A',
    'Ê': 'E',
    'Î': 'I',
    'Ô': 'O',
    'Û': 'U',
    'â': 'a',
    'ê': 'e',
    'î': 'i',
    'ô': 'o',
    'û': 'u',
    # TILDE
    'Ã': 'A',
    'Ñ': 'N',
    'Õ': 'O',
    'ã': 'a',
    'ñ': 'n',
    'õ': 'o',
    # UMLAUT
    'Ä': 'AE',
    'Ë': 'E',
    'Ï': 'I',
    'Ö': 'OE',
    'Ü': 'UE',
    'Ÿ': 'Y',
    'ä': 'ae',
    'ë': 'e',
    'ï': 'i',
    'ö': 'oe',
    'ü': 'ue',
    'ÿ': 'y',
    # OTHER FOREIGN CHARACTERS,
    '¡': '!',
    '¿': '?',
    'Ç': 'c',
    'ç': 'c',
    'Œ': 'OE',
    'œ': 'oe',
    'ß': 'ss',
    'Ø': 'O',
    'ø': 'o',
    'Å': 'A',
    'å': 'a',
    'Æ': 'AE',
    'æ': 'ae',
    'Þ': '',
    'þ': '',
    'Ð': '',
    'ð': '',
    '«': '',
    '»': '',
    '‹': '',
    '›': '',
    'Š': 'S',
    'š': 's',
    'Ž': 'Z',
    'ž': 'z',
    # CURRENCY SYMBOLS
    '¢': '',
    '£': '',
    '€': '',
    '¥': '',
    'ƒ': '',
    '¤': '',
    '°': '',
}


def replace_vowels(text):
    """
    Sostituisce le vocali accentate con le corrispondenti non accentate
    """
    return "".join([SPECIAL_CHARS.get(c) or c for c in text])


WIN_CHARS = {
    "\u00ab": '"',  # in realtà sarebbe >>
    "\u00bb": '"',  # in realtà sarebbe <<
    "\u00b4": '\'',
    "\u0060": '\'',
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '""',
    "\u2013": '-',
    "\u2014": '-',
    "\u2018": '\'',
    "\u2019": '\'',
    "\u2026": '...',
}


def clean_win_chars(text):
    """
    Ritorna il testo con i caratteri winlatin convertiti in cose normali.
    Windows sucks.
    """
    for k, v in WIN_CHARS.items():
        text = text.replace(k, v)
    return text


class NetaddictionManifest(models.Model):
    _name = 'netaddiction.manifest'
    _description = "Netaddiction Manifest"
    _order = 'date desc'
    _rec_name = 'date'

    carrier_id = fields.Many2one(
        'delivery.carrier',
        string="Corriere",
    )

    date = fields.Date(
        string="Data Manifest"
    )

    date_sent = fields.Datetime(
        string="Data spedizione"
    )

    delivery_ids = fields.One2many(
        'stock.picking',
        'manifest',
        string="Spedizioni",
    )

    manifest_file1 = fields.Binary(
        attachment=True,
        string="File1",
    )

    manifest_file2 = fields.Binary(
        attachment=True,
        string="File2",
    )

    def send_manifest(self):
        self.ensure_one()
        brt = self.env.ref('netaddiction_warehouse.carrier_brt')

        params = self.env['ir.config_parameter'].sudo()
        prefix1 = params.get_param('bartolini_prefix_file1')
        prefix2 = params.get_param('bartolini_prefix_file2')

        if brt == self.carrier_id:
            if not self.manifest_file1 or not self.manifest_file2:
                raise ValidationError("Non hai ancora creato il manifest")
            try:
                now = datetime.datetime.now()
                ftp = FTP('ftp.brt.it')
                ftp.login('0270443', 'neta1533')
                ftp.cwd('IN')
                name = now.strftime("%Y%m%d")
                name1 = '%s%s.txt' % (prefix1, name)
                name2 = '%s%s.txt' % (prefix2, name)

                bio1 = io.BytesIO(base64.b64decode(self.manifest_file1))
                ftp.storbinary('STOR %s' % name1, bio1)
                sem1 = io.BytesIO(b'')
                sem_name1 = '%s%s.chk' % (prefix1, name)
                ftp.storbinary('STOR %s' % sem_name1, sem1)

                bio2 = io.BytesIO(base64.b64decode(self.manifest_file2))
                ftp.storbinary('STOR %s' % name2, bio2)
                sem2 = io.BytesIO(b'')
                sem_name2 = '%s%s.chk' % (prefix2, name)
                ftp.storbinary('STOR %s' % sem_name2, sem2)
                self.date_sent = now

            except Exception as e:
                raise ValidationError(str(e))

        else:
            if self.manifest_file1 is False:
                raise ValidationError("Non hai ancora creato il manifest")
            try:
                now = datetime.datetime.now()
                ftp = FTP('ftp.sda.it')
                ftp.login('cli_c54566', 'inet54566')
                ftp.cwd('recv')
                bio = io.BytesIO(base64.b64decode(self.manifest_file1))
                name = now.strftime("%Y%m%d%H%M")
                ftp.storbinary('STOR %s.clidati.dat' % name, bio)
                semaforo = io.BytesIO(b'')
                ftp.storbinary('STOR %s.clidati.dis' % name, semaforo)
                self.date_sent = now
            except Exception as e:
                raise ValidationError(str(e))

    def create_manifest(self):
        self.ensure_one()
        brt = self.env.ref('netaddiction_warehouse.carrier_brt').id
        if brt == self.carrier_id.id:
            self.create_manifest_bartolini()
        else:
            self.create_manifest_sda()

    def create_manifest_sda(self):
        self.ensure_one()

        params = self.env['ir.config_parameter'].sudo()
        payment_contrassegno = int(params.get_param('contrassegno_id') or 0)

        if not payment_contrassegno:
            raise ValidationError(
                "Non sono state effettuate le configurazioni del Manifest SDA"
            )

        file1 = io.StringIO()

        for delivery in self.delivery_ids:
            if delivery.delivery_read_manifest:
                nation = delivery.sale_id.partner_shipping_id.country_id.code

                payment = delivery.sale_order_payment_method

                riga = 'CLI120522416'  # CODICE IDENTIFICATIVO
                riga += ' ' * 30
                riga += 'NN'
                riga += 'S'  # stampa ldv

                riga += delivery.delivery_barcode  # numero spedizione
                count = 25 - len(delivery.delivery_barcode)

                riga += ' ' * count
                riga += datetime.date.today().strftime('%Y%m%d')
                riga += 'P'

                # ESTERO CODICE MITTENTE CAMPO 9
                if nation in ['IT', 'SM']:
                    riga += 'NETA30'
                else:
                    riga += '      '
                # FINE ESTERO                

                riga += ' ' * 14
                azienda = 'NetAddiction srl'
                riga += azienda
                count = 40 - len(azienda)
                riga += ' ' * count
                capo = 'Andrea Alunni'
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
                    company = delivery.sale_id.partner_shipping_id.name[:40]
                    company = clean_win_chars(company)
                    company = replace_vowels(company)
                else:
                    company = ' '

                riga += ' ' * 2
                riga += company
                count = 40 - len(company)
                riga += ' ' * count

                if delivery.sale_id.partner_shipping_id.name:
                    name = delivery.sale_id.partner_shipping_id.name[:20]
                    name = clean_win_chars(name)
                    name = replace_vowels(name)
                else:
                    name = ' '

                riga += name
                count = 20 - len(name)
                riga += ' ' * count

                if delivery.sale_id.partner_shipping_id.street:
                    address = delivery.sale_id.partner_shipping_id.street[:30]\
                        + ' ' + delivery.sale_id.partner_shipping_id.street2
                    address = clean_win_chars(address)
                    address = replace_vowels(address)
                else:
                    address = ' '

                address = address[:40]
                riga += address
                count = 40 - len(address)
                riga += ' ' * count

                if delivery.sale_id.partner_id.mobile \
                        or delivery.sale_id.partner_id.phone:
                    mobile = delivery.sale_id.partner_id.mobile
                    if not mobile:
                        mobile = delivery.sale_id.partner_id.phone
                    mobile = mobile.replace(' ', '')
                    mobile = mobile.replace('+39', '')
                    mobile = mobile[:15]
                else:
                    # ESTERO TEELFONO
                    if nation in ['IT', 'SM']:
                        mobile = ' ' * 15
                    else:
                        mobile = '1' * 15
                    # FINE ESTERO

                riga += mobile
                count = 15 - len(mobile)
                riga += ' ' * count

                if delivery.sale_id.partner_shipping_id.zip:
                    cap = delivery.sale_id.partner_shipping_id.zip[:9]
                    riga += cap
                else:
                    cap = ' '

                count = 9 - len(cap)
                riga += ' ' * count

                if delivery.sale_id.partner_shipping_id.city:
                    citta = delivery.sale_id.partner_shipping_id.city[:30]
                    citta = clean_win_chars(citta)
                    citta = replace_vowels(citta)
                else:
                    citta = ' '

                riga += citta
                count = 30 - len(citta)
                riga += ' ' * count

                if delivery.sale_id.partner_shipping_id.state_id.code:
                    riga += str(
                        delivery.sale_id.partner_shipping_id.state_id.code)
                    count = 2 - len(str(
                        delivery.sale_id.partner_shipping_id.state_id.code))
                else:
                    riga += ' '
                    count = 2 - len(' ')

                riga += ' ' * count
                riga += "001"
                riga += "0001000"
                riga += '0' * 15

                # ESTERO CODICE SERVIZIO CAMPO 34
                if nation in ['IT', 'SM']:
                    riga += 'EXT'
                else:
                    riga += 'EUD'
                # FINE ESTERO

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
                riga += delivery.delivery_barcode  # numero spedizione
                count = 25 - len(delivery.delivery_barcode)
                riga += ' ' * count
                riga += 'TR'

                # ESTERO CONTENUTO CAMPO 44
                if nation in ['IT', 'SM']:
                    riga += 'Varie'
                    count = 30 - len('Varie')
                else:
                    riga += 'Videogames action figures'
                    count = 30 - len('Videogames action figures')
                # FINE ESTERO

                riga += ' ' * count
                riga += 'P'

                # ESTERO NAZIONE MITTENTE CAMPO 46
                if nation in ['IT', 'SM']:
                    riga += ' ' * 3
                else:
                    riga += 'IT '
                # FINE ESTERO

                # ESTERO NAZIONE DESTINATARIO
                if nation in ['IT', 'SM']:
                    riga += ' ' * 3
                else:
                    riga += nation + ' '
                # FINE ESTERO

                riga += ' ' * 10
                riga += 'MGCS'
                riga += ' ' * 5
                riga += ' '
                riga += '03'
                riga += ' ' * 20

                riga += ' ' * 3

                # ESTERO EMAIL CLIENTE
                if delivery.sale_id.partner_id.email:
                    email_customer = delivery.sale_id.partner_id.email[:50]
                else:
                    email_customer = 'example_ex@exampleit.ad'

                riga += email_customer
                count = 50 - len(email_customer)
                riga += ' ' * count

                # ESTERO NUMERO TELEFONO CLIENTE
                mobile = ''
                if delivery.sale_id.partner_id.mobile \
                        or delivery.sale_id.partner_id.phone:
                    mobile = delivery.sale_id.partner_id.mobile
                    if not mobile:
                        mobile = delivery.sale_id.partner_id.phone
                    mobile = mobile.replace(' ', '')
                    mobile = mobile.replace('+39', '')
                    mobile = mobile[:14]
                    mobile = mobile.replace('+', '').zfill(14)
                riga += mobile
                count = 14 - len(mobile)
                riga += ' ' * count
                riga += ' ' * 4
                if nation in ['IT', 'SM']:
                    riga += ' ' * 2
                else:
                    riga += 'C '
                riga += ' ' * 79

                riga += '\r\n'
                file1.write(riga)

        self.manifest_file1 = base64.b64encode(file1.getvalue().encode("utf8"))
        self.manifest_file2 = None

        file1.close()

    def create_manifest_bartolini(self):
        self.ensure_one()

        # RECUPERO I SETTINGS
        params = self.env['ir.config_parameter'].sudo()
        prefix1 = params.get_param('bartolini_prefix_file1')
        prefix2 = params.get_param('bartolini_prefix_file2')
        payment_contrassegno = int(params.get_param('contrassegno_id') or 0)

        if not (prefix1 and prefix2 and payment_contrassegno > 0):
            raise ValidationError(
                "Non sono state effettuate le configurazioni del"
                " Manifest Bartolini"
            )

        # CREO I FILES
        file1 = io.StringIO()

        for delivery in self.delivery_ids:
            if delivery.delivery_read_manifest:
                payment = delivery.sale_order_payment_method

                file1.write("  ")  # flag annullamento
                file1.write("0270443 ")  # nostro codice
                file1.write("026 ")  # Punto operativo di partenza
                file1.write(str(self.date.year))  # anno
                file1.write(" ")  # spazi
                # correzione brt
                file1.write(self.date.strftime("%m%d"))  # mesegiorno

                file1.write(" ")  # spazi
                file1.write("00")  # numero serie
                file1.write(" ")  # spazi
                # id spedizione univoco
                file1.write(delivery.delivery_barcode[-7:])

                if payment:
                    if payment.id == payment_contrassegno:
                        file1.write("4 ")  # se contrassegno
                    else:
                        file1.write("1 ")  # tutti gli altri pagamenti
                else:
                    file1.write("1 ")

                file1.write(" 000")

                name = ''
                if delivery.sale_id.partner_shipping_id.name:
                    name = delivery.sale_id.partner_shipping_id.name
                if delivery.sale_id.partner_shipping_id.company_address:
                    name += delivery.sale_id.partner_shipping_id\
                        .company_address
                name = clean_win_chars(name)
                name = replace_vowels(name)

                file1.write(name[:69])  # prima parte destinatario

                count = 70 - len(name)
                spaces = ' ' * count
                file1.write(spaces)  # seconda parte destinatario

                if delivery.sale_id.partner_shipping_id.street:
                    address = delivery.sale_id.partner_shipping_id.street[:30]\
                        + ' ' + delivery.sale_id.partner_shipping_id.street2
                    address = clean_win_chars(address)
                    address = replace_vowels(address)
                    address = address[:35]
                else:
                    address = ' '

                file1.write(address)  # indirizzo
                count = 35 - len(address)
                spaces = ' ' * count
                file1.write(spaces)  # indirizzo

                if delivery.sale_id.partner_shipping_id.zip:
                    cap = delivery.sale_id.partner_shipping_id.zip[:9]
                else:
                    cap = ' '

                file1.write(cap)  # CAP
                count = 9 - len(cap)
                spaces = ' ' * count
                file1.write(spaces)  # CAP

                if delivery.sale_id.partner_shipping_id.city:
                    citta = delivery.sale_id.partner_shipping_id.city[:35]
                    citta = clean_win_chars(citta)
                    citta = replace_vowels(citta)
                else:
                    citta = ' '

                file1.write(citta)  # citta
                count = 35 - len(citta)
                spaces = ' ' * count
                file1.write(spaces)  # citta

                if delivery.sale_id.partner_shipping_id.state_id.code:
                    provincia = delivery.sale_id.partner_shipping_id\
                        .state_id.code
                else:
                    provincia = 'XX'

                file1.write(provincia)  # provincia

                file1.write("   ")  # italia
                file1.write("  ")  # primo giorno di chiusura
                file1.write("  ")  # secondo giorno di chiusura
                file1.write(" 300")  # codice tariffa
                file1.write("C")  # tipo servizio bolle

                file1.write(" 0000000000,000")  # importo da assicurare
                file1.write("EUR")  # currency
                file1.write("Videogiochi    ")  # tipo merce
                file1.write(" 00001")  # numero colli
                file1.write(" ")

                weight = '1,0'
                count = 8 - len(weight)
                zeros = '0' * count
                file1.write(zeros)
                file1.write(weight)  # peso
                file1.write(" 00,000")  # volume
                file1.write(" 0000000000,000")  # quantità da fatturare

                if payment:
                    if payment.id == payment_contrassegno:
                        file1.write(" ")
                        t = str(round(delivery.total_import, 2))
                        split = t.split('.')
                        c = 3 - len(split[1])

                        total = split[0] + ',' + split[1] + '0' * c
                        count = 14 - len(total)
                        zeros = '0' * count
                        file1.write(zeros)
                        file1.write(total)  # importo contrassegno
                        file1.write("  ")  # tipo incasso contrassegno
                        file1.write("EUR")  # currency
                    else:
                        file1.write(" 0000000000,000")  # importo
                        file1.write("  ")  # tipo incasso contrassegno
                        file1.write("   ")  # divisa contrassegno
                else:
                    file1.write(" 0000000000,000")  # importo
                    file1.write("  ")  # tipo incasso contrassegno
                    file1.write("   ")  # divisa contrassegno

                file1.write("   ")
                file1.write(str(delivery.sale_id.id).zfill(15))  # idordine
                file1.write("               ")  # rferimento alfanumerico
                file1.write(" 0000000")  # dal numero
                file1.write(" 0000000")  # al numero
                file1.write(" ")  # blank fisso

                file1.write(" " * 35)  # note???
                file1.write(" " * 35)  # note2???
                file1.write(" 00")  # zona di consegna
                file1.write("7Q")  # cod.trattamento merce
                file1.write(" ")  # ritiro c/deposito
                file1.write(" 00000000")  # fata consegna richiesta
                file1.write(" ")  # tipo consegna richiesta
                file1.write(" 0000")  # ora richiesta
                file1.write("  ")  # tipo tassazione
                file1.write(" ")  # flag tariffa
                file1.write(" 0000000000,000")  # valore dichiarato
                file1.write("EUR")  # currency
                file1.write("  ")  # particolarità di consegna
                file1.write("  ")  # particolarità di giacenza
                file1.write("  ")  # particolarità varie
                file1.write(" ")  # 1a consegna particolare
                file1.write(" ")  # 2a consegna particolare
                file1.write(" ")  # codice sociale
                file1.write(" 000000000")  # tipo bancali
                file1.write("                         ")  # mittente
                file1.write("         ")  # cap
                file1.write("   ")  # nazione
                file1.write("\n")

        self.manifest_file1 = base64.b64encode(file1.getvalue().encode("utf8"))
        file1.close()

        file2 = io.StringIO()

        for delivery in self.delivery_ids:
            if delivery.delivery_read_manifest:
                # secondo file
                file2.write("  ")  # flag annullamento
                file2.write("0270443 ")  # nostro codice
                file2.write("026 ")  # punto operativo di partenza
                file2.write(str(self.date.year))  # anno
                file2.write(" ")  # spazi

                file2.write("00")  # numero serie
                file2.write(" ")  # spazi
                # id spedizione univoco
                file2.write(delivery.delivery_barcode[-7:])

                file2.write("E")  # tipo record testa
                file2.write(delivery.delivery_barcode)
                file2.write("\n")

                file2.write("  ")
                file2.write("0270443 ")  # nostro codice
                file2.write("026 ")  # punto partenza
                file2.write(str(self.date.year))  # anno
                file2.write(" ")  # spazi

                # file2.write(" ") #spazi
                file2.write("00")  # numero serie
                file2.write(" ")  # spazi
                # id spedizione univoco
                file2.write(delivery.delivery_barcode[-7:])

                file2.write("B")  # tipo record test
                if delivery.partner_id.mobile:
                    tel = delivery.partner_id.mobile[:35]
                else:
                    tel = " " * 35
                count = 35 - len(tel)
                file2.write(tel)
                file2.write(" " * count)
                file2.write("\n")

                file2.write("  ")
                file2.write("0270443 ")  # nostro codice
                file2.write("026 ")  # punto partenza
                file2.write(str(self.date.year))  # anno
                file2.write(" ")  # spazi

                file2.write("00")  # numero serie
                file2.write(" ")  # spazi
                file2.write(
                    delivery.delivery_barcode[-7:])  # id spedizione univoco

                file2.write("I")  # tipo record test
                email = delivery.partner_id.email[
                        0:35] if delivery.partner_id.email else ''
                file2.write(email)
                file2.write(" ")
                file2.write("\n")

        self.manifest_file2 = base64.b64encode(file2.getvalue().encode("utf8"))
        file2.close()
