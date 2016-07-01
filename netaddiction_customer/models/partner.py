# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Partner(models.Model):
    _inherit = 'res.partner'
    #_name = 'netaddiction.partner'

    is_default_delivery_address = fields.Boolean(string="Indirizzo di Default")
    company_address = fields.Char(string="Azienda")
    rating = fields.Selection([('0','Negativo'), ('1','Medio'), ('2','Positivo')], string='Rating', default="2")
    email_rating = fields.Selection([('A+','A+'), ('A','A'), ('B','B'), ('C','C'), ('D','D'), ('E','E'), ('F','F'), ('','Non valutato')], string='Email Rating', default='')
    birthdate = fields.Date(string="Data di nascita")

    @api.multi
    def name_get(self):
        res = []

        for s in self:
            if len(s.parent_id)>0 and s.customer == True:
                res.append((s.id,s.name + ', ' + s.city + ' ' + s.street + ' ' + s.street2))
            else:
                res.append((s.id,s.name))

        return res

    @api.one
    def write(self,values):
        """
        quando  aggiorno un partner controllo che solo un indirizzo del contatto abbia is_default_delivery_address = True
        IMPORTANTE: se facendo edit del padre si cancella un figlio A e ad un altro figlio B si mette is_default_delivery_address a true, A non verrà cancellato perchè gli viene messo is is_default_delivery_address a false
        """


        if not self.parent_id:
            #è stato salvato il padre
            #prima cosa imposto il suo default delivery address a false
                values['is_default_delivery_address'] = False
                ids = []
                #vediamo se almeno a un figlio è stato messo default delivery address a true
                if 'child_ids' in values.keys():
                    for child in values['child_ids']:
                        if child[2] and 'is_default_delivery_address' in child[2].keys() and child[2]['is_default_delivery_address'] and child[1]:
                            ids.append(child[1])

                    #se c'è almeno un figlio con default delivery address a true...
                    if ids:
                        #allora modifico values per tutti i figli
                        for child in values['child_ids']:
                        #di default scelgo come unico figlio con default delivery a true il primo che incontro
                        
                            #se aveva già altre modifiche gli aggiungo is default delivery address
                            if child[2]:
                                child[2]['is_default_delivery_address'] = child[1] == ids[0] 
                                child[2]['Write_come_from_father'] = True 
                            #altrimenti lo registro in values
                            else:
                                son = self.search([('id','=',child[1])])
                                if son.is_default_delivery_address :
                                    child[0] = 1
                                    child[2] = {'is_default_delivery_address': child[1] == ids[0] }
                                    child[2]['Write_come_from_father'] = True
                    else:
                        #sto inserendo/modificando dei figli ma nessuno ha default delivery address a true
                        #devo controllare di avere già un indirizzo di default altrimenti lo assegno a uno dei figli modificati/creati (impedisco la creazione dei primi contatti senza indirizzo di default)
                        got_a_delivery_address = False
                        for id_child in self.child_ids:
                            son = self.search([('id','=',id_child.id)])
                            got_a_delivery_address = got_a_delivery_address  or son.is_default_delivery_address
                            if got_a_delivery_address:
                                break
                        if not got_a_delivery_address:
                             #se aveva già altre modifiche gli aggiungo is default delivery address
                            child = values['child_ids'][0]
                            if child[2]:
                                    child[2]['is_default_delivery_address'] = True
                                    child[2]['Write_come_from_father'] = True 
                            #altrimenti lo registro in values
                            else:
                                    child[0] = 1
                                    child[2] = {'is_default_delivery_address': True }
                                    child[2]['Write_come_from_father'] = True


                           

        else:
                if 'Write_come_from_father' not in values.keys() and 'is_default_delivery_address' in values.keys() :
                #salvataggio da dentro un figlio! Write_come_from_father indica che la write è stata chiamata dalla write del padre
                    if  values['is_default_delivery_address']:
                        for id_father in self.parent_id:
                                father = self.search([('id','=',id_father.id)])
                                ids = []
                                for id_child in father.child_ids:
                                    if id_child.id != self.id:
                                        son = self.search([('id','=',id_child.id)])
                                        if son.is_default_delivery_address:
                                            ids.append(son.id)

                                for default_id in ids:
                                    new_values = {'is_default_delivery_address' : False, 'Write_come_from_father': True}

                                    if default_id != self.id:
                                        son = self.search([('id','=',default_id)])
                                        son.write(new_values)
                    else:
                        #non permetto di mettere false. Per cambiare bisogna mettere un altro a true
                        values['is_default_delivery_address'] = True


                else:
                    if 'Write_come_from_father' in values.keys():
                        del values['Write_come_from_father']        
    


        return super(Partner, self).write(values)

    @api.model
    def create(self,values):
        
        """
        quando  creo un partner controllo che solo un indirizzo del contatto abbia is_default_delivery_address = True
        """

            
        if  'parent_id' in values.keys() and values['parent_id']:

            if  'is_default_delivery_address' in values.keys() and values['is_default_delivery_address']:
                id_father = values['parent_id']
                father = self.env['res.partner'].search([('id','=',id_father)])
                ids = []
                for id_child in father.child_ids:
                    new_values = {'is_default_delivery_address' : False, 'Write_come_from_father': True}
                    son = self.env['res.partner'].search([('id','=',id_child.id)])
                    if son.is_default_delivery_address:
                        son.write(new_values)
        else:
            #sono un padre, non posso avere indirizzo di default
            values['is_default_delivery_address'] = False

            
        return  super(Partner, self).create(values)

    @api.one
    def unlink(self):
        " abbiamo deciso di non far cancellare i clienti. Li archiviamo."
        self.active = False
        if self.affiliate_id:
            self.affiliate_id['active'] = False

        # for id_child in self.child_ids:
        #     id_child.active = False

        # if self.is_default_delivery_address:
        #     for id_father in self.parent_id:
        #         father = self.search([('id','=',id_father.id)])
        #         ids = []
        #         for id_child in father.child_ids:
        #             if id_child.id != self.id:
        #                 son = self.search([('id','=',id_child.id)])
        #                 if  not son.is_default_delivery_address:
        #                     new_values = {'is_default_delivery_address' : True, 'Write_come_from_father': True}
        #                     son.write(new_values)
        #                     break 

                                   

        # return super(Partner, self).unlink()

