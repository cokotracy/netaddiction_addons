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

    @api.model
    def delete_one_extra_img(self, object_id, url_delete):
        # cancella dal rigo object_id l'url_delete passato da backoffice quando clicchi su cancella immagine extra
        this_row = self.sudo().search([('id', '=', int(object_id))])
        the_dict = this_row.value.split(',')
        new_dict = []
        for line in the_dict:
            line = line.replace('"', '')
            line = line.replace("'", "")
            line = line.replace("[", "")
            line = line.replace("]", "")
            line = line.strip()
            new_dict.append(line)
        do = False
        for url in new_dict:
            if url == url_delete.strip():
                new_dict.remove(url)
                do = True
        this_row.sudo().write({'value': json.dumps(new_dict)})
        if do:
            return {'result': 'ok'}
        else:
            return {'result': 'no'}

    @api.model
    def add_one_extra_img(self, object_id, src):
        this_row = self.sudo().search([('id', '=', int(object_id))])
        the_dict = this_row.value.split(',')
        new_dict = []
        for line in the_dict:
            line = line.replace('"', '')
            line = line.replace("'", "")
            line = line.replace("[", "")
            line = line.replace("]", "")
            line = line.strip()
            new_dict.append(line)
        new_dict.append(src)
        this_row.sudo().write({'value': json.dumps(new_dict)})
        return {'result': 'ok'}

class ConfigApiExtraData(models.Model):
    _name = 'netaddiction.extra.data.settings'

    category = fields.Many2one(string="Categoria", comodel_name="product.category")
    api_set = fields.Selection(string="API", selection=[('multi', 'Multiplayer.it'), ('movie', 'Movieplayer.it')])
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('account.account'))

