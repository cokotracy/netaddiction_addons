# -*- coding: utf-8 -*-
import logging
from openerp import models
from lxml import etree, objectify
# http://localhost:8069/web/image/product.template/6901/image/300x300?unique=1d457f6
SITEID = "101"
VERSION = "967"
IT_LANGUAGE = "it_IT"
IT = "IT"
BRAND = "Brand"
MPN = "MPN"
EUR = "EUR"
GTC = "GTC"
FIXED_PRICE = "FixedPriceItem"
TERNI = "Terni, TR"
PAYPAL = "PayPal"
COD = "COD"
MB_OPTION = "MoneyBack"
MB = "Money Back"
RETURNS_ACCEPTED_OPTION = "ReturnsAccepted"
RETURNS_ACCEPTED = "Rimborsati entro 10 giorni"

INSURANCE_INCLUDED = "IncludedInShippingHandling"
IT_COURIER = "IT_ExpressCourier"
SHIPPING_COST = "4.90"
ADDITIONAL_COST = "0.00"
SHIPPING_PRIORITY = "1"
DISPATCH_MAX_TIME = "2"
CONDITION_ID = "1000"
ITA = "Italy"

END_REASON = "NotAvailable"

IMAGE_URL_FORMAT = 'https://images.multiplayer.com/thumbs/%(splitter)s/%(model)s-%(field)s-%(pk)d-%(width)dx%(height)d-q%(quality)d.jpg'

_logger = logging.getLogger(__name__)



