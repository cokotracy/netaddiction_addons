# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import models, fields, api
from collections import defaultdict
import math
import re
import lmslib
import uuid
import time
import random
import traceback
import logging
from ebaysdk.exception import ConnectionError
from ebaysdk.trading import Connection as Trading
from ebay_xml_builder import SITEID

MAX_NUM_JOB_CHECK = 100

_logger = logging.getLogger(__name__)

CONTEXT = {u'lang': u'it_IT', u'tz': u'Europe/Rome', u'uid': 1}


class EbayProducts(models.Model):
    _inherit = 'product.product'

    on_ebay = fields.Boolean(string="Acceso su ebay", default=False)
    # ebay_id = '' --> convenzione per 'non hostato su ebay' 
    ebay_id = fields.Char(string="ID eBay corrente", default='')
    ebay_price = fields.Float(string="Modifica manuale prezzo eBay", default=0.0)
    set_ebay_price = fields.Boolean(string="Imponi prezzo su ebay", default=False)
    ebay_published_date = fields.Datetime(string="Data pubblicazione eBay")
    ebay_expiration_date = fields.Datetime(string="Data scadenza inserzione")
    ebay_image_expiration_date = fields.Datetime(string="Data scadenza immagine eBay")
    ebay_selled = fields.Integer(string="Venduti su eBay", default=0)
    ebay_image_url = fields.Char(string="Immagini eBay")

    @api.one
    def toggle_ebay(self):
        self.on_ebay = not self.on_ebay
        if self.on_ebay:
            self.ebay_price = self.compute_ebay_price()

    def compute_ebay_price(self):
        """ calcola il prezzo per ebay"""

        if self.set_ebay_price and self.ebay_price > 0.0:
            return self.ebay_price

        curr_price = self.offer_price if self.offer_price > 0.0 else self.list_price

        # gadget_category = self.env["product.category"].search([("name", "=", "Gadget")])
        # if gadget_category and self.categ_id.id != gadget_category.id:
        #     curr_price += (curr_price / 100.0) * 10.0

        decimal, curr_price = math.modf(curr_price)
        curr_price += 0.9

        return curr_price

    def _ebay_ean(self):
        """calcola l'EAN per ebay"""
        ret = re.sub("[^0-9]", "", self.barcode)
        if len(ret) < 13:
            ret = ("0" * (13 - len(ret))) + ret
        return ret

    def _create_upload_job(self, environment, uu_id, jobtype):
        """Crea un job su ebay di tipo jobtype
        """
        # create a new job
        create_job = lmslib.CreateUploadJob(environment)

        create_job.buildRequest(jobtype, 'gzip', uu_id)
        # can save response to file if desired
        response = create_job.sendRequest()
        response, resp_struct = create_job.getResponse()

        if response == 'Success':
            return resp_struct
        else:
            self._send_ebay_error_mail('createUploadJob Error[%s]: %s  %s' % (resp_struct.get('errorId', None), resp_struct.get('message', None), resp_struct), '[EBAY] ERRORE Upload Job')
            # sys.exit()
            return False

    def _upload_file_to_ebay_and_start_job(self, environment, uu_id, xml_to_upload, job_id, file_id):
        """invia a ebay il file xml_to_upload e lo associa al job con id = job_id, poi lo fa partire
        """
        upload_job = lmslib.UploadFile(environment)
        upload_job.buildRequest(job_id, file_id, xml_to_upload)

        response = upload_job.sendRequest()

        response, response_struct = upload_job.getResponse()

        if response == 'Success':
            pass
            # print "uploadFile Success!"
            # pprint.pprint(response_struct)
            # print '\n'
        else:
            self._send_ebay_error_mail('uploadFile Error Error[%s]: %s  %s' % (response_struct.get('errorId', None), response_struct.get('message', None), response_struct), '[EBAY] ERRORE Upload File')
            return False

        time.sleep(10)

        #####################################
        # Start processing the file
        #####################################

        start_job = lmslib.StartUploadJob(environment)
        start_job.buildRequest(job_id)

        response = start_job.sendRequest()
        response, response_struct = start_job.getResponse()

        if response == 'Success':
            # print "startUploadJob Success!"
            # pprint.pprint(response_struct)
            # print '\n'
            return response_struct
        else:
            self._send_ebay_error_mail('startUploadJob Error Error[%s]: %s  %s' % (response_struct.get('errorId', None), response_struct.get('message', None), response_struct), '[EBAY] ERRORE Start Upload Job')
            return False

    def _check_job_status(self, environment, job_id):
        # print '*' * 50
        # print "Checking Job Status\n"
        job_status = lmslib.GetJobStatus(environment)
        job_status.buildRequest(job_id)
        # Keep checking on status until completed
        ret_value = False
        attempt = 0
        max_num_job_check = self.env["ir.values"].search([("name", "=", "max_num_retry"), ("model", "=", "netaddiction.ebay.config")]).value
        max_num_job_check = max_num_job_check if max_num_job_check > 0 else MAX_NUM_JOB_CHECK
        while attempt < max_num_job_check:
            response = job_status.sendRequest()
            response, resp_struct = job_status.getResponse()
            if response == 'Success':
                if resp_struct[0].get('jobStatus', None) == 'Completed':
                    # print "Job Finished! Woo hoo!"
                    # print resp_struct[0]
                    # print '\n'
                    ret_value = True
                    break
                elif resp_struct[0].get('jobStatus', None) == 'Failed':
                    # print "JOB FAILED"
                    # print "Job is %s complete, trying again in 10 seconds" % resp_struct[0].get('percentComplete', None)
                    # print resp_struct
                    break
                else:
                    pass
                    # print "Job is %s complete, trying again in 10 seconds" % resp_struct[0].get('percentComplete', None)
                    # print resp_struct
                    # print '\n'
            # Check again in 10 seconds
            attempt += 1
            time.sleep(10)
        # print '*' * 50
        # print '\n'
        return (ret_value, resp_struct)

    def _upload_images_to_ebay(self, environment, uu_id, xml_builder, products_id):
        """Carica le immagini dei prodotti in products_id su eBay. Ritorna associazione id_prodotto:link immagine su ebay."""
        resp_struct = self._create_upload_job(environment, uu_id, 'UploadSiteHostedPictures')

        if not resp_struct:
            # ERRORE
            return

        # The job_id used throughout the process
        job_id = resp_struct.get('jobId', None)
        # The fileId for the file to be uploaded
        file_id = resp_struct.get('fileReferenceId', None)

        if not job_id or not file_id:
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE Upload Images')
            return False

        try:
            xml_images = xml_builder.build_image_upload(products_id)
        except:
            raise Exception("prodotto immagini %s" % products_id)

        resp_struct = self._upload_file_to_ebay_and_start_job(environment, uu_id, xml_images, job_id, file_id)

        if not resp_struct:
            return

        ######################################
        # Get Job status
        ######################################
        res, resp_struct = self._check_job_status(environment, job_id)
        if not res:
            self._send_ebay_error_mail("_check_job_status ha ritornato None", '[EBAY] ERRORE Upload Images')
            return
        download_file_id = resp_struct[0].get('fileReferenceId', None)

        ###########################################
        # downloadFile --The responses
        ###########################################
        # print '*' * 50
        # print "Downloading Responses\n"

        download_file = lmslib.DownloadFile(environment)
        download_file.buildRequest(job_id, download_file_id)

        response = download_file.sendRequest()

        xml = download_file.getResponse()

        if xml:
            pass
            # print "Successfully downloaded response!"
            # print xml
            # print '\n'
        else:
            self._send_ebay_error_mail("Failure! downloadFile failed ", '[EBAY] ERRORE Upload Images')

        return xml

    def _search_and_remove_ebay_jobs(self, environment, job_types, job_statuses):
        get_jobs = lmslib.GetJobs(environment)
        get_jobs.buildRequest(jobtype_list=job_types, jobstatus_list=job_statuses)
        get_jobs.sendRequest()
        response, resp_struct = get_jobs.getResponse()
        # self._send_ebay_error_mail("%s /n %s" % (response, pprint.pformat(resp_struct)), '[EBAY] Debug GetJobs')
        # print response
        # pprint.pprint(resp_struct)

        if response == 'Success':
            abort_job = lmslib.AbortJob(environment)
            for job in resp_struct:
                abort_job.buildRequest(job['jobId'])
                abort_job.sendRequest()
                response, resp_struct = abort_job.getResponse()
                # self._send_ebay_error_mail("%s /n %s" % (response, pprint.pformat(resp_struct)), '[EBAY] Debug Abort Job')

    def _revise_products_on_ebay(self, environment, uu_id, xml_builder, prods):

        resp_struct = self._create_upload_job(environment, uu_id, 'ReviseFixedPriceItem')

        if not resp_struct:
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE ReviseFixedPriceItem')
            return False

        # The job_id used throughout the process
        job_id = resp_struct.get('jobId', None)
        # The fileId for the file to be uploaded
        file_id = resp_struct.get('fileReferenceId', None)

        if not job_id or not file_id:
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE ReviseFixedPriceItem')
            return False

        xml_addfixed = xml_builder.build_revise_fixed_price_items(prods)

        resp_struct = self._upload_file_to_ebay_and_start_job(environment, uu_id, xml_addfixed, job_id, file_id)

        if not resp_struct:
            return False

        ######################################
        # Get Job status
        ######################################
        res, resp_struct = self._check_job_status(environment, job_id)

        if not res:
            self._send_ebay_error_mail("_check_job_status ha tornato None", '[EBAY] ERRORE ReviseFixedPriceItem')
            return
        download_file_id = resp_struct[0].get('fileReferenceId', None)

        ###########################################
        # downloadFile --The responses
        ###########################################
        # print '*' * 50
        # print "Downloading Responses\n"

        download_file = lmslib.DownloadFile(environment)
        download_file.buildRequest(job_id, download_file_id)

        response = download_file.sendRequest()

        xml = download_file.getResponse()

        if xml:
            pass
            # print "Successfully downloaded response!"
            # print xml
            # print '\n'
        else:
            self._send_ebay_error_mail("Failure! downloadFile failed ", '[EBAY] ERRORE Revise Products')
            # print "Failure! downloadFile failed"
            # print xml

        return xml

    def _relist_fixed_price_items_on_ebay(self, environment, uu_id, xml_builder, prods):

        resp_struct = self._create_upload_job(environment, uu_id, 'RelistFixedPriceItem')

        if not resp_struct:
            # ERRORE
            self._send_ebay_error_mail("_check_job_status ha tornato None", '[EBAY] ERRORE RelistFixedPriceItem')
            return False

        # The job_id used throughout the process
        job_id = resp_struct.get('jobId', None)
        # The fileId for the file to be uploaded
        file_id = resp_struct.get('fileReferenceId', None)

        if not job_id or not file_id:
            # print "createUploadJob Error: couldn't obtain jobId or fileReferenceId"
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE RelistFixedPriceItem')
            return False

        xml_addfixed = xml_builder.build_relist_fixed_price_items(prods)

        resp_struct = self._upload_file_to_ebay_and_start_job(environment, uu_id, xml_addfixed, job_id, file_id)

        if not resp_struct:
            return False

        ######################################
        # Get Job status
        ######################################
        res, resp_struct = self._check_job_status(environment, job_id)
        if not res:
            self._send_ebay_error_mail("Failure! _check_job_status failed ", '[EBAY] ERRORE Relist Products')
            return
        download_file_id = resp_struct[0].get('fileReferenceId', None)

        ###########################################
        # downloadFile --The responses
        ###########################################
        # print '*' * 50
        # print "Downloading Responses\n"

        download_file = lmslib.DownloadFile(environment)
        download_file.buildRequest(job_id, download_file_id)

        response = download_file.sendRequest()

        xml = download_file.getResponse()

        if xml:
            pass
            # print "Successfully downloaded response!"
            # print xml
            # print '\n'
        else:
            self._send_ebay_error_mail("Failure! downloadFile failed ", '[EBAY] ERRORE Relist Products')
            # print "Failure! downloadFile failed"
            # print xml

        return xml

    def _end_fixed_price_items_on_ebay(self, environment, uu_id, xml_builder, prods):

        resp_struct = self._create_upload_job(environment, uu_id, 'EndFixedPriceItem')

        if not resp_struct:
            # ERRORE
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE EndFixedPriceItem')
            return False

        # The job_id used throughout the process
        job_id = resp_struct.get('jobId', None)
        # The fileId for the file to be uploaded
        file_id = resp_struct.get('fileReferenceId', None)

        if not job_id or not file_id:
            # print "createUploadJob Error: couldn't obtain jobId or fileReferenceId"
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE EndFixedPriceItem')
            return False

        xml_endfixed = xml_builder.build_end_fixed_price_items(prods)

        resp_struct = self._upload_file_to_ebay_and_start_job(environment, uu_id, xml_endfixed, job_id, file_id)

        if not resp_struct:
            return False

        ######################################
        # Get Job status
        ######################################
        res, resp_struct = self._check_job_status(environment, job_id)
        if not res:
            self._send_ebay_error_mail("Failure! _check_job_status failed ", '[EBAY] ERRORE End Products')
            return False
        download_file_id = resp_struct[0].get('fileReferenceId', None)

        ###########################################
        # downloadFile --The responses
        ###########################################
        # print '*' * 50
        # print "Downloading Responses\n"

        download_file = lmslib.DownloadFile(environment)
        download_file.buildRequest(job_id, download_file_id)

        response = download_file.sendRequest()

        xml = download_file.getResponse()

        if xml:
            pass
            # print "Successfully downloaded response!"
            # print xml
            # print '\n'
        else:
            self._send_ebay_error_mail("Failure! downloadFile failed ", '[EBAY] ERRORE End Products')
            # print "Failure! downloadFile failed"
            # print xml

        return xml

    def _add_fixed_price_items_to_ebay(self, environment, uu_id, xml_builder, prods, contrassegno):

        resp_struct = self._create_upload_job(environment, uu_id, 'AddFixedPriceItem')

        if not resp_struct:
            # ERRORE
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE AddFixedPriceItem')
            return

        # The job_id used throughout the process
        job_id = resp_struct.get('jobId', None)
        # The fileId for the file to be uploaded
        file_id = resp_struct.get('fileReferenceId', None)

        if not job_id or not file_id:
            # print "createUploadJob Error: couldn't obtain jobId or fileReferenceId"
            self._send_ebay_error_mail("createUploadJob Error: couldn't obtain jobId or fileReferenceId", '[EBAY] ERRORE AddFixedPriceItem')
            return False

        paypal_account = self.env["ir.values"].search([("name", "=", "paypal_account"), ("model", "=", "netaddiction.ebay.config")]).value

        xml_addfixed = xml_builder.build_add_fixed_price_items(prods, paypal_account, str(contrassegno.lst_price))

        self._send_ebay_error_mail(" %s " % xml_addfixed, '[EBAY] debug AddFixedPriceItem')

        resp_struct = self._upload_file_to_ebay_and_start_job(environment, uu_id, xml_addfixed, job_id, file_id)

        if not resp_struct:
            return

        ######################################
        # Get Job status
        ######################################
        res, resp_struct = self._check_job_status(environment, job_id)
        if not res:
            self._send_ebay_error_mail("Failure! _check_job_status failed ", '[EBAY] ERRORE AddFixedPriceItem')
            return False
        download_file_id = resp_struct[0].get('fileReferenceId', None)

        ###########################################
        # downloadFile --The responses
        ###########################################
        # print '*' * 50
        # print "Downloading Responses\n"

        download_file = lmslib.DownloadFile(environment)
        download_file.buildRequest(job_id, download_file_id)

        response = download_file.sendRequest()

        xml = download_file.getResponse()

        if xml:
            pass
            # print "Successfully downloaded response!"
            # print xml
            # print '\n'
        else:
            self._send_ebay_error_mail("Failure! downloadFile failed ", '[EBAY] ERRORE End Products')
            # print "Failure! downloadFile failed"
            # print xml

        return xml

    @api.model
    def _upload_new_products_to_ebay(self):
        u"""Prende i prodotti da mettere su ebay che non hanno un ebay_id, carica le loro immagini, e apre la relativa asta."""
        # ebay_id = '' convenzione per 'non hostato su ebay'
        products_to_upload = self.env["product.product"].search([("on_ebay", "=", True), ("ebay_id", "=", '')])

        if products_to_upload:
            environment = lmslib.PRODUCTION
            uu_id = uuid.uuid4()

            # SEARCH FOR ACTIVE JOB
            self._search_and_remove_ebay_jobs(environment, ["UploadSiteHostedPictures"], ["Created", "InProcess", "Scheduled"])
            # self._search_and_remove_ebay_jobs(environment, ["AddFixedPriceItem"], ["Created", "InProcess", "Scheduled", "Aborted", "Failed", "Completed"])
            prods = {}
            book_id = self.env["product.category"].search([("name", "=", "Libri e Fumetti")]).id
            # creo il dizionario products con i dati da mandare a ebay
            category_dict = self._build_category_dictionary()
            for product in products_to_upload:
                product.ebay_price = product.compute_ebay_price()
                category = category_dict.get(product.categ_id.id, '139973')
                if isinstance(category, dict):
                    category = category.get(product.attribute_value_ids[0].id, category[0]) if product.attribute_value_ids else category[0]
                isbn = product.barcode if product.categ_id.id == book_id else None
                prods[str(product.id)] = {
                    'qty': str(product.qty_available_now),
                    'name': product.with_context(CONTEXT).name[:80],
                    'ean': str(product.barcode),
                    'description': product.description,
                    'ebay_image': "TO_FILL",
                    'ebay_category': category,
                    'price': str(product.ebay_price),
                    'isbn': isbn, }

            xml_builder = self.env["netaddiction.ebay.xmlbuilder"].create({})
            # upload immagini
            xml = self._upload_images_to_ebay(environment, uu_id, xml_builder, prods.keys())
            if not xml:
                return
            # risposta da ebay
            images = xml_builder.parse_image_upload_response(xml)

            if images:
                for prod_id, data in images.iteritems():
                    if prod_id in prods:
                        prods[prod_id]["ebay_image"] = data['url']

            # upload prodotti come fixed price items
            uu_id = uuid.uuid4()
            contrassegno = self.env.ref('netaddiction_payments.product_contrassegno')
            self._search_and_remove_ebay_jobs(environment, ["AddFixedPriceItem"], ["Created", "InProcess", "Scheduled"])

            xml = self._add_fixed_price_items_to_ebay(environment, uu_id, xml_builder, prods, contrassegno)

            if not xml:
                return
            items = xml_builder.parse_addfixed_response(xml)
            duplicates = []
            if items:
                for prod_id, item in items.iteritems():
                    if prod_id in prods:
                        products_uploaded = [p for p in products_to_upload if p.id == int(prod_id)]
                        if products_uploaded:
                            product = products_uploaded[0]
                            product.ebay_id = item['id']
                            if item['duplicate']:
                                duplicates.append((product.with_context(CONTEXT).name[:80], product.id))
                            else:
                                product.ebay_published_date = datetime.strptime(item["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
                                product.ebay_expiration_date = datetime.strptime(item["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
                                product.ebay_image_url = prods[prod_id]["ebay_image"]
                                product.ebay_image_expiration_date = datetime.strptime(images[prod_id]['expire_date'], "%Y-%m-%dT%H:%M:%S.%fZ")

            problems = [p for p in products_to_upload if "%s" % p.id not in items]
            if problems:
                self._send_ebay_error_mail("Non sono riuscito ad aggiungere questi prodotti %s %s " % (problems, xml), '[EBAY] ERRORE nell upload di nuovi prodotti su ebay')
            if duplicates:
                self._send_ebay_error_mail("Duplicati nell' AddFixedPriceItem %s" % duplicates, '[EBAY] WARNING duplicati')

    @api.model
    def _update_products_on_ebay(self):
        u"""Prende i prodotti che hanno inserzioni attive su ebay e hanno subito qualche modifica (comprese quantità disponibili) e aggiorna le relative aste su ebay.

        Se sono scadute le immagini su ebay le esegue un nuovo upload.
        """
        last_executed = self.env["ir.values"].search([("name", "=", "ebay_last_update"), ("model", "=", "netaddiction.ebay.config")]).value
        last_executed = last_executed if last_executed else (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        products_on_ebay = self.env["product.product"].search([("on_ebay", "=", True), ("ebay_id", "!=", '')])
        products_on_ebay = [p.id for p in products_on_ebay]

        products_sold = self.env["sale.order.line"].search([("state", "in", ["sale", "done", "partial_done"]), ("write_date", ">=", last_executed), ("product_id", 'in', products_on_ebay), ("order_id.from_ebay", "=", False)])
        products_sold = [p.product_id for p in products_sold]

        products_modified = self.env["product.product"].search([("on_ebay", "=", True), ("ebay_id", "!=", ''), ("write_date", ">=", last_executed)])
        # elimino i duplicati e faccio il merge delle due liste
        set_product_sold = set(products_sold)
        products_to_update = list(set_product_sold) + list(set(products_modified) - set_product_sold)

        products_image_expired = self.env["product.product"].search([("on_ebay", "=", True), ("ebay_id", "!=", ''), ("ebay_image_expiration_date", "<", last_executed)])

        products_to_update = products_to_update + list(set(products_image_expired) - set(products_to_update))

        if products_to_update:

            environment = lmslib.PRODUCTION

            # SEARCH FOR ACTIVE JOB
            self._search_and_remove_ebay_jobs(environment, ["ReviseFixedPriceItem"], ["Created", "InProcess", "Scheduled"])
            prods = {}

            book_id = self.env["product.category"].search([("name", "=", "Libri e Fumetti")]).id

            # creo il dizionario products con i dati da mandare a ebay
            category_dict = self._build_category_dictionary()
            for product in products_to_update:
                if product.qty_available_now > 0:
                    product.ebay_price = product.compute_ebay_price()
                    category = category_dict.get(product.categ_id.id, '139973')
                    if isinstance(category, dict):
                        category = category.get(product.attribute_value_ids[0].id, category[0]) if product.attribute_value_ids else category[0]
                    isbn = product.barcode if product.categ_id.id == book_id else None
                    prods[str(product.id)] = {
                        'qty': str(product.qty_available_now),
                        'name': product.with_context(CONTEXT).name[:80],
                        'ean': str(product.barcode),
                        'ebay_id': product.ebay_id,
                        'description': product.description,
                        'ebay_image': product.ebay_image_url,
                        'ebay_category': category,
                        'price': str(product.ebay_price), 
                        'isbn': isbn, }
                else:
                    product.on_ebay = False

            products_reupdate_images = ["%s" % p.id for p in products_to_update if p.ebay_image_expiration_date < last_executed and p.on_ebay]

            xml_builder = self.env["netaddiction.ebay.xmlbuilder"].create({})
            images = {}
            if products_reupdate_images:
                # upload immagini
                # SEARCH FOR ACTIVE JOB
                self._search_and_remove_ebay_jobs(environment, ["UploadSiteHostedPictures"], ["Created", "InProcess", "Scheduled"])
                uu_id = uuid.uuid4()
                xml = self._upload_images_to_ebay(environment, uu_id, xml_builder, products_reupdate_images)
                if xml:
                    # risposta da ebay
                    images = xml_builder.parse_image_upload_response(xml)
                    if images:
                        for prod_id, data in images.iteritems():
                            if prod_id in prods:
                                prods[prod_id]["ebay_image"] = data['url']

            uu_id = uuid.uuid4()
            xml = self._revise_products_on_ebay(environment, uu_id, xml_builder, prods)

            self.env["ir.values"].search([("name", "=", "ebay_last_update"), ("model", "=", "netaddiction.ebay.config")]).value = datetime.now()
            if not xml:
                return

            error_products = xml_builder.parse_revisefixed_response(xml)
            if images:
                images_ids = images.keys()
                for product in products_to_update:
                    id_string = "%s" % product.id
                    if id_string not in error_products and id_string in images_ids:
                        product.ebay_image_url = prods[id_string]["ebay_image"]
                        product.ebay_image_expiration_date = datetime.strptime(images[id_string]['expire_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            if error_products:
                self._send_ebay_error_mail("errore ritornato da revise fixed price  %s %s " % (error_products, xml), '[EBAY] ERRORE errore ritornato da revise fixed price ')
                return

    @api.model
    def _relist_products_on_ebay(self):
        u"""Prende tutti i prodotti ancora da tenere su ebay la cui inserzione è scaduta e li relista su ebay."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # prodotti la cui inserzione è scaduta
        products_expired = self.env["product.product"].search([("on_ebay", "=", True), ("ebay_id", "!=", ''), ("ebay_expiration_date", "<", now)])

        if products_expired:
            # TODO CHANGE API SANDBOX api.ebay.com
            environment = lmslib.PRODUCTION

            # SEARCH FOR ACTIVE JOB
            self._search_and_remove_ebay_jobs(environment, ["RelistFixedPriceItem"], ["Created", "InProcess", "Scheduled"])
            prods = {}

            book_id = self.env["product.category"].search([("name", "=", "Libri e Fumetti")]).id
            # creo il dizionario products con i dati da mandare a ebay
            category_dict = self._build_category_dictionary()
            for product in products_expired:
                product.ebay_price = product.compute_ebay_price()
                category = category_dict.get(product.categ_id.id, '1')
                if isinstance(category, dict):
                        category = category.get(product.attribute_value_ids[0].id, category[0]) if product.attribute_value_ids else category[0]
                isbn = product.barcode if product.categ_id.id == book_id else None
                prods[str(product.id)] = {
                    'qty': str(product.qty_available_now),
                    'name': product.with_context(CONTEXT).name[:80],
                    'ean': str(product.barcode),
                    'ebay_id': product.ebay_id,
                    'description': product.description,
                    'ebay_image': product.ebay_image_url,
                    'ebay_category': category,
                    'price': str(product.ebay_price), 
                    'id': str(product.id),
                    'isbn': isbn,
                }

            products_reupdate_images = ["%s" % p.id for p in products_expired if p.ebay_image_expiration_date < now]

            xml_builder = self.env["netaddiction.ebay.xmlbuilder"].create({})

            if products_reupdate_images:
                # upload immagini
                # SEARCH FOR ACTIVE JOB
                self._search_and_remove_ebay_jobs(environment, ["UploadSiteHostedPictures"], ["Created", "InProcess", "Scheduled"])
                uu_id = uuid.uuid4()
                xml = self._upload_images_to_ebay(environment, uu_id, xml_builder, products_reupdate_images)
                if xml:
                    # risposta da ebay
                    images = xml_builder.parse_image_upload_response(xml)
                    if images:
                        for prod_id, data in images.iteritems():
                            if prod_id in prods:
                                prods[prod_id]["ebay_image"] = data['url']

            uu_id = uuid.uuid4()
            xml = self._relist_fixed_price_items_on_ebay(environment, uu_id, xml_builder, prods)
            relisted_products = xml_builder.parse_relistfixed_response(xml)

            if relisted_products:
                for prod_id, item in relisted_products.iteritems():
                    if prod_id in prods:
                        products_uploaded = [p for p in products_expired if p.id == int(prod_id)]
                        if products_uploaded:
                            product = products_uploaded[0]
                            if "start" in item and "end" in item:
                                product.ebay_published_date = datetime.strptime(item["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
                                product.ebay_expiration_date = datetime.strptime(item["end"], "%Y-%m-%dT%H:%M:%S.%fZ")

            problems = [p for p in products_expired if "%s" % p.id not in relisted_products]
            if problems:
                self._send_ebay_error_mail("Non sono riuscito ad aggiungere questi prodotti %s %s" % (problems, xml), '[EBAY] ERRORE nel relist di nuovi prodotti su ebay ')

    @api.model
    def _end_products_on_ebay(self):
        u"""Prende tutti i prodotti da non tenere più su ebay la cui inserzione  NON è scaduta e cancella l'inserzione.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        products_to_end = self.env["product.product"].search([("on_ebay", "=", False), ("ebay_id", "!=", ''), ])
        products_out_of_stock = self.env["product.product"].search([("on_ebay", "=", True), ("ebay_id", "!=", ''), ("qty_available_now", "<", 1)])
        products_dead = self.env["product.product"].search([("on_ebay", "=", False), ("ebay_id", "!=", ''), ("ebay_expiration_date", "=", False)])

        products_to_end = list(set(products_to_end + products_out_of_stock + products_dead))

        if products_to_end:

            environment = lmslib.PRODUCTION

            # SEARCH FOR ACTIVE JOB
            self._search_and_remove_ebay_jobs(environment, ["EndFixedPriceItem"], ["Created", "InProcess", "Scheduled"])
            prods = [(p.id, p.ebay_id) for p in products_to_end]

            xml_builder = self.env["netaddiction.ebay.xmlbuilder"].create({})
            uu_id = uuid.uuid4()

            xml = self._end_fixed_price_items_on_ebay(environment, uu_id, xml_builder, prods)

            if not xml:
                return False
            ended_products = xml_builder.parse_endfixed_response(xml)

            if ended_products:
                for prod_id, end_date in ended_products.iteritems():
                    product_ended = [p for p in products_to_end if p.id == int(prod_id)]
                    if product_ended:
                        product = product_ended[0]
                        product.ebay_expiration_date = datetime.strptime(end_date['end'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        product.ebay_image_expiration_date = ''
                        product.ebay_published_date = ''
                        product.ebay_id = ''

            problems = [p for p in products_to_end if "%s" % p.id not in ended_products]
            if problems:
                self._send_ebay_error_mail("Non sono riuscito a terminare questi prodotti %s %s" % (problems, xml), '[EBAY] ERRORE nel end di nuovi prodotti su ebay ')

    @api.model
    def _remove_expired_ebay_ids(self):
        u"""Prende tutti i prodotti a cui è scaduto l'ebay_id e lo resetta.
        """
        now = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")

        products = self.env["product.product"].search([("on_ebay", "=", False), ("ebay_id", "!=", ''), ("ebay_expiration_date", "<", now)])

        for product in products:
            product.ebay_id = ''

    @api.model
    def _get_ebay_orders(self):
        """Crea gli ordini provenienti da eBay
        """

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        last_executed = self.env["ir.values"].search([("name", "=", "ebay_last_order_check"), ("model", "=", "netaddiction.ebay.config")]).value
        last_executed = last_executed if last_executed else (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        error_transaction = []
        try:

            api = Trading(debug=True, config_file=None, appid="Multipla-644d-46c5-b42e-d222d91ad5c2", certid="9514cd34-39e2-45f7-9a62-9a68ff704d4b", devid="639886ba-b87c-4189-9173-0bc9d268a3ef", token="AgAAAA**AQAAAA**aAAAAA**2FApWg**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wDk4OlC5mFpAmdj6x9nY+seQ**9awAAA**AAMAAA**d63JWRuVCrO5PQy3n8nejZzsnqWUtEp072ktglLxrpkBTGiZJSJbCIk5wPuPWOs5sLcDTeWG5/ZOGqW8A5nMYCcMJeNaSW6Qu19hpY53TPRqhakOqybrmqf23i9Rzjm93LF9OhuxzACuDpSEz01OQo67XXtdn7QV/z7j8cT58lkJjsIpTg4MknCbsy1h2b9oLXM7gWyZqooCTSDiXgNq6MvOYZ9sEkCtdYJVE2F39hIzCXVr3h48pjhlEsL3tk3YDPxirF4CLJwEop7rHrTR+bT/LP9N2x2tgdo7eLQqu1sG/pCUmaL8JTxAYVGMoFguOrzWAKw2SqLYKXjvDjR8DjOP29Na43oVULhFrZUSXoIQwO257kKrPeX5yjtmR33uwYgCvqgCme/gajFfWLgUQS1/sNnEm1oZO42zGxvV5QBnkebzqob3cs5qLGr233HSlME4IZDMGH81Ikx0/1ArSHpx7fYZphocn2IUcG7rDssPmG6aY62kpwCm8jPkaQTKYl5h32M2qjaG2FBwhWGvERTjlOLLxedwRqWDpffa1M9GjeTJgUCaUh4fO8v4sh8Wde6fb1T2kki5h3EtSbv26bK5pUotDE9KK3lPWNT+L0eVAGjdKRZSwyeN9XWxjYafQGgKNI55Tl1Zg35Bo3UxchRNg5H1EVsnz7GX0Lgh0DY1xBV7N/zp0L99plM1FZWKX2quQKfmEMVeB4/QjAyIqeh+oHCG/ziJkgrcNrDLFhs6C/QWamtW0KcNt2X4iC81",
                       warnings=True, site_id=SITEID, timeout=20, domain='api.ebay.com')
        except ConnectionError as e:
            # print(e)
            # print(e.response.dict())
            self._send_ebay_error_mail("problema di connessione %s " % e, '[EBAY] ERRORE nel get order')
            return

        curr_pag = 0
        tot_pag = 1
        # controllo sugli ordini già scaricati non completati necessario perchè ebay te li rimanda
        # dopo che gli hai detto che sono stati spediti
        received_transactions = self.env["sale.order"].search([("from_ebay", "=", True), ('state', "!=", "cancel")])
        received_transactions = [order.ebay_transaction_id.split() for order in received_transactions]
        received_transactions = [item for sublist in received_transactions for item in sublist]
        _logger.warning("[EBAY] RECEIVED TRANSACTIONS %s" % received_transactions)
        while(curr_pag < tot_pag):
            curr_pag += 1
            try:
                api.execute('GetSellerTransactions', {'ModTimeFrom': last_executed, 'ModTimeTo': now, 'DetailLevel': 'ReturnAll', 'Pagination': {'EntriesPerPage': '200', 'PageNumber': '%s' % curr_pag}})
            except ConnectionError as e:
                # print(e)
                # print(e.response.dict())
                self._send_ebay_error_mail("problema di connessione, dentro al ciclo iterazione %s eccezione %s " % (curr_pag, e), '[EBAY] ERRORE nel get order')
                return

            resp = api.response.dict()
            self._send_ebay_error_mail("EBAY DEBUG %s " % resp, '[EBAY] GET TRANSACTION')

            tot_pag = int(resp["PaginationResult"]["TotalNumberOfPages"])
            tot_transaction = int(resp["ReturnedTransactionCountActual"])
            if tot_transaction < 1:
                # nessuna transazione
                continue

            elif tot_transaction == 1:
                # 1 transazione, resp["TransactionArray"]["Transaction"] c'è un dizionario che rappresenta la transazione
                transaction = resp["TransactionArray"]["Transaction"]
                if transaction['Status']['eBayPaymentStatus'] == 'NoPaymentFailure' and transaction['Status']['CheckoutStatus'] == 'CheckoutComplete' and transaction["TransactionID"] not in received_transactions:
                        ret_str = self._create_ebay_order(transaction)
                        if ret_str != "OK":
                            error_transaction.append([transaction["TransactionID"], ret_str])
            else:
                # > 1 transazione, in resp["TransactionArray"]["Transaction"] c'è una lista di transazioni
                transactions = [transaction for transaction in resp["TransactionArray"]["Transaction"]]
                groupped_transactions = defaultdict(list)

                for transaction in transactions:
                    groupped_transactions[transaction["Buyer"]["Email"]].append(transaction)

                for user, transactions in groupped_transactions.iteritems():
                    num_transactions = len(transactions)
                    _logger.warning("[EBAY] %s num %s" % (user, num_transactions))
                    # se le transazioni sono tutte pagate faccio l'ordine
                    # altrimenti se sono tutte non pagate le unisco
                    # altrimenti mail e segnalazione
                    if num_transactions == 1:
                        transaction = transactions[0]
                        _logger.warning("[EBAY] creo ordine per %s eBayPaymentStatus %s CheckoutStatus %s transaction_id %s  transazione %s" % (user, transaction['Status']['eBayPaymentStatus'], transaction['Status']['CheckoutStatus'], transaction["TransactionID"], transaction))
                        if transaction['Status']['eBayPaymentStatus'] == 'NoPaymentFailure' and transaction['Status']['CheckoutStatus'] == 'CheckoutComplete' and transaction["TransactionID"] not in received_transactions:
                            ret_str = self._create_ebay_order(transaction)
                            if ret_str != "OK":
                                error_transaction.append([transaction["TransactionID"], ret_str])
                    elif num_transactions > 1:
                        paid_number = 0
                        for transaction in transactions:
                            if transaction['Status']['eBayPaymentStatus'] == 'NoPaymentFailure' and transaction['Status']['CheckoutStatus'] == 'CheckoutComplete' and transaction["TransactionID"] not in received_transactions:
                                paid_number += 1
                        if paid_number == 0:
                            # unisci!
                            transaction_array = []
                            total = 0.0
                            for transaction in transactions:
                                transaction_array.append({'Item': {'ItemID': transaction["Item"]["ItemID"]}, 'TransactionID': transaction["TransactionID"]})
                                total += float(transaction["TransactionPrice"]['value']) * int(transaction["QuantityPurchased"])

                            total += 4.90
                            self._send_ebay_error_mail(" %s totale %s " % (transaction_array, total), '[EBAY] DEBUG nel get order')
                            try:
                                api.execute('AddOrder', {'Order': {'TransactionArray': {'Transaction': transaction_array}, 'Total': {'#text': '%s' % total, '@attrs': {'currencyID': 'EUR'}}, 'CreatingUserRole': 'Seller', 'PaymentMethods': ['PayPal', 'COD'], 'ShippingDetails': {'CODCost': '3.0', 'ShippingServiceOptions': {'ShippingService': 'Other', 'ShippingServicePriority': '1', 'ShippingServiceCost': '4.90', 'ShippingServiceAdditionalCost': '0.00', 'ShippingSurcharge': '0.00'}}}})
                                resp = api.response.dict()
                                self._send_ebay_error_mail(" %s " % resp, '[EBAY] DEBUG ADD order')

                                if resp["Ack"] != "Success" and resp["Ack"] != "Warning":
                                    self._send_ebay_error_mail(" %s " % resp, '[EBAY] ERRORE nel AddOrder')
                            except ConnectionError as e:
                                self._send_ebay_error_mail(" %s " % e, '[EBAY] ECCEZIONE nel AddOrder')
                        elif paid_number == num_transactions:
                            # fai ordine
                            ret_str = self._create_ebay_order(transactions, multi=True)
                            if ret_str != "OK":
                                for transaction in transactions:
                                    error_transaction.append([transaction["TransactionID"], ret_str])
                        else:
                            # hmmmmm... fai partire le transazioni pagate?
                            for transaction in transactions:
                                if transaction['Status']['eBayPaymentStatus'] == 'NoPaymentFailure' and transaction['Status']['CheckoutStatus'] == 'CheckoutComplete' and transaction["TransactionID"] not in received_transactions:
                                        ret_str = self._create_ebay_order(transaction)
                                        if ret_str != "OK":
                                            error_transaction.append([transaction["TransactionID"], ret_str])

        self.env["ir.values"].search([("name", "=", "ebay_last_order_check"), ("model", "=", "netaddiction.ebay.config")]).value = datetime.now()
        if error_transaction:
            self._send_ebay_error_mail("problemi con queste transazioni %s " % error_transaction, '[EBAY] ERRORE nel get order')

        return

    @api.model
    def _complete_ebay_orders(self):
        """Comunica a eBay la spedizione degli ordini
        """
        orders = self.env["sale.order"].search([('state', '=', 'done'), ('ebay_completed', '=', False), ('from_ebay', "=", True)])
        if orders:
            # print orders
            try:

                api = Trading(debug=False, config_file=None, appid="Multipla-644d-46c5-b42e-d222d91ad5c2", certid="9514cd34-39e2-45f7-9a62-9a68ff704d4b", devid="639886ba-b87c-4189-9173-0bc9d268a3ef", token="AgAAAA**AQAAAA**aAAAAA**2FApWg**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wDk4OlC5mFpAmdj6x9nY+seQ**9awAAA**AAMAAA**d63JWRuVCrO5PQy3n8nejZzsnqWUtEp072ktglLxrpkBTGiZJSJbCIk5wPuPWOs5sLcDTeWG5/ZOGqW8A5nMYCcMJeNaSW6Qu19hpY53TPRqhakOqybrmqf23i9Rzjm93LF9OhuxzACuDpSEz01OQo67XXtdn7QV/z7j8cT58lkJjsIpTg4MknCbsy1h2b9oLXM7gWyZqooCTSDiXgNq6MvOYZ9sEkCtdYJVE2F39hIzCXVr3h48pjhlEsL3tk3YDPxirF4CLJwEop7rHrTR+bT/LP9N2x2tgdo7eLQqu1sG/pCUmaL8JTxAYVGMoFguOrzWAKw2SqLYKXjvDjR8DjOP29Na43oVULhFrZUSXoIQwO257kKrPeX5yjtmR33uwYgCvqgCme/gajFfWLgUQS1/sNnEm1oZO42zGxvV5QBnkebzqob3cs5qLGr233HSlME4IZDMGH81Ikx0/1ArSHpx7fYZphocn2IUcG7rDssPmG6aY62kpwCm8jPkaQTKYl5h32M2qjaG2FBwhWGvERTjlOLLxedwRqWDpffa1M9GjeTJgUCaUh4fO8v4sh8Wde6fb1T2kki5h3EtSbv26bK5pUotDE9KK3lPWNT+L0eVAGjdKRZSwyeN9XWxjYafQGgKNI55Tl1Zg35Bo3UxchRNg5H1EVsnz7GX0Lgh0DY1xBV7N/zp0L99plM1FZWKX2quQKfmEMVeB4/QjAyIqeh+oHCG/ziJkgrcNrDLFhs6C/QWamtW0KcNt2X4iC81",
                       warnings=True, site_id=SITEID, timeout=20, domain='api.ebay.com')
                errors = []
                for order in orders:
                    transaction_ids = order.ebay_transaction_id.split()
                    item_ids = order.ebay_item_id.split()
                    index = 0
                    for transaction_id in transaction_ids:
                        api.execute('CompleteSale', {'ItemID': item_ids[index], 'TransactionID': transaction_id, 'Paid': 'true', 'Shipped': 'true'})
                        index += 1
                    # if api.warnings():
                    #     print("Warnings" + api.warnings())

                    # if api.response.content:
                    #     print("Call Success: %s in length" % len(api.response.content))

                    # print(api.response.content)
                    # print(api.response.json())
                    # print("Response Reply: %s" % api.response.reply)

                    # dictstr = "%s" % api.response.dict()
                    # print("Response dictionary: %s..." % dictstr[:150])
                    # replystr = "%s" % api.response.reply
                    # print("Response Reply: %s" % replystr[:150])

                    resp = api.response.dict()

                    if resp["Ack"] == "Success" or resp["Ack"] == "Warning":
                        order.ebay_completed = True
                    else:
                        errors.append([order.id, str(resp)])
            except ConnectionError as e:
                # print(e)
                # print(e.response.dict())
                self._send_ebay_error_mail("problema di connessione %s " % e, '[EBAY] ERRORE nel complete_ebay_order')
                return

            if errors:
                # print errors
                self._send_ebay_error_mail("problemi con queste transazioni %s " % errors, '[EBAY] ERRORE nel complete_ebay_order')

    def _send_ebay_error_mail(self, body, subject):
        """
        utility invio mail errore ebay
        """
        values = {
            'subject': subject,
            'body_html': body,
            'email_from': "shopping@multiplayer.com",
            # TODO 'email_to': "ecommerce-servizio@netaddiction.it",
            'email_to': "andrea.bozzi@netaddiction.it",
        }

        email = self.env['mail.mail'].create(values)
        email.send()

    def _create_ebay_order(self, transaction, multi=False):
        """
        utility per creare un ordine a partire da una transazione ebay
        """
        if multi:
            transactions = transaction
            transaction = transaction[0]
        buyer = transaction["Buyer"]
        user = self.env["res.partner"].search([("email", "=", buyer["Email"])])
        user = user[0] if user else None
        # print buyer["Email"]
        # print user
        shipping_address = buyer["BuyerInfo"]["ShippingAddress"]
        italy_id = self.env["res.country"].search([('code', '=', 'IT')])[0]
        shipping_dict = {'name': shipping_address["Name"], 'street': shipping_address["Street1"], 'phone': shipping_address["Phone"] if "Phone" in shipping_address else None, 'country_id': italy_id, 'city': shipping_address["CityName"], 'zip': shipping_address["PostalCode"], 'street2': shipping_address.get("Street2") or False}
        if not shipping_dict["street2"]:
            parsed = re.findall('\d+', shipping_dict["street"])
            if parsed:
                shipping_dict['street2'] = parsed[-1]
                # shipping_dict["street"].translate(None, parsed[-1])
                shipping_dict["street"] = re.sub(parsed[-1], '', shipping_dict["street"])
            else:
                shipping_dict['street2'] = False
        user_shipping = None
        user_billing = None
        if user:
            find_ship_address = False
            for child in user.child_ids:
                if child.type == "delivery" and child.equals(shipping_dict):
                    find_ship_address = True
                    user_shipping = child
                    break
            if not find_ship_address:
                shipping_dict['company_id'] = user.company_id.id
                shipping_dict['is_company'] = False
                shipping_dict['type'] = 'delivery'
                shipping_dict['customer'] = True
                shipping_dict['parent_id'] = user.id
                shipping_dict['country_id'] = italy_id.id

                user_shipping = self.env["res.partner"].create(shipping_dict)
            billings = [child for child in user.child_ids if child.type == 'invoice']
            if billings:
                user_billing = billings[0]
            else:
                user_billing = self.env["res.partner"].create({'name': user.name, 'type': 'invoice', 'street': shipping_dict["street"], 'phone': shipping_dict["phone"], 'country_id': italy_id.id, 'city': shipping_dict["city"], 'zip': shipping_dict["zip"], 'parent_id': user.id, 'company_id': user.company_id.id, 'street2': shipping_dict["street2"]})
        else:
            # creare user e indirizzo che sega
            company_id = self.env["res.company"].search([("name", "=", "Multiplayer.com")])[0].id
            user = self.env["res.partner"].create({
                'name': shipping_dict["name"],
                'company_id': company_id,
                'email': buyer["Email"],
                'is_company': True,
                'customer': True,
                'type': 'contact',
                'phone': shipping_dict["phone"],
                'notify_email': 'none'})
            user_shipping = self.env["res.partner"].create({
                'name': shipping_dict["name"],
                'company_id': company_id,
                'street': shipping_dict["street"],
                'street2': shipping_dict["street2"],
                'phone': shipping_dict["phone"],
                'country_id': italy_id.id,
                'city': shipping_dict["city"],
                'zip': shipping_dict["zip"],
                'parent_id': user.id,
                'is_company': False,
                'customer': True,
                'type': 'delivery',
                'notify_email': 'none'})
            user_billing = self.env["res.partner"].create({
                'name': shipping_dict["name"],
                'company_id': company_id,
                'street': shipping_dict["street"],
                'street2': shipping_dict["street2"],
                'phone': shipping_dict["phone"],
                'country_id': italy_id.id,
                'city': shipping_dict["city"],
                'zip': shipping_dict["zip"],
                'parent_id': user.id,
                'is_company': False,
                'customer': True,
                'type': 'invoice',
                'notify_email': 'none'})

        # creare ordine e mandarlo in lavorazione
        # public_price_list = self.env["product.pricelist"].search([("name", "=", "Listino Pubblico")])[0].id
        sda = self.env["delivery.carrier"].search([('name', '=', 'Corriere Espresso SDA')])[0].id
        brt = self.env["delivery.carrier"].search([('name', '=', 'Corriere Espresso BRT')])[0].id
        # print public_price_list
        journal_id = None
        pay_pal_tran_id = ''
        if (transaction["Status"]["PaymentMethodUsed"] == "PayPal"):
            journal_id = self.env['ir.model.data'].get_object('netaddiction_payments', 'paypal_journal').id
            pay_pal_tran_id = transaction["MonetaryDetails"]["Payments"]["Payment"]["ReferenceID"]['value']
        elif (transaction["Status"]["PaymentMethodUsed"] == "COD"):
            journal_id = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal').id
        else:
            return "pagamento sconosciuto"

        try:
            order = self.env["sale.order"].create({
                'partner_id': user.id,
                'partner_invoice_id': user_billing.id,
                'partner_shipping_id': user_shipping.id,
                'state': 'draft',
                'delivery_option': 'all',
                'carrier_id': random.choice([sda, brt]),
                'payment_method_id': journal_id,
                'pay_pal_tran_id': pay_pal_tran_id,
                'ebay_item_id': transaction["Item"]["ItemID"],
                'ebay_completed': False,
                'from_ebay': True,
                'ebay_transaction_id': transaction["TransactionID"],
            })
            # print transaction["TransactionPrice"]
            if not multi:
                quantity = int(transaction["QuantityPurchased"])
                prod = self.env["product.product"].browse(int(transaction["Item"]["SKU"]))
                if not prod:
                    return "product not found %s " % transaction["Item"]["SKU"]
                order_line = self.env["sale.order.line"].create({
                    "order_id": order.id,
                    "product_id": prod.id,
                    "product_uom_qty": quantity,
                    "product_uom": prod.uom_id.id,
                    "name": prod.display_name,
                    "price_unit": float(transaction["TransactionPrice"]['value']),
                })
                prod.ebay_selled += 1
            else:
                transaction_id = ""
                item_id = ""
                for t in transactions:
                    quantity = int(t["QuantityPurchased"])
                    prod = self.env["product.product"].browse(int(t["Item"]["SKU"]))
                    if not prod:
                        return "product not found %s " % t["Item"]["SKU"]
                    order_line = self.env["sale.order.line"].create({
                        "order_id": order.id,
                        "product_id": prod.id,
                        "product_uom_qty": quantity,
                        "product_uom": prod.uom_id.id,
                        "name": prod.display_name,
                        "price_unit": float(t["TransactionPrice"]['value']),
                    })
                    transaction_id += t["TransactionID"]
                    transaction_id += " "
                    item_id += t["Item"]["ItemID"]
                    item_id += " "
                    prod.ebay_selled += 1
                order.ebay_transaction_id = transaction_id
                order.ebay_item_id = item_id

            order.manual_confirm()
        except Exception as e:
            return "%s" % e

        return "OK"

    def _build_category_dictionary(self):
        return {
            self.env["product.category"].search([("name", "=", "Abbigliamento")]).id: "183742",
            self.env["product.category"].search([("name", "=", "Figures")]).id: "246",
            self.env["product.category"].search([("name", "=", "Film e Serie TV")]).id: "617",
            self.env["product.category"].search([("name", "=", "Gadget")]).id: {
                self.env["product.attribute.value"].search([("name", "=", "Portachiavi")]).id: "47137",
                0: "1383"
            },
            self.env["product.category"].search([("name", "=", "Giochi")]).id: {
                self.env["product.attribute.value"].search([("name", "=", "Giochi da Tavolo")]).id: "2550",
                self.env["product.attribute.value"].search([("name", "=", "Carte Collezionabili")]).id: "2536",
                self.env["product.attribute.value"].search([("name", "=", "LEGO")]).id: "19006",
                0: "234"

            },
            self.env["product.category"].search([("name", "=", "Libri e Fumetti")]).id: "268",
            self.env["product.category"].search([("name", "=", "Modellismo e Model Kit")]).id: "180277",
            self.env["product.category"].search([("name", "=", "Pro Gaming")]).id: {
                self.env["product.attribute.value"].search([("name", "=", "Tastiere")]).id: "33963",
                self.env["product.attribute.value"].search([("name", "=", "Mouse")]).id: "23160",
                self.env["product.attribute.value"].search([("name", "=", "Cuffie / Headset / Auricolari")]).id: "80183",
                self.env["product.attribute.value"].search([("name", "=", "MousePad")]).id: "23895",
                self.env["product.attribute.value"].search([("name", "=", "Monitor")]).id: "162497",
                self.env["product.attribute.value"].search([("name", "=", "Controller")]).id: "117042",
                0: "162"

            },
            self.env["product.category"].search([("name", "=", "Tecnologia")]).id: "162",
            self.env["product.category"].search([("name", "=", "Videogiochi")]).id: "139973",
        }

    @api.model
    def _ebay_cron_hourly(self):
        try:
            self._upload_new_products_to_ebay()
        except Exception as e:
            self._send_ebay_error_mail(" %s  ****  %s  PRODUCT_ID: %s" % (traceback.format_exc(), ''.join(traceback.format_stack()), e), '[EBAY] ECCEZIONE lanciata da _upload_new_products_to_ebay ')

        try:
            self._update_products_on_ebay()
        except Exception as e:
            self._send_ebay_error_mail(" %s  ****  %s" % (traceback.format_exc(), ''.join(traceback.format_stack())), '[EBAY] ECCEZIONE lanciata da _update_products_on_ebay ')

        try:
            self._get_ebay_orders()
        except Exception as e:
            self._send_ebay_error_mail(" %s  ****  %s" % (traceback.format_exc(), ''.join(traceback.format_stack())), '[EBAY] ECCEZIONE lanciata da _get_ebay_orders ')
        try:
            self._end_products_on_ebay()
        except Exception as e:
            self._send_ebay_error_mail(" %s  ****  %s" % (traceback.format_exc(), ''.join(traceback.format_stack())), '[EBAY] ECCEZIONE lanciata da _end_products_on_ebay ')

        return True

    @api.model
    def _ebay_cron_daily(self):
        try:
            self._remove_expired_ebay_ids()
        except Exception as e:
            self._send_ebay_error_mail(" %s  ****  %s" % (traceback.format_exc(), ''.join(traceback.format_stack())), '[EBAY] ECCEZIONE lanciata da _remove_expired_ebay_ids ')
        try:
            self._complete_ebay_orders()
        except Exception as e:
            self._send_ebay_error_mail(" %s  ****  %s" % (traceback.format_exc(), ''.join(traceback.format_stack())), '[EBAY] ECCEZIONE lanciata da _complete_ebay_orders ')
        # try:
        #     self._relist_products_on_ebay()
        # except Exception as e:
        #     self._send_ebay_error_mail("%s  %s" % (e, traceback.print_exc()), '[EBAY] ECCEZIONE lanciata da _relist_products_on_ebay ')
        return True