class Products(models.Model):
    _inherit = "product.product"

    extra_data = fields.One2many(string="Extra_Data", comodel_name="netaddiction.extradata.key.value", inverse_name="product_id")

    extra_data_id = fields.Char(string="Id Scheda Extra Dati")
    push_data_id = fields.Char(string="Id Scheda Push Dati")

    @api.multi
    def api_get_extra_data(self):
        self.ensure_one()

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

    @api.model
    def extra_dati_get_data(self, pid):
        product = self.search([('id', '=', int(pid))])
        api_data = {
            'multi': 'api_get_extra_data_multi',
            'movie': 'api_get_extra_data_movie'
        }
        config = self.env['netaddiction.extra.data.settings'].sudo().search([('category', '=', product.categ_id.id), ('company_id', '=', self.env.user.company_id.id)])
        if config:
            if product.extra_data_id:
                func = getattr(product, api_data[config.api_set])
                return func()
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

        pip = []
        new_images = []

        search = self.env['netaddiction.extradata.key.value'].sudo().search([('product_id', '=', self.id)])
        images = None
        for ser in search:
            if ser.key == 'images':
                if not images:
                    images = ser
                else:
                    ser.unlink()
            else:
                ser.unlink()

        attr = {
            'company_id': self.env.user.company_id.id,
            'product_id': self.id,
            'key_type': 'Movieplayer.it',
            'key': None,
            'value': None
        }

        attr['key'] = 'genere'
        attr['value'] = ','.join(text.get('genres', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'genere',
                'value': ','.join(text.get('genres', []))})

        attr['key'] = 'attori'
        attr['value'] = ','.join(text.get('actors', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'attori',
                'value': ','.join(text.get('actors', []))})

        attr['key'] = 'poster'
        poster = text.get('poster', False)
        if poster:
            attr['value'] = poster['url']
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'poster',
                'value': poster['url']})

        # TODO: se ci dovessero essere problemi con i video cercare di trovare
        # in modo migliore l'id del video
        attr['key'] = 'file_url'
        trailer = text.get('trailer', False)
        if trailer:
            attr['value'] = trailer['file_url']
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'file_url',
                'value': trailer['file_url']})

        attr['key'] = 'images'
        imgs = text.get('images', False)
        imm = {
            'company_id': self.env.user.company_id.id,
            'product_id': self.id,
            'key_type': 'Movieplayer.it',
            'key': 'images',
        }
        if poster:
            img_list = []
            f = imgs['still-frame']
            for i in f:
                img_list.append(i['url'])
            if not images:
                attr['value'] = json.dumps(img_list)
                imm['value'] = json.dumps(img_list)
                imm['value2'] = img_list
                self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            else:
                the_dict = images.value.split(',')
                new_dict = []
                attr['value2'] = []
                imm['value2'] = []
                for line in the_dict:
                    line = line.replace('"', '')
                    line = line.replace("'", "")
                    line = line.replace("[", "")
                    line = line.replace("]", "")
                    line = line.strip()
                    new_dict.append(line)
                    attr['value2'].append(line)
                    imm['value2'].append(line)
                for url in img_list:
                    if url not in new_dict:
                        new_images.append(url)
            pip.append(imm)

        attr['key'] = 'anno'
        attr['value'] = text.get('year', False)
        if attr['value']:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'anno',
                'value': text.get('year', False)})

        attr['key'] = 'regia'
        attr['value'] = ','.join(text.get('directors', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'regia',
                'value': ','.join(text.get('directors', []))})

        attr['key'] = 'sceneggiatura'
        attr['value'] = ','.join(text.get('screenwriters', []))
        if len(attr['value']) > 0:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'sceneggiatura',
                'value': ','.join(text.get('screenwriters', []))})

        attr['key'] = 'durata'
        attr['value'] = text.get('duration', False)
        if attr['value']:
            self.env['netaddiction.extradata.key.value'].sudo().create(attr)
            pip.append({
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Movieplayer.it',
                'key': 'durata',
                'value': text.get('duration', False)})

        return {'result': 'ok', 'values': pip, 'new_images': new_images}

    @api.one
    def api_get_extra_data_multi(self):
        parser = {
            'url': 'url_multiplayer_it',
            'pegi': 'pegi',
            'sviluppatore': 'sviluppatore',
            'publisher': 'publisher',
            'manual_lang': 'manual_lang',
            'software_lang': 'software_lang',
            'anno': 'anno',
            'immagini': 'images',
            'video': 'video_flv'
        }        # prende i dati da multiplayer.it
        try:
            d = xmlrpclib.Server("http://multiplayer.it/service/")
            root = ET.fromstring(d.get_gamecard_info(self.extra_data_id).encode('utf8'))
        except:
            raise Warning("C'è stato un problema nella connessione con multiplayer.it")

        search = self.env['netaddiction.extradata.key.value'].sudo().search([('product_id', '=', self.id)])
        images = None
        for ser in search:
            if ser.key == 'images':
                if not images:
                    images = ser
                else:
                    ser.unlink()
            else:
                ser.unlink()

        pip = []
        new_images = []

        for sub in root:
            attr = {
                'company_id': self.env.user.company_id.id,
                'product_id': self.id,
                'key_type': 'Multiplayer.it'
            }

            if sub.tag in parser.keys():
                attr['key'] = None

                if sub.tag == 'anno':
                    anno = datetime.datetime.strptime(sub.text, '%d-%m-%Y')
                    attr['key'] = parser[sub.tag]
                    attr['value'] = anno.year
                elif sub.tag == 'video':
                    for v in sub:
                        if v.tag == 'embed':
                            attr['key'] = 'video_flv'
                            attr['value'] = v.text
                            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', v.text)
                            attr['url_value'] = urls[0]
                elif sub.tag == 'immagini':
                    imgs = []
                    for img in sub:
                        for i in img:
                            if i.tag == 'fotourl':
                                imgs.append(i.text)
                    if not images:
                        attr['key'] = 'images'
                        attr['value'] = json.dumps(imgs)
                    else:
                        the_dict = images.value.split(',')
                        new_dict = []
                        for line in the_dict:
                            line = line.replace('"', '')
                            line = line.replace("'", "")
                            line = line.replace("[", "")
                            line = line.replace("]", "")
                            line = line.strip()
                            new_dict.append(line)
                        for url in imgs:
                            if url not in new_dict:
                                new_images.append(url)
                else:
                    attr['key'] = parser[sub.tag]
                    attr['value'] = sub.text

                if attr['key']:
                    self.env['netaddiction.extradata.key.value'].sudo().create(attr)
                    if attr['key'] == 'images':
                        new_dict = []
                        for line in imgs:
                            line = line.replace('"', '')
                            line = line.replace("'", "")
                            line = line.replace("[", "")
                            line = line.replace("]", "")
                            line = line.strip()
                            new_dict.append(line)
                        attr['value2'] = new_dict
                    pip.append(attr)
                else:
                    if len(new_images) > 0 and not attr['key']:
                        attr['key'] = 'images'
                        attr['value2'] = new_dict

                        pip.append(attr)

        return {'result': 'ok', 'values': pip, 'new_images': new_images}
