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
    
    working_hours_close = fields.Float('Ore per chiudere la problematica',readonly=True)
    avg_whc = fields.Float('Media ore per chiudere la problematica',readonly=True,group_operator="avg")
    working_hours_open = fields.Float('Ore per assegnare la problematica',readonly=True)
    avg_who = fields.Float('Media ore per assegnare la problematica',readonly=True,group_operator="avg")

    satisfaction_rate = fields.Char('Tasso di Soddisfazione',readonly=True)
   
 

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
        	CREATE OR REPLACE VIEW %s as (
        		SELECT 
        		pj.id as id,
        		pj.user_id as user_id,
        		pj.company_id,
        		pj.create_date,
        		pj.working_hours_close,
        		pj.working_hours_close as avg_whc,
        		pj.id as issue_id,
        		pj.working_hours_open,
        		pj.working_hours_open as avg_who,
        		pj.satisfaction_rate
        		FROM project_issue pj
        		WHERE pj.active='true'
        	)""" % (self._table))