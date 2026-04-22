from odoo import fields, models

class ConceptExogenus(models.Model):
    _name = 'concept.exogenus'
    _description = 'Concept Exogenus'

    name = fields.Char(string="Concept")
    description_concept = fields.Char(string="Description")
    format_exogenus_concept_id = fields.Many2one('format.exogenus',strings='Formato')
