# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'

    is_default_delivery_address = fields.Boolean(string="Indirizzo di Default")

    # TODO: quando salva e is_default_delivery_address is true allora deve mettere a false
    # tutti gli altri indirizzi.
    @api.multi
    def write(self,values):
        """
        quando  aggiorno un partner controllo che solo un indirizzo del contatto abbia is_default_delivery_address = True
        """
        
        for p in self:
            if not self.parent_id:
                #è stato salvato il padre
                
                #prima cosa imposto il suo default delivery address a false
                values['is_default_delivery_address'] = False
                child_attr = []
                ids = []
                #vediamo se almeno a un figlio è stato messo default delivery address a true
                if 'child_ids' in values.keys():
                    for child in values['child_ids']:
                        if child[2] and child[2]['is_default_delivery_address']:
                            print "found!"
                            ids.append(child[1])
                    print "ecco gli id dei figli"
                    print ids
                    #se c'è almeno un figlio con default delivery address a true...
                    if ids:
                        print "c'è ids"
                        #allora modifico values per tutti i figli
                        for idx, child in enumerate(values['child_ids']):
                        #di default scelgo come unico figlio con default delivery a true il primo che incontro
                        
                            #se aveva già altre modifiche gli aggiungo is default delivery address
                            if values['child_ids'][idx][2]:
                                values['child_ids'][idx][2]['is_default_delivery_address'] = values['child_ids'][idx][1] == ids[0] 
                            #altrimenti lo registro in values
                            else:
                                values['child_ids'][idx][0] = 1
                                values['child_ids'][idx][2] = {'is_default_delivery_address': values['child_ids'][idx][1] == ids[0] }
                            values['child_ids'][idx][2]['Write_come_from_father'] = True 
                           

            else:
                if 'Write_come_from_father' not in values.keys() and 'is_default_delivery_address' in values.keys() :
                #salvataggio da dentro un figlio! Write_come_from_father indica che la write è stata chiamata dalla write del padre
                    if  values['is_default_delivery_address']:
                        new_values = {'is_default_delivery_address' : False, 'Write_come_from_father': True}
                        for id_father in self.parent_id:
                                father = self.search([('id','=',id_father.id)])
                                ids = []
                                for id_child in father.child_ids:
                                    if id_child.id != self.id:
                                        son = self.search([('id','=',id_child.id)])
                                        if son.is_default_delivery_address:
                                            ids.append(son.id)

                                for default_id in ids:
                                    if default_id != self.id:
                                        son = self.search([('id','=',default_id)])
                                        son.write(new_values)
                    else:
                        #non permetto di mettere false. Per cambiare bisogna mettere un altro a true
                        values['is_default_delivery_address'] = True


                else:
                    if 'Write_come_from_father' in values.keys():
                        del values['Write_come_from_father']        

        


                                  #  son.is_default_delivery_address = son.id == self.id
    #-------------------------------------------------------------


        return super(Partner, self).write(values)

    @api.model
    def create(self,values):
        
        """
        quando  creo un partner controllo che solo un indirizzo del contatto abbia is_default_delivery_address = True
        """
        for p in self:
            if not self.parent_id:
                #è stato salvato il padre
                
                #prima cosa imposto il suo default delivery address a false
                values['is_default_delivery_address'] = False
                child_attr = []
                ids = []
                #vediamo se almeno a un figlio è stato messo default delivery address a true
                if 'child_ids' in values.keys():
                    for child in values['child_ids']:
                        if child[2] and child[2]['is_default_delivery_address']:
                            print "found!"
                            ids.append(child[1])
                    print "ecco gli id dei figli"
                    print ids
                    if not ids:
                        #se  non c'è almeno un figlio con default delivery address a true
                        #indirizzo di default assegnato al primo child 
                        ids.append(values['child_ids'][1])
                   
                    print "c'è ids"
                    #allora modifico values per tutti i figli
                    for idx, child in enumerate(values['child_ids']):
                    #di default scelgo come unico figlio con default delivery a true il primo che incontro
                        
                        #se aveva già altre modifiche gli aggiungo is default delivery address
                        if values['child_ids'][idx][2]:
                            values['child_ids'][idx][2]['is_default_delivery_address'] = values['child_ids'][idx][1] == ids[0] 
                        #altrimenti lo registro in values
                        else:
                            values['child_ids'][idx][0] = 1
                            values['child_ids'][idx][2] = {'is_default_delivery_address': values['child_ids'][idx][1] == ids[0] }
                        values['child_ids'][idx][2]['Create_come_from_father'] = True 
                       

            else:
                if 'Create_come_from_father' not in values.keys() and 'is_default_delivery_address' in values.keys() :
                #creazione di un figlio! Create_come_from_father indica che la create è stata chiamata dalla create del padre
                    if  values['is_default_delivery_address']:
                        new_values = {'is_default_delivery_address' : False, 'Write_come_from_father': True}
                        for id_father in self.parent_id:
                                father = self.search([('id','=',id_father.id)])
                                ids = []
                                for id_child in father.child_ids:
                                    if id_child.id != self.id:
                                        son = self.search([('id','=',id_child.id)])
                                        if son.is_default_delivery_address:
                                            ids.append(son.id)

                                for default_id in ids:
                                    if default_id != self.id:
                                        son = self.search([('id','=',default_id)])
                                        son.write(new_values)
                else:
                    if 'Create_come_from_father' in values.keys():
                        del values['Create_come_from_father']        



        return  super(Partner, self).create(values)