class EbayXMLBuilder(models.TransientModel):
    """Classe di utilità associata a un transient model creare xml per ebay
    """
    _name = "netaddiction.ebay.xmlbuilder"


    def get_object_image_url(self, pk, model='product.product', width=0, height=0, crop=False, field='image', quality=85):
        """
        Returns the URL of the image stored in the given field of the given object.
        """
        # DEBUG 
        # return "http://images.multiplayer.com/thumbs/0a/cc/product.product-image-285195-0x0-q85.jpg"

        kwargs = {'model': model, 'pk': pk, 'field': field}

        query = [
            ('res_model', '=', model),
            ('res_field', '=', field),
            ('res_id', '=', pk),
        ]

        try:
            attachment = self.env['ir.attachment'].search(query)
        except Exception:
            return ''

        splitter = '%s/%s' % (attachment.store_fname[3:5], attachment.store_fname[5:7])

        kwargs.update({
            'splitter': splitter,
            'width': width,
            'height': height,
            'quality': quality,
        })


        return IMAGE_URL_FORMAT % kwargs

    def build_image_upload(self, products_id):

        bulk_root = etree.Element("BulkDataExchangeRequests", xmlns="urn:ebay:apis:eBLBaseComponents")
        header = etree.SubElement(bulk_root, "Header", xmlns="urn:ebay:apis:eBLBaseComponents")
        site_id = etree.SubElement(header, "SiteID")
        site_id.text = SITEID
        version = etree.SubElement(header, "Version")
        version.text = VERSION
        for prod_id in products_id:
            root = etree.SubElement(bulk_root, "UploadSiteHostedPicturesRequest", xmlns="urn:ebay:apis:eBLBaseComponents")
            err_language = etree.SubElement(root, "ErrorLanguage")
            err_language.text = IT_LANGUAGE
            warning_level = etree.SubElement(root, "WarningLevel")
            warning_level.text = "High"
            version_el = etree.SubElement(root, "Version")
            version_el.text = VERSION
            message_id = etree.SubElement(root, "MessageID")
            message_id.text = prod_id
            img_url = etree.SubElement(root, "ExternalPictureURL")
            img_url.text = self.get_object_image_url(int(prod_id))
        # print etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)
        return etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)

    def parse_image_upload_response(self, xml):

        ret = {}
        root = objectify.fromstring(xml)
        for img_data in root.UploadSiteHostedPicturesResponse:
            # print img_data.Ack.text
            if img_data.Ack.text != "Failure":
                ret[img_data.CorrelationID.text] = {'url': img_data.SiteHostedPictureDetails.FullURL.text, 'expire_date': img_data.SiteHostedPictureDetails.UseByDate.text}

        return ret

    def build_add_fixed_price_items(self, products, paypal_mail, cod_cost):
        bulk_root = etree.Element("BulkDataExchangeRequests")
        header = etree.SubElement(bulk_root, "Header")
        site_id = etree.SubElement(header, "SiteID")
        site_id.text = SITEID
        version = etree.SubElement(header, "Version")
        version.text = VERSION
        for prod_id, prod in products.iteritems():
            root = etree.SubElement(bulk_root, "AddFixedPriceItemRequest", xmlns="urn:ebay:apis:eBLBaseComponents")
            err_language = etree.SubElement(root, "ErrorLanguage")
            err_language.text = IT_LANGUAGE
            warning_level = etree.SubElement(root, "WarningLevel")
            warning_level.text = "High"
            version = etree.SubElement(root, "Version")
            version.text = VERSION
            message_id = etree.SubElement(root, "MessageID")
            # message_id.text = prod_id + "|" + prod["qty"]
            message_id.text = prod_id
            item = etree.SubElement(root, "Item")
            item_specifics = etree.SubElement(item, "ItemSpecifics")
            name_value = etree.SubElement(item_specifics, "NameValueList")
            name1 = etree.SubElement(name_value, "Name")
            name1.text = BRAND
            item1 = etree.SubElement(name_value, "Value")
            # item1.text = prod["name"][0:60]
            item1.text = "Does Not Apply"
            name_value_2 = etree.SubElement(item_specifics, "NameValueList")
            name2 = etree.SubElement(name_value_2, "Name")
            name2.text = MPN
            item2 = etree.SubElement(name_value_2, "Value")
            item2.text = prod["ean"]
            category_mapping = etree.SubElement(item, "CategoryMappingAllowed")
            category_mapping.text = "true"
            country = etree.SubElement(item, "Country")
            country.text = IT
            currency = etree.SubElement(item, "Currency")
            currency.text = EUR
            description = etree.SubElement(item, "Description")
            description.text = prod["description"]
            listing_duration = etree.SubElement(item, "ListingDuration")
            # TODO GTC
            listing_duration.text = GTC
            listing_type = etree.SubElement(item, "ListingType")
            listing_type.text = FIXED_PRICE
            location = etree.SubElement(item, "Location")
            location.text = TERNI
            payment_method1 = etree.SubElement(item, "PaymentMethods")
            payment_method1.text = PAYPAL
            payment_method2 = etree.SubElement(item, "PaymentMethods")
            payment_method2.text = COD
            paypal_address = etree.SubElement(item, "PayPalEmailAddress")
            paypal_address.text = paypal_mail
            picture_details = etree.SubElement(item, "PictureDetails")
            picture_url = etree.SubElement(picture_details, "PictureURL")
            picture_url.text = prod["ebay_image"]
            primary_category = etree.SubElement(item, "PrimaryCategory")
            category = etree.SubElement(primary_category, "CategoryID")
            category.text = prod["ebay_category"]
            quantity = etree.SubElement(item, "Quantity")
            quantity.text = prod["qty"]
            shipping_details = etree.SubElement(item, "ShippingDetails")
            apply_shipping_discount = etree.SubElement(shipping_details, "ApplyShippingDiscount")
            apply_shipping_discount.text = "false"
            insurance_option = etree.SubElement(shipping_details, "InsuranceOption")
            insurance_option.text = INSURANCE_INCLUDED
            shipping_service_options = etree.SubElement(shipping_details, "ShippingServiceOptions")
            shipping_service = etree.SubElement(shipping_service_options, "ShippingService")
            shipping_service.text = IT_COURIER
            shipping_service_cost = etree.SubElement(shipping_service_options, "ShippingServiceCost")
            shipping_service_cost.text = SHIPPING_COST
            shipping_service_additional_cost = etree.SubElement(shipping_service_options, "ShippingServiceAdditionalCost")
            shipping_service_additional_cost.text = ADDITIONAL_COST
            shipping_service_priority = etree.SubElement(shipping_service_options, "ShippingServicePriority")
            shipping_service_priority.text = SHIPPING_PRIORITY
            expedited_service = etree.SubElement(shipping_service_options, "ExpeditedService")
            expedited_service.text = "true"
            shipping_type = etree.SubElement(shipping_details, "ShippingType")
            shipping_type.text = "Flat"
            third_party_checkout = etree.SubElement(shipping_details, "ThirdPartyCheckout")
            third_party_checkout.text = "false"
            insurance_details = etree.SubElement(shipping_details, "InsuranceDetails")
            insurance_option = etree.SubElement(insurance_details, "InsuranceOption")
            insurance_option.text = INSURANCE_INCLUDED
            codcost = etree.SubElement(shipping_details, "CODCost", currencyID=EUR)
            codcost.text = cod_cost
            dispatch_time = etree.SubElement(item, "DispatchTimeMax")
            dispatch_time.text = DISPATCH_MAX_TIME
            condition_id = etree.SubElement(item, "ConditionID")
            condition_id.text = CONDITION_ID
            ship_to = etree.SubElement(item, "ShipToLocations")
            ship_to.text = IT
            site = etree.SubElement(item, "Site")
            site.text = ITA
            price = etree.SubElement(item, "StartPrice", currencyID=EUR)
            price.text = prod["price"]
            title = etree.SubElement(item, "Title")
            title.text = prod["name"]
            sku = etree.SubElement(item, "SKU")
            sku.text = prod_id
            product_listing_details = etree.SubElement(item, "ProductListingDetails")
            brand_mpn = etree.SubElement(product_listing_details, "BrandMPN")
            brand = etree.SubElement(brand_mpn, "Brand")
            # brand.text = prod["name"][0:60]
            brand.text = "Does Not Apply"
            mpn = etree.SubElement(brand_mpn, "MPN")
            mpn.text = prod["ean"][0:60]
            ean = etree.SubElement(product_listing_details, "EAN")
            ean.text = prod["ean"]
            product_id = etree.SubElement(product_listing_details, "ProductID")
            product_id.text = prod_id
            return_policy = etree.SubElement(item, "ReturnPolicy")
            refund_option = etree.SubElement(return_policy, "RefundOption")
            refund_option.text = MB_OPTION
            refund = etree.SubElement(return_policy, "Refund")
            refund.text = MB
            returns_accepted_option = etree.SubElement(return_policy, "ReturnsAcceptedOption")
            returns_accepted_option.text = RETURNS_ACCEPTED_OPTION
            returns_accepted = etree.SubElement(return_policy, "ReturnsAccepted")
            returns_accepted.text = RETURNS_ACCEPTED
        _logger.warning("***************************************")
        _logger.warning(etree.tostring(bulk_root, xml_declaration=True, pretty_print=True))
        _logger.warning("***************************************")
        # print etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)
        return etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)

    def parse_addfixed_response(self, xml):

        ret = {}
        root = objectify.fromstring(xml)
        
        for resp in root.AddFixedPriceItemResponse:
            # print resp.Ack.text
            if resp.Ack.text != "Failure":
                ret[resp.CorrelationID.text] = {'id': resp.ItemID.text, 'start': resp.StartTime.text, 'end': resp.EndTime.text, 'duplicate': False}
            else:
                for error in resp.Errors:
                    _logger.warning("%s" % error.ErrorCode.text)
                    if error.ErrorCode.text == "21919067":
                        id_ebay = None
                        for error_value in error.ErrorParameters:
                            if error_value.get("ParamID") == "1":
                                id_ebay = error_value.Value.text
                        if id_ebay:
                            ret[resp.CorrelationID.text] = {'duplicate': True, 'id': id_ebay}
        return ret

    def build_revise_fixed_price_items(self, products):
        bulk_root = etree.Element("BulkDataExchangeRequests")
        header = etree.SubElement(bulk_root, "Header")
        site_id = etree.SubElement(header, "SiteID")
        site_id.text = SITEID
        version = etree.SubElement(header, "Version")
        version.text = VERSION
        for prod_id, prod in products.iteritems():
            root = etree.SubElement(bulk_root, "ReviseFixedPriceItemRequest", xmlns="urn:ebay:apis:eBLBaseComponents")
            err_language = etree.SubElement(root, "ErrorLanguage")
            err_language.text = IT_LANGUAGE
            warning_level = etree.SubElement(root, "WarningLevel")
            warning_level.text = "High"
            version = etree.SubElement(root, "Version")
            version.text = VERSION
            item = etree.SubElement(root, "Item")
            description = etree.SubElement(item, "Description")
            description.text = prod["description"]
            item_id = etree.SubElement(item, "ItemID")
            item_id.text = prod['ebay_id']
            picture_details = etree.SubElement(item, "PictureDetails")
            picture_url = etree.SubElement(picture_details, "PictureURL")
            picture_url.text = prod["ebay_image"]
            quantity = etree.SubElement(item, "Quantity")
            quantity.text = prod["qty"]
            price = etree.SubElement(item, "StartPrice", currencyID=EUR)
            price.text = prod["price"]
            title = etree.SubElement(item, "Title")
            title.text = prod["name"]
            message_id = etree.SubElement(root, "MessageID")
            message_id.text = prod['ebay_id']
        # print etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)
        return etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)

    def parse_revisefixed_response(self, xml):

        ret = []
        root = objectify.fromstring(xml)
        for resp in root.ReviseFixedPriceItemResponse:
            # print resp.Ack.text
            if resp.Ack.text == "Failure":
                ret.append(resp.CorrelationID.text)

        return ret

    def build_relist_fixed_price_items(self, products):
        bulk_root = etree.Element("BulkDataExchangeRequests")
        header = etree.SubElement(bulk_root, "Header")
        site_id = etree.SubElement(header, "SiteID")
        site_id.text = SITEID
        version = etree.SubElement(header, "Version")
        version.text = VERSION
        for prod_id, prod in products.iteritems():
            root = etree.SubElement(bulk_root, "RelistFixedPriceItemRequest", xmlns="urn:ebay:apis:eBLBaseComponents")
            err_language = etree.SubElement(root, "ErrorLanguage")
            err_language.text = IT_LANGUAGE
            warning_level = etree.SubElement(root, "WarningLevel")
            warning_level.text = "High"
            version = etree.SubElement(root, "Version")
            version.text = VERSION
            item = etree.SubElement(root, "Item")
            description = etree.SubElement(item, "Description")
            description.text = prod["description"]
            item_id = etree.SubElement(item, "ItemID")
            item_id.text = prod['ebay_id']
            picture_details = etree.SubElement(item, "PictureDetails")
            picture_url = etree.SubElement(picture_details, "PictureURL")
            picture_url.text = prod["ebay_image"]
            quantity = etree.SubElement(item, "Quantity")
            quantity.text = prod["qty"]
            price = etree.SubElement(item, "StartPrice", currencyID=EUR)
            price.text = prod["price"]
            title = etree.SubElement(item, "Title")
            title.text = prod["name"]
            message_id = etree.SubElement(root, "MessageID")
            message_id.text = prod['id']
        # print etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)
        return etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)

    def parse_relistfixed_response(self, xml):

        ret = {}
        root = objectify.fromstring(xml)
        for resp in root.RelistFixedPriceItemResponse:
            # print resp.Ack.text
            if resp.Ack.text != "Failure":
                ret[resp.CorrelationID.text] = {'start': resp.StartTime.text, 'end': resp.EndTime.text}

        return ret

    def build_end_fixed_price_items(self, products_id):
        bulk_root = etree.Element("BulkDataExchangeRequests")
        header = etree.SubElement(bulk_root, "Header")
        site_id = etree.SubElement(header, "SiteID")
        site_id.text = SITEID
        version = etree.SubElement(header, "Version")
        version.text = VERSION
        for (prod_id, ebay_id) in products_id:
            root = etree.SubElement(bulk_root, "EndFixedPriceItemRequest", xmlns="urn:ebay:apis:eBLBaseComponents")
            err_language = etree.SubElement(root, "ErrorLanguage")
            err_language.text = IT_LANGUAGE
            warning_level = etree.SubElement(root, "WarningLevel")
            warning_level.text = "High"
            version = etree.SubElement(root, "Version")
            version.text = VERSION
            ending_reason = etree.SubElement(root, "EndingReason")
            ending_reason.text = END_REASON
            item_id = etree.SubElement(root, "ItemID")
            item_id.text = str(ebay_id)
            message_id = etree.SubElement(root, "MessageID")
            message_id.text = str(prod_id)
        # print etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)
        return etree.tostring(bulk_root, xml_declaration=True, pretty_print=True)

    def parse_endfixed_response(self, xml):

        ret = {}
        root = objectify.fromstring("%s" % xml)
        for resp in root.EndFixedPriceItemResponse:
            # print resp.Ack.text
            if resp.Ack.text != "Failure":
                ret[resp.CorrelationID.text] = {'end': resp.EndTime.text}
        return ret

    def build_get_seller_transactions_items(self, time_from_string, time_to_string):
        root = etree.Element("GetSellerTransactionsRequest")
        time_from = etree.SubElement(root, "ModTimeFrom")
        time_from.text = time_from_string
        time_to = etree.SubElement(root, "ModTimeTo")
        time_to.text = time_to_string
        pagination = etree.SubElement(root, "Pagination")
        entries_per_page = etree.SubElement(pagination, "EntriesPerPage")
        entries_per_page.text = "200"
        page_number = etree.SubElement(pagination, "PageNumber")
        page_number.text = "1"
        detail_level = etree.SubElement(root, "DetailLevel")
        detail_level.text = "ReturnAll"
        site_id = etree.SubElement(root, "SiteID")
        site_id.text = SITEID
        version = etree.SubElement(root, "Version")
        version.text = VERSION
        
        # print etree.tostring(root, xml_declaration=True, pretty_print=True)
        return etree.tostring(root, xml_declaration=True, pretty_print=True)

