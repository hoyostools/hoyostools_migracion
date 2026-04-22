from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    # Campos booleanos
    shareholder = fields.Boolean(string='Tipo persona')
    supplier_format = fields.Boolean(string='Supplier')
    customer_format = fields.Boolean(string='Customer')
    is_bank = fields.Boolean(string='Bank')
    is_employee = fields.Boolean(string='Employee', compute='_compute_is_employee')
    
    # Otros campos
    person_exo = fields.Selection(
        selection=[
            ('01', 'Persona Natural'),
            ('02', 'Persona Juridica'),
        ],
        string='Tipo de documento Exógena'
    )
    supplier_invoice_count = fields.Integer(string="# Facturas de proveedores")

    # Onchange para tipo de persona
    @api.onchange('person_type')
    def _onchange_person_type_shareholder(self):
        self.shareholder = self.person_type == 'Persona Juridica y asimilada'

    # Onchange para categoría: Proveedor
    @api.onchange('name', 'category_id')
    def _onchange_category_supplier(self):
        self.supplier_format = any(category.name == 'Proveedor' for category in self.category_id)

    # Onchange para categoría: Cliente
    @api.onchange('name', 'category_id')
    def _onchange_category_customer(self):
        self.customer_format = any(category.name == 'Cliente' for category in self.category_id)

    # Onchange para categoría: Banco
    @api.onchange('name', 'category_id')
    def _onchange_category_bank(self):
        self.is_bank = any(category.name == 'Banco' for category in self.category_id)

    # Cómputo de campo booleano si es empleado
    @api.depends('employee_ids')
    def _compute_is_employee(self):
        for partner in self:
            partner.is_employee = bool(partner.employee_ids)
