# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class IssueReport(models.Model):
    _name = "netaddiction.project.issue.report"
    _description = "Statistiche Customer Care"
    _auto = False

    user_id = fields.Many2one('res.users', string='Assegnato a', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    create_date = fields.Datetime('Data Creazione', readonly=True)
    issue_id = fields.Many2one('project.issue', string="Id problematica", readonly=True)
    state = fields.Char(string="Stato", readonly=True)
    issue_type_src = fields.Char(string="Tipo", readonly=True)

    
    hour_for_assign = fields.Float('Ore per assegnare la problematica',readonly=True)
    avg_dfa = fields.Float('Media ore per assegnare la problematica',readonly=True,group_operator="avg")

    hour_for_close = fields.Float('Ore per chiudere la problematica',readonly=True)
    avg_dfc = fields.Float('Media ore per chiudere la problematica',readonly=True,group_operator="avg")
    
    hour_assign_to_close = fields.Float('Ore da assegnazione a chiusura',readonly=True)
    avg_dfac = fields.Float('Media ore da assegnazione a chiusura',readonly=True,group_operator="avg")

    satisfaction_rate = fields.Char('Tasso di Soddisfazione',readonly=True)
   
    number_email = fields.Integer('# email')
 

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
        	CREATE OR REPLACE VIEW %s as (
        		SELECT 
        		pj.id as id,
        		pj.user_id as user_id,
        		pj.company_id,
        		pj.create_date,
        		pj.hour_for_assign,
        		pj.hour_for_assign as avg_dfa,
                pj.hour_for_close,
                pj.hour_for_close as avg_dfc,
        		pj.id as issue_id,
        		pj.satisfaction_rate,
                pj.state,
                pj.issue_type_src,
                pj.hour_assign_to_close,
                pj.hour_assign_to_close as avg_dfac,
                pj.number_email
        		FROM project_issue pj
        		WHERE pj.active='true'
        	)""", (self._table, ))