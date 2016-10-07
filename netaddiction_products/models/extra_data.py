# -*- coding: utf-8 -*-

from openerp.exceptions import Warning
from openerp import models, fields, api
import xmlrpclib
import xml.etree.ElementTree as ET
import datetime
import urllib2
import json
import re


class ExtraData(models.Model):
    _name = 'netaddiction.extradata.key.value'

    company_id = fields.Many2one(comodel_name='res.company', string="Azienda", required=True)
    value = fields.Char(string="Valore", required=True)
    key = fields.Char(string="Chiave", required=True)
    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product", required=True, ondelete="set null")
    key_type = fields.Char(string="Tipo/Sito")

class ConfigApiExtraData(models.Model):
    _name = 'netaddiction.extra.data.settings'

    category = fields.Many2one(string="Categoria", comodel_name="product.category")
    api_set = fields.Selection(string="API", selection=[('multi', 'Multiplayer.it'), ('movie', 'Movieplayer.it')])
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('account.account'))

class Products(models.Model):
    _inherit = "product.product"

    extra_data = fields.One2many(string="Extra_Data", comodel_name="netaddiction.extradata.key.value", inverse_name="product_id")

    extra_data_id = fields.Char(string="Id Scheda Extra Dati")

    @api.one
    def api_get_extra_data(self):
        api_data = {
            'multi': 'api_get_extra_data_multi',
            'movie': 'api_get_extra_data_movie'
        }
        config = self.env['netaddiction.extra.data.settings'].sudo().search([('category', '=', self.categ_id.id), ('company_id', '=', self.env.user.company_id.id)])
        if config:
            if self.extra_data_id:
                func = getattr(self, api_data[config.api_set])
                func()
            else:
                raise Warning("Devi inserire l'id della scheda dai cui recuperare i dati")
        else:
            raise Warning("A questa categoria non è associata nessuna API")

    @api.one
    def api_get_extra_data_movie(self):
        url_series = 'http://movieplayer.it/api/v1/tvseries/%s/?format=json&api_key=f260cc4fab3e6a2d268ee825905e9780ccdeed5a' % self.extra_data_id
        url_movies = 'http://movieplayer.it/api/v1/movie/%s/?format=json&api_key=f260cc4fab3e6a2d268ee825905e9780ccdeed5a' % self.extra_data_id
        try:
            response = urllib2.urlopen(url_series)
            text = json.load(response)
        except:
            try:
                response = urllib2.urlopen(url_movies)
                text = json.load(response)
            except:
                raise Warning("Erorre di comunicazione con movieplayer.it")

        parser = {
            'genres': 'genere',
            'actors': 'attori',
            'poster': 'poster',
            'trailer': 'file_url',
            'year': 'anno',
            'screenwriters': 'sceneggiatura',
            'duration': 'durata',
            'directors': 'regia',
            'images': 'images'
        }

        self.sudo().extra_data.sudo().unlink()
        attr = {
            'company_id': self.env.user.company_id.id,
            'product_id': self.id,
            'key_type': 'Movieplayer.it'
        }

        attr['key'] = 'genere'
        attr['value'] = ','.join(text.get('genres', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        attr['key'] = 'attori'
        attr['value'] = ','.join(text.get('actors', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        attr['key'] = 'poster'
        poster = text.get('poster', False)
        if poster:
            attr['value'] = poster['url']
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        # TODO: se ci dovessero essere problemi con i video cercare di trovare
        # in modo migliore l'id del video
        attr['key'] = 'file_url'
        trailer = text.get('trailer', False)
        if trailer:
            trailer = trailer['file_url']
            l = [m.start() for m in re.finditer('/', trailer)]
            start = l[-2] + 1
            finish = l[-1]
            video_id = trailer[start:finish]
            attr['value'] = '<iframe src="https://video.netaddiction.it/embed/%s" frameborder="0" allowfullscreen></iframe>' % video_id
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        attr['key'] = 'images'
        imgs = text.get('images', False)
        if poster:
            img_list = []
            f = imgs['still-frame']
            for i in f:
                img_list.append(i['url'])
            attr['value'] = json.dumps(img_list)
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        attr['key'] = 'anno'
        attr['value'] = text.get('year', False)
        if attr['value']:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        attr['key'] = 'regia'
        attr['value'] = ','.join(text.get('directors', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        attr['key'] = 'sceneggiatura'
        attr['value'] = ','.join(text.get('screenwriters', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        attr['key'] = 'durata'
        attr['value'] = text.get('duration', False)
        if attr['value']:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

    @api.one
    def api_get_extra_data_multi(self):
        parser = {
            'url': 'url_multiplayer_it',
            'pegi': 'pegi',
            'sviluppatore': 'sviluppatore',
            'publisher': 'publisher',
            'manual_lang': 'manual_lang',
            'software_lang': 'software_lang',
            'anno': 'anno'
        }
        # prende i dati da multiplayer.it
        try:
            d = xmlrpclib.Server("http://multiplayer.it/service/")
            root = ET.fromstring(d.get_gamecard_info(self.extra_data_id).encode('utf8'))
        except:
            raise Warning("C'è stato un problema nella connessione con multiplayer.it")
        for sub in root:
            attr = {
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Multiplayer.it'
            }
            if sub.tag in parser.keys():
                search = self.env['netaddiction.extradata.key.value'].sudo().search([('product_id', '=', self.id), ('key', '=', parser[sub.tag]), ('company_id', '=', self.env.user.id)])
                if search:
                    if sub.tag == 'anno':
                        anno = datetime.datetime.strptime(sub.text, '%d-%m-%Y')
                        if search.value != anno.year:
                            search.sudo().value = anno.year
                    else:
                        if search.value != sub.text:
                            search.sudo().value = sub.text
                else:
                    # qua aggiungo
                    if sub.tag == 'anno':
                        anno = datetime.datetime.strptime(sub.text, '%d-%m-%Y')
                        attr['key'] = parser[sub.tag]
                        attr['value'] = anno.year
                    else:
                        attr['key'] = parser[sub.tag]
                        attr['value'] = sub.text

                    self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            # aggiungi immagini e video
            imgs = []
            if sub.tag == 'immagini':
                for img in sub:
                    for i in img:
                        if i.tag == 'fotourl':
                            imgs.append(i.text)
                img_search = self.env['netaddiction.extradata.key.value'].sudo().search([('product_id', '=', self.id), ('key', '=', 'images'), ('company_id', '=', self.env.user.id)])
                if img_search:
                    img_search.sudo().value = json.dumps(imgs)
                else:
                    attr['key'] = 'images'
                    attr['value'] = json.dumps(imgs)
                    self.env['netaddiction.extradata.key.value'].sudo().create(attr)

            if sub.tag == 'video':
                for v in sub:
                    if v.tag == 'embed':
                        v_search = self.env['netaddiction.extradata.key.value'].sudo().search([('product_id', '=', self.id), ('key', '=', 'video_flv'), ('company_id', '=', self.env.user.id)])
                        if v_search:
                            v_search.sudo().value = v.text
                        else:
                            attr['key'] = 'video_flv'
                            attr['value'] = v.text
                            self.env['netaddiction.extradata.key.value'].sudo().create(attr)

        return True
