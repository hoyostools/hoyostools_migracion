from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):

        res = super().button_validate()

        sin_regla_location = self.env["stock.location"].search([
            ("complete_name", "=", "CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05")
        ], limit=1)

        for picking in self:

            if picking.picking_type_code != 'incoming' or picking.picking_type_id.warehouse_id.code != 'CLH':
                continue

            for move in picking.move_ids:

                product = move.product_id
                qty = move.quantity

                route_ok = product.route_ids.filtered(
                    lambda r: r.name == "Yumbo: Abastecer U05"
                )

                if not route_ok:
                    continue

                orderpoint = self.env["stock.warehouse.orderpoint"].search([
                    ("product_id", "=", product.id)
                ], limit=1)

                record_vals = {
                    "product_id": product.id,
                    "picking_id": picking.id,
                    "fecha_llegada": picking.date_done,
                    "cantidad_recibida": qty,
                }

                if orderpoint:

                    dest =  product.ubicacion_reab or sin_regla_location
                    if not product.ubicacion_reab or product.ubicacion_reab.complete_name == 'CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05':
                        record_vals.update({
                            "sin_regla": True,
                            "location_id": sin_regla_location.id
                        })

                    picking_type = self.env["stock.picking.type"].search([
                        ("code", "=", "internal"),("sequence_code", "=", "INT"),("warehouse_id", "=", picking.picking_type_id.warehouse_id.id)
                    ], limit=1)

                    responsible = self._get_auto_location_responsible(product, dest)

                    new_picking = self.env["stock.picking"].create({
                        "picking_type_id": picking_type.id,
                        "location_id": picking.location_dest_id.id,
                        "location_dest_id": dest.id,
                        "origin": picking.name,
                        "user_id": responsible.id if responsible else False,
                        "priority": '1'
                    })

                    purchase = self.env["purchase.order"].search([
                        ("name", "=", picking.origin)
                    ], limit=1)

                    move = self.env["stock.move"].create({
                        "name": product.name,
                        "product_id": product.id,
                        "product_uom_qty": qty,
                        "product_uom": product.uom_id.id,
                        "picking_id": new_picking.id,
                        "location_id": picking.location_dest_id.id,
                        "location_dest_id": dest.id,
                    })

                    country = product.product_tmpl_id.country_of_origin

                    origen = "importado"
                    if country and country.name == "Colombia":
                        origen = "nacional"

                    record_vals.update({
                        "cantidad_pendiente": qty,
                        "move_id": move.id,
                        "location_id": dest.id,
                        "product_max_qty": orderpoint.product_max_qty,
                        "purchase_id": purchase.id,
                        "ranking_rotacion": product.ranking,
                        "origen_bienes": origen,
                    })

                    new_picking.action_confirm()

                elif sin_regla_location:
                    record_vals.update({
                        "sin_regla": True,
                        "location_id": sin_regla_location.id
                    })
                else:
                    record_vals.update({
                        "sin_regla": True,
                        "location_id": sin_regla_location.id
                    })

                anterior = self.env["auto.location.record"].search([('product_id', '=', product.id)])
                if anterior:
                    anterior.write(record_vals)
                else:
                    self.env["auto.location.record"].create(record_vals)

        return res

    def _get_auto_location_responsible(self, product, location):

        Responsible = self.env["auto.location.responsible"]

        country = product.product_tmpl_id.country_of_origin

        origen = "importado"
        if country and country.name == "Colombia":
            origen = "nacional"

        domain = [("origen_bienes", "=", origen)]

        responsibles = Responsible.search(domain)

        if not responsibles:
            return False

        best_user = False
        min_pickings = float('inf')

        for rec in responsibles:

            rec._compute_picking_count()

            if rec.picking_count < min_pickings:
                min_pickings = rec.picking_count
                best_user = rec.user_id

        return best_user

