# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models, fields

import logging

_logger = logging.getLogger(__file__)


class StockPickingMixin(models.AbstractModel):
    _name = 'stock.picking.mixin'
    _description = 'Stock Picking Mixin'

    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    routing_module_version = fields.Char(
        related='company_id.routing_module_version',
    )

    def _get_stock_object(self, rec_id):
        try:
            return self.search([('id', '=', int(rec_id))])
        except Exception as ex:
            _logger.error(ex)
            return False

    def _get_sml_with_entire_pack(self, operations_to_pick):
        return operations_to_pick.filtered(lambda x: x.package_level_id and not x.package_level_id.is_done)

    def _get_sml_data(self, sml_ids, operation_fields):
        sml_data = sml_ids.read(fields=operation_fields)
        [rec.update({'_type': 'stock.move.line'}) for rec in sml_data]
        return sml_data

    def _get_package_level_data(self, sml_ids, package_fields):
        package_level_data = sml_ids.mapped('package_level_id').read(fields=package_fields)
        [rec.update({'_type': 'stock.package_level'}) for rec in package_level_data]
        return package_level_data

    def _serialize_picking_data(self, stock_object, package_fields, operation_fields, limit=None):
        picking_data = []
        operations_to_pick = stock_object.operations_to_pick

        if limit:
            operations_to_pick = stock_object.operations_to_pick[:limit]

        # If entire pack is not used, return only stock move lines without packages
        is_using_entire_pack = stock_object.picking_type_id.show_entire_packs
        if not is_using_entire_pack:
            sml_data = self._get_sml_data(operations_to_pick, operation_fields)
            picking_data += sml_data
            return picking_data

        # Separation of stock move lines with entire pack and without
        sml_with_entire_pack_ids = self._get_sml_with_entire_pack(operations_to_pick)
        sml_without_entire_pack_ids = operations_to_pick - sml_with_entire_pack_ids

        sml_data = self._get_sml_data(sml_without_entire_pack_ids, operation_fields)
        package_level_data = self._get_package_level_data(sml_with_entire_pack_ids, package_fields)

        picking_data += sml_data
        picking_data += package_level_data

        return picking_data

    def serialize_record_ventor(self, rec_id, package_fields=[], operation_fields=[], limit=None):
        """Record serialization for the Ventor app."""
        stock_object = self._get_stock_object(rec_id)
        if not stock_object:
            return []

        picking_data = self._serialize_picking_data(stock_object, package_fields, operation_fields, limit)
        return picking_data
