# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from decimal import getcontext, Decimal

class ProductReview(models.Model):
    _inherit = 'product.template'
    
    def _get_avg_product_rating(self):
        for review_obj in self:
            avg_product_rating = 0.0
            total_messages = len( [x.id for x in review_obj.reviews_ids if x.message_rate > 0] )
            if total_messages > 0:
                total_rate = sum( [x.message_rate for x in review_obj.reviews_ids] )
                avg_product_rating = Decimal( total_rate ) / Decimal( total_messages )
            review_obj.avg_product_rating = avg_product_rating
    
    reviews_ids = fields.One2many('reviews.ratings', 'rating_product_id', string='Reviews & Ratings')
    avg_product_rating = fields.Float( compute=_get_avg_product_rating, store=False, string='Product Ratings' )
    
    
    
class ReviewRating(models.Model):
    _name = 'reviews.ratings'
    _rec_name = 'short_desc'
    
    customer_id = fields.Many2one("res.users", string='Customer')
    short_desc = fields.Char(string='Short Description')
    message_rate = fields.Integer( 'Message Rating' )
    website_message = fields.Boolean( 'Is Website Message', default=False )
    review = fields.Text(string="Review")
    rating_product_id = fields.Many2one('product.template','Product')
    website_published = fields.Boolean(related='rating_product_id.website_published', store=True)
    

        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
