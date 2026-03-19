from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchasePartialOrderWizard(models.TransientModel):
    _name = "purchase.partial.order.wizard"
    _description = "Wizard para partición de orden de compra"

    purchase_id = fields.Many2one("purchase.order", string="Orden de Compra", required=True)
    option = fields.Selection([
        ('new', 'Crear nueva orden'),
        ('existing', 'Seleccionar orden existente')
    ], string="Opción", required=True, default="new")

    existing_order_id = fields.Many2one(
        "purchase.order",
        string="Orden de Compra Existente",
        domain=[('state', '=', 'draft')]
    )

    def confirm_action(self):
        """ Ejecuta la partición de la orden de compra """
        self.ensure_one()

        # ✅ Validar que haya al menos un producto seleccionado
        selected_lines = self.purchase_id.order_line.filtered('selected_for_partial')
        if not selected_lines:
            raise UserError(_("Debe seleccionar al menos un producto para crear una orden parcial."))

        # ✅ Validar factura solo si la moneda NO es USD
        if self.purchase_id.currency_id.name != 'USD' and self.purchase_id.invoice_status in ['invoiced', 'to invoice']:
            raise UserError(_("No puede dividir una orden que ya ha sido facturada."))

        # ✅ Validar recepciones validadas
        if self.purchase_id.picking_ids.filtered(lambda p: p.state == 'done'):
            raise UserError(_("No puede dividir una orden con recepciones ya validadas."))

        if self.option == "new":
            new_order = self._create_new_purchase_order()
        else:
            new_order = self.existing_order_id
            # 📌 Agregar el nombre de la orden actual al campo de texto, sin duplicados
            existing_names = (new_order.partition_origin_names or "").split(', ')
            if self.purchase_id.name not in existing_names:
                existing_names.append(self.purchase_id.name)
                new_order.partition_origin_names = ', '.join(existing_names)

        self._process_order_lines(new_order)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': new_order.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def _create_new_purchase_order(self):
        """ Crea una nueva orden de compra sin generar un nuevo albarán """
        new_order = self.purchase_id.copy(default={
            'order_line': [],
            'partner_ref': self.purchase_id.partner_ref,
            'picking_ids': [(5, 0, 0)],
            'partition_origin_names': self.purchase_id.name  # Inicia con el nombre de la orden actual
        })

        return new_order

    def _process_order_lines(self, new_order):
        """ Procesa las líneas de la orden de compra y realiza la partición """
        selected_lines = self.purchase_id.order_line.filtered('selected_for_partial')


        for line in selected_lines:
            if line.to_split_qty <= 0:
                raise UserError(f"La cantidad a partir en {line.product_id.display_name} debe ser mayor a 0.")
            if line.to_split_qty > line.product_qty:
                raise UserError(f"La cantidad a partir en {line.product_id.display_name} no puede ser mayor a la cantidad original.")

            remaining_qty = line.product_qty - line.to_split_qty

            # Crear la nueva línea en la orden parcial
            # line.copy(default={
            #     'order_id': new_order.id,
            #     'product_qty': line.to_split_qty,
            #     'to_split_qty': 0,
            #     'selected_for_partial': False
            # })
            
            new_line_vals = {
                'order_id': new_order.id,
                'product_qty': line.to_split_qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'taxes_id': [(6, 0, line.taxes_id.ids)],
                'product_id': line.product_id.id,
                'name': line.name,
                'date_planned': line.date_planned,
                'product_uom': line.product_uom.id,
                'to_split_qty': 0,
                'selected_for_partial': False,
                # ❌ NO copiar packaging_id ni packaging_qty aquí
            }

            self.env['purchase.order.line'].create(new_line_vals)

            # Actualizar la orden original sin activar cambios en stock
            line.write({
                'product_qty': remaining_qty if remaining_qty > 0 else 0,
                'price_unit': 0 if remaining_qty == 0 else line.price_unit,
                'to_split_qty': 0,
                'selected_for_partial': False
            })

        # **Asegurar que NO se cree un nuevo albarán en la orden original**
        self._prevent_new_picking_creation()

    def _prevent_new_picking_creation(self):
        """ Evita que Odoo genere un nuevo albarán en la orden original """
        if self.purchase_id.picking_ids:
            for picking in self.purchase_id.picking_ids:
                if picking.state in ['waiting', 'confirmed']:
                    picking.action_cancel()  # ❌ Cancela el albarán extra si se ha creado

