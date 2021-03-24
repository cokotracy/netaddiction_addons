from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)



class InheritAffiliateProgram(models.Model):
    _inherit = "affiliate.program"

    commission_type = fields.Selection([('d', 'default'),('c', 'Coupon')], string="Comission Type",required=True,default="d")

    def open_coupon_program(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Affiliate Coupon Program',
        'view_mode': 'form',
        'res_model': 'coupons.program',
        'res_id': self.env.ref("wk_affiliate_coupon.affiliate_coupons_program").id,
        'target': 'current',
        }

class InheritAffiliateVisit(models.Model):
    _inherit = "affiliate.visit"

    commission_type = fields.Selection([('d', 'default'),('c', 'Coupon')], string="Comission Type")
    coupon_type = fields.Selection([('single', 'Single'),('consolidate', 'Consolidate')],readonly='True', string="Coupon Type")
    coupon_amount = fields.Float(string='Coupon Amount',default=0.0)
    coupon_code = fields.Char(string='Code', size=100)
    consolidate_amount = fields.Float(string='Consolidate Amount',default=0.0)
    sale_coupon_program_id = fields.Many2one('sale.coupon.program',string='Coupon Program',readonly='True')

    @api.model
    def create_invoice(self):
        if self.commission_type == "c" :
            raise UserError("For commission type coupon invoice cannot be generated.")
        else:
            return super(InheritAffiliateVisit,self).create_invoice()

    def _coupon_code(self,partner):
        visit = self.env["sale.coupon"].sudo().search([("is_affiliate_coupon","=",True)])
        return str(partner.res_affiliate_key) + "-" + str(len(visit))


    def _create_coupon(self,coupon_program,partner):

        vals = {
            "partner_id":partner.id,
            "program_id":coupon_program.id,
            "code": self._coupon_code(partner),
            "is_affiliate_coupon":True,
        }
        return self.env["sale.coupon"].sudo().create(vals)



    def _get_rate(self,affiliate_method,affiliate_type,type_id):

        if self.affiliate_program_id.commission_type == "c":
            default_coupons_program = self.env["coupons.program"].sudo().search([],limit=1)
            discount_type = None
            discount_fixed_amount = None
            if self.affiliate_method=="ppc":
                discount_type = default_coupons_program.ppc_discount_type
                if discount_type == "fixed_amount":
                    discount_fixed_amount = default_coupons_program.ppc_fixed_amount
                else:
                    discount_fixed_amount =  (self.price_total*default_coupons_program.ppc_percentage /100)

            elif self.affiliate_method=="pps":
                discount_type = default_coupons_program.pps_discount_type
                if discount_type == "fixed_amount":
                    discount_fixed_amount = default_coupons_program.pps_fixed_amount
                else:
                    discount_fixed_amount = (self.price_total*default_coupons_program.pps_percentage /100)
            vals = {
                    "name":"Coupons Program For affiliate user %s"%self.affiliate_partner_id.name,
                    "promo_code_usage":"code_needed",
                    "discount_apply_on":"on_order",
                    "program_type":"coupon_program",
                    "discount_type":"fixed_amount",
                    "discount_fixed_amount":discount_fixed_amount,
                    "validity_duration":default_coupons_program.coupon_validity,
                    "coupon_type" : "single",
                }

            coupon_program = self.env["sale.coupon.program"].sudo().create(vals)
            coupon= self._create_coupon(coupon_program,self.affiliate_partner_id)
            self.write({'coupon_type':"single",
                        "sale_coupon_program_id": coupon_program.id,
                        'coupon_code': coupon.code,
                        'coupon_amount':coupon_program.discount_fixed_amount,
                        "sale_coupon_program_id": coupon_program.id,})
            response = {
                    'is_error':0,
                    'message':'Commission successfully added',

                    }
            return response

        else:
            return super(InheritAffiliateVisit,self)._get_rate(affiliate_method,affiliate_type,type_id)

    def send_coupon_mail(self,coupon,partner):
        template_id = self.env.ref('sale_coupon.mail_template_sale_coupon')
        if template_id:
            template_id.send_mail(coupon.id, email_values={'email_to': partner.email, 'email_from': partner.company_id.email or ''})

    def confirm_visit(self):
        records = self
        self = self[0]
        default_coupons_program = self.env["coupons.program"].sudo().search([],limit=1)
        coupons_visits_pps = records.filtered(lambda visit: visit.commission_type == 'c' and visit.affiliate_method == "pps" and visit.state =="draft")
        coupons_visits_ppc = records.filtered(lambda visit: visit.commission_type == 'c' and visit.affiliate_method == "ppc" and visit.state =="draft")
        coupons_visits =  None
        if coupons_visits_pps:
            coupons_visits = coupons_visits_pps
        elif coupons_visits_ppc:
            coupons_visits = coupons_visits_ppc
        else:
            coupons_visits =  self.env["affiliate.visit"].sudo()

        default_visit = records - coupons_visits
        coupon_count = 0
        if coupons_visits:
            partner_ids = list(set(visit.affiliate_partner_id  for visit in coupons_visits))
            visit_details = []
            visit_dict = {}
            for partner in partner_ids:
                list_amount = []
                visit_ids = []
                for visit in coupons_visits:
                    if visit.affiliate_partner_id.id == partner.id:
                        if visit.affiliate_method=="ppc":
                            discount_type = default_coupons_program.ppc_discount_type
                            if discount_type == "fixed_amount":
                                list_amount.append(default_coupons_program.ppc_fixed_amount)
                            else:
                                list_amount.append(self.price_total*default_coupons_program.ppc_percentage /100)

                        elif self.affiliate_method=="pps":
                            discount_type = default_coupons_program.pps_discount_type
                            if discount_type == "fixed_amount":
                                discount_fixed_amount = default_coupons_program.pps_fixed_amount
                            else:
                                discount_fixed_amount = (self.price_total*default_coupons_program.pps_percentage /100)

                        list_amount.append(discount_fixed_amount)
                        visit_ids.append(visit)
                c = 0
                for v in visit_ids:
                    # [{}]
                    if c == 0:
                        vals = {
                                "name":"Coupons Program For affiliate user %s"%v.affiliate_partner_id.name,
                                "promo_code_usage":"code_needed",
                                "discount_apply_on":"on_order",
                                "program_type":"coupon_program",
                                "discount_type":"fixed_amount",
                                "discount_fixed_amount":sum(list_amount),
                                "validity_duration":default_coupons_program.coupon_validity,
                                "coupon_type" : ["consolidate" if len(visit_ids)>1 else "single"][0],
                                # "aff_visit_id":[(6, 0, [IDs])]
                            }
                        coupon_program = self.env["sale.coupon.program"].sudo().create(vals)
                        coupon = self._create_coupon(coupon_program,visit_ids[0].affiliate_partner_id)
                        sent_mail = self.send_coupon_mail(coupon,v.affiliate_partner_id)
                        coupon_count += 1
                        c = c + 1
                    value = {
                    "coupon_type":"consolidate",
                    "coupon_amount": list_amount[c],
                    "consolidate_amount":sum(list_amount),
                    "coupon_code": coupon_program.coupon_ids.code,
                    "state":"confirm",
                    "sale_coupon_program_id": coupon_program.id,
                    }
                    v.write(value)
        elif default_visit :
            for visit in default_visit:
                visit.action_confirm()
        if coupon_count:
            msg = "%s Coupons Created and mailed to respective partner"%(coupon_count)
            partial_id = self.env['wk.wizard.message'].create({'text': msg})
            return {
            'name': "Message",
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'wk.wizard.message',
            'res_id': partial_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            }
