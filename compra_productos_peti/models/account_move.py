# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Product(models.Model):
    _inherit = 'product.template'

    fecha_recepcion = fields.Datetime(string="Fecha de Recepción")

    orden_compra = fields.Many2many(
        comodel_name='purchase.order',
        inverse_name='orden_producto',
        string='',
        )

class Purchase(models.Model):
    _inherit = 'purchase.order'

    orden_producto = fields.Many2many(comodel_name='product.template')

    def button_confirm(self):
        res = super(Purchase,self).button_confirm()
        for record in self:
            if record.order_line:
                productos = record.order_line.product_id
                if productos:
                    for producto in productos:
                        #producto.orden_compra = False
                        producto.orden_compra += record
        return res

class Stock(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('date_done')
    def asignar_fecha_producto(self):
        for record in self:
            if record.move_ids_without_package:
                productos = record.move_ids_without_package.product_id.product_tmpl_id
                if productos:
                    for producto in productos:
                        producto.fecha_recepcion = False
                        producto.fecha_recepcion = record.date_done