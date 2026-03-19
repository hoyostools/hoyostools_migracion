from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_repr, format_datetime


class StockReturnRequest(models.Model):
    _name = "ht.stock.return.request"
    _description = "Realizar devoluciones de acciones en todas las selecciones"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        "Referencia",
        default=lambda self: _("New"),
        copy=False,
        readonly=True,
        required=True,
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente/Proveedor", domain="[('type', 'in', ['contact', 'invoice'])]")
    pickup_address_id = fields.Many2one(
        'res.partner',
        string="Dirección a recoger",
        help="Dirección donde se recogerá la devolución",
        domain="[('id', 'child_of', partner_id), ('type', '=', 'delivery')]",
    )
    salesperson_id = fields.Many2one(
        comodel_name="res.users",
        string="Vendedor",
        related="partner_id.user_id",
        store=True,
        readonly=True,
    )
    return_type = fields.Selection(string="Tipo de Devolucion",
        selection=[
            ("supplier", "Devolver a Proveedor"),
            ("customer", "Devolucion de Cliente"),
            ("internal", "Devolver desde una Ubicacion Interna"),
        ],
        required=True,
        help="Proveedor: busque movimientos entrantes de este proveedor\n"
        "Cliente: busque movimientos salientes para este cliente\n"
        "Interno - Buscar movimientos salientes a esta ubicación.",
    )
    return_from_location = fields.Many2one(
        comodel_name="stock.location",
        string="Devolver Desde",
        help="Ubicacion desde donde se va a devolver",
        required=True,
        domain='[("usage", "=", "internal")]',
    )
    return_to_location = fields.Many2one(
        comodel_name="stock.location",
        string="Devolver A",
        help="Ubicacion a donde se va a devolver",
        required=True,
        domain='[("usage", "=", "internal")]',
    )
    return_order = fields.Selection(string="Orden de Devolucion",
        selection=[
            ("date desc, id desc", "Mas recientes primero"),
            ("date asc, id desc", "Mas antiguo primero"),
        ],
        default="date desc, id desc",
        required=True,
        help="Las devoluciones se realizarán buscando movimientos en el orden indicado.",
    )
    from_date = fields.Date(
        string="Buscar desde esta fecha",
    )
    picking_types = fields.Many2many(
        comodel_name="stock.picking.type",
        string="Tipo de Operaciones",
        help="Restringir los tipos de operaciones para buscar",
    )
    impresion = fields.Boolean(
        string="Impreso?"
    )
    state = fields.Selection(string="Estado",
        selection=[
            ("draft", "Abierto"),
            ("confirmed", "Confirmada"),
            ("done", "Hecho"),
            ("cancel", "Cancelado"),
        ],

        default="draft",
        tracking=True,
        compute="_compute_auto_state",
        copy=False,
        store=True,
    )
    returned_picking_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="ht_stock_return_request_id",
        string="Returned Pickings",
        readonly=True,
        copy=False,
    )
    to_refund = fields.Boolean()
    show_to_refund = fields.Boolean(
        compute="_compute_show_to_refund",
        help="Whether to show it or not depending on the availability of"
        "the stock_account module (so a bridge module is not necessary)",
    )
    line_ids = fields.One2many(
        comodel_name="ht.stock.return.request.line",
        inverse_name="request_id",
        string="Stock Return",
        copy=True,
    )
    note = fields.Text(
        string="Comments",
        help="They will be visible on the report",
    )
    
    invoice_ids = fields.Many2many(
        comodel_name="account.move",
        string="Notas de crédito",
        domain="[('move_type', 'in', ['out_refund', 'in_refund'])]",
        readonly=True,
    )

    has_credit_note = fields.Boolean(
        compute="_compute_has_credit_note",
        string="¿Tiene nota de crédito?",
    )
    
    package_unit = fields.Char(string="Unidad de Empaque")
    pickup_method = fields.Selection(
        [('own_truck', 'Camión Propio'),
        ('carrier', 'Transportadora'),
        ('building', 'Recoge en Edificio'),
        ('advisor', 'Asesor')],
        string="Recoger en",
    )
    invoice_reference = fields.Char(string="Cruzar con Factura")
    
    authorized = fields.Boolean(string="Autorizado")
    no_validate_history = fields.Boolean(string="No validar historial")
    
    estimated_total = fields.Monetary(
        string="Mercancia Asegurada por",
        currency_field='company_currency_id',
        compute="_compute_estimated_total",
        store=False,  # Opcional: no lo guardes si quieres que siempre sea dinámico
        help="Suma de (Precio actual del producto * Cantidad) de cada línea."
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id.id,
        readonly=True
    )

    product_count = fields.Integer(
        string="Cantidad de Productos",
        compute="_compute_product_count",
        store=True
    )
    
    def _prepare_return_vals_from_origin_move(self, origin_move, qty, uom=None):
        """Crea los vals para copiar un movimiento origen (componente o normal) como devolución."""
        return {
            "product_id": origin_move.product_id.id,
            "product_uom_qty": qty,
            "product_uom": (uom or origin_move.product_uom).id,
            "state": "draft",
            "location_id": self.return_from_location.id,
            "location_dest_id": self.return_to_location.id,
            "origin_returned_move_id": origin_move.id,
            "procure_method": "make_to_stock",
            "picking_id": False,
            **({"to_refund": self.to_refund} if self.show_to_refund else {}),
        }
    
    def _get_phantom_bom(self, product):
        return self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('type', '=', 'phantom')
        ], limit=1)
    
    @api.depends('line_ids')
    def _compute_product_count(self):
        for rec in self:
            rec.product_count = len(rec.line_ids)
        
    @api.depends('line_ids.product_id', 'line_ids.quantity')
    def _compute_estimated_total(self):
        for request in self:
            total = 0.0
            for line in request.line_ids:
                if line.product_id:
                    price = line.product_id.product_tmpl_id.list_price
                    total += (price or 0.0) * (line.quantity or 0.0)
            request.estimated_total = total
    
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('name', self.env['ir.sequence'].next_by_code('ht.stock.return.request'))
        default.setdefault('state', 'draft')
        default.setdefault('invoice_ids', False)
        default.setdefault('returned_picking_ids', False)
        default.setdefault('authorized', False)
        default.setdefault('no_validate_history', False)
        return super().copy(default)

    @api.constrains('return_type', 'package_unit', 'pickup_method')
    def _check_required_fields(self):
        for rec in self:
            if rec.return_type != 'supplier':
                if not rec.package_unit:
                    raise ValidationError("El campo 'Unidad de Empaque' es obligatorio si el tipo de devolución no es 'Proveedor'.")
                if not rec.pickup_method:
                    raise ValidationError("El campo 'Recoger en' es obligatorio si el tipo de devolución no es 'Proveedor'.")

    
    @api.depends('invoice_ids')
    def _compute_has_credit_note(self):
        for record in self:
            record.has_credit_note = bool(record.invoice_ids)
            
    @api.depends('returned_picking_ids.state')
    def _compute_auto_state(self):
        for record in self:
            # Solo cambia a done si está confirmado y todos los albaranes están en "done"
            if record.state == 'confirmed' and all(p.state == 'done' for p in record.returned_picking_ids):
                record.state = 'done'
            elif record.state not in ['done', 'cancel'] and record.returned_picking_ids:
                record.state = 'confirmed'

    def action_view_credit_notes(self):
        """Mostrar las notas de crédito relacionadas."""
        self.ensure_one()
        action = self.env.ref("account.action_move_out_refund_type").read()[0]
        action["domain"] = [("id", "in", self.invoice_ids.ids)]
        return action

    def action_create_credit_note(self):
        self.ensure_one()

        if self.state != 'done':
            raise UserError("La solicitud debe estar validada para crear la nota de crédito.")

        picking = self.returned_picking_ids.filtered(lambda p: p.state == "done")
        if not picking:
            raise UserError("No se encontró un albarán en estado hecho.")

        move_lines = picking.move_ids_without_package.filtered(lambda m: m.state == 'done')

        invoice_lines = []
        processed_kits = set()

        for line in self.line_ids:

            bom = self._get_phantom_bom(line.product_id)

            # ============================
            # 🔹 SI ES KIT
            # ============================
            if bom:

                if line.product_id.id in processed_kits:
                    continue

                processed_kits.add(line.product_id.id)

                # Buscar línea original de venta
                sale_line = False
                purchase_line = False

                for move in move_lines:
                    if move.origin_returned_move_id:
                        if move.origin_returned_move_id.sale_line_id:
                            sale_line = move.origin_returned_move_id.sale_line_id
                        if move.origin_returned_move_id.purchase_line_id:
                            purchase_line = move.origin_returned_move_id.purchase_line_id

                price_unit = 0.0
                taxes = False
                discount = 0.0

                if sale_line:
                    price_unit = sale_line.price_unit
                    taxes = [(6, 0, sale_line.tax_id.ids)]
                    discount = sale_line.discount

                elif purchase_line:
                    price_unit = purchase_line.price_unit
                    taxes = [(6, 0, purchase_line.taxes_id.ids)]
                    if hasattr(purchase_line, 'discount'):
                        discount = purchase_line.discount

                invoice_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'discount': discount,
                    'tax_ids': taxes,
                    'name': line.product_id.display_name,
                }))

            # ============================
            # 🔹 PRODUCTO NORMAL
            # ============================
            else:
                for move in move_lines.filtered(lambda m: m.product_id == line.product_id):

                    sale_line = move.origin_returned_move_id.sale_line_id
                    purchase_line = move.origin_returned_move_id.purchase_line_id

                    price_unit = 0.0
                    taxes = False
                    discount = 0.0

                    if sale_line:
                        price_unit = sale_line.price_unit
                        taxes = [(6, 0, sale_line.tax_id.ids)]
                        discount = sale_line.discount

                    elif purchase_line:
                        price_unit = purchase_line.price_unit
                        taxes = [(6, 0, purchase_line.taxes_id.ids)]
                        if hasattr(purchase_line, 'discount'):
                            discount = purchase_line.discount
                    else:
                        if self.return_type == 'customer':
                            taxes = [(6, 0, move.product_id.taxes_id.ids)]
                        else:
                            taxes = [(6, 0, move.product_id.supplier_taxes_id.ids)]

                    invoice_lines.append((0, 0, {
                        'product_id': move.product_id.id,
                        'quantity': sum(move.move_line_ids.mapped('qty_done')),
                        'price_unit': price_unit,
                        'discount': discount,
                        'tax_ids': taxes,
                        'name': move.name or move.product_id.name,
                    }))

        invoice_vals = {
            'move_type': 'out_refund' if self.return_type == 'customer' else 'in_refund',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'invoice_origin': self.name,
        }

        invoice = self.env['account.move'].create(invoice_vals)

        invoice.message_post(
            body="Nota de crédito creada desde solicitud de devolución: %s" % self.name
        )

        self.invoice_ids += invoice

        return {
            'type': 'ir.actions.act_window',
            'name': 'Nota de crédito',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.onchange("return_type", "partner_id")
    def onchange_locations(self):
        warehouse = self._default_warehouse_id()

        if self.return_type == "supplier":
            self.return_order = "date desc, id desc"
            
            # Ubicación destino: del proveedor
            self.return_to_location = self.partner_id.property_stock_supplier
            
            # Ubicación origen: del almacén, solo si no es interna
            if self.return_from_location.usage != "internal":
                self.return_from_location = warehouse.lot_stock_id.id
                
            # Picking types: Recibos del almacén YUMBO solamente
            self.picking_types = self.env['stock.picking.type'].search([
                ('name', 'ilike', 'Recibos'),
                ('warehouse_id.name', '=', 'YUMBO'),
            ])

        elif self.return_type == "customer":
            # 1️⃣ De dónde: ubicaciones de clientes (Partners/Customers)
            customer_location = self.env.ref("stock.stock_location_customers", raise_if_not_found=False)
            self.return_from_location = customer_location and customer_location.id or False

            # 2️⃣ Hacia dónde: ubicación DEV/Cliente/Transito Seleccion
            destino = self.env['stock.location'].search([
                ('name', '=', 'Transito Seleccion'),
                ('location_id.name', '=', 'Cliente'),
                ('location_id.location_id.name', '=', 'DEV'),
            ], limit=1)
            self.return_to_location = destino.id if destino else False

            # 3️⃣ Orden de devolución: Más antiguo primero
            self.return_order = "date desc, id desc"

            # 4️⃣ Picking types: los que contienen “Ordenes de entrega” o “Ordenes PdV”
            self.picking_types = self.env['stock.picking.type'].search([
                ('name', 'ilike', 'ordenes de entrega'),
                ('warehouse_id.name', 'in', ['YUMBO', 'CALI']),
            ]) | self.env['stock.picking.type'].search([
                ('name', 'ilike', 'ordenes pdv'),
                ('warehouse_id.name', 'in', ['YUMBO', 'CALI']),
            ])


            # 5️⃣ Dirección a recoger
            delivery_addresses = self.partner_id.child_ids.filtered(lambda c: c.type == 'delivery')
            self.pickup_address_id = delivery_addresses[:1] or self.partner_id

        elif self.return_type == "internal":
            self.partner_id = False
            if self.return_to_location.usage != "internal":
                self.return_to_location = warehouse.lot_stock_id.id
            if self.return_from_location.usage != "internal":
                self.return_from_location = warehouse.lot_stock_id.id

    @api.model
    def _default_warehouse_id(self):
        warehouse = self.env["stock.warehouse"].search(
            [
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        return warehouse

    def _compute_show_to_refund(self):
        self.show_to_refund = "to_refund" in self.env["stock.move"]._fields

    def _prepare_return_picking(self, picking_dict, moves):
        """Extend to add more values if needed"""
        picking_type = self.env["stock.picking.type"].browse(
            picking_dict.get("picking_type_id")
        )
        return_picking_type = (
            picking_type.return_picking_type_id or picking_type.return_picking_type_id
        )
        picking_dict.update(
            {
                "move_ids": [(6, 0, moves.ids)],
                "move_line_ids": [(6, 0, moves.mapped("move_line_ids").ids)],
                "picking_type_id": return_picking_type.id,
                "state": "draft",
                # "origin": _("Return of %s", picking_dict.get("origin")),
                "origin": self.name if self.no_validate_history else _("Return of %s" % picking_dict.get("origin")),
                "location_id": self.return_from_location.id,
                "location_dest_id": self.return_to_location.id,
                "ht_stock_return_request_id": self.id,
            }
        )
        return picking_dict

    def _create_picking(self, pickings, picking_moves):
        """Create return pickings with the proper moves"""
        return_pickings = self.env["stock.picking"]
        for picking in pickings:
            picking_dict = picking.copy_data(
                {
                    "origin": picking.name,
                    "printed": False,
                }
            )[0]
            
            if self.no_validate_history:
                # Si no hay historial, todos los movimientos deben ir al picking
                moves = picking_moves
            else:
                # Solo los que provienen del picking original
                moves = picking_moves.filtered(
                    lambda x, picking=picking: x.origin_returned_move_id.picking_id == picking
                )
            new_picking = return_pickings.create(
                self._prepare_return_picking(picking_dict, moves)
            )
            new_picking.message_post_with_source(
                "mail.message_origin_link",
                render_values={"self": new_picking, "origin": picking},
                subtype_id=self.env.ref("mail.mt_note").id,
            )
            return_pickings += new_picking
        return return_pickings

    def _prepare_move_default_values(self, line, qty, move):
        """Extend this method to add values to return move"""
        vals = {
            "product_id": line.product_id.id,
            "product_uom_qty": qty,
            "product_uom": line.product_uom_id.id,
            "state": "draft",
            "location_id": line.request_id.return_from_location.id,
            "location_dest_id": line.request_id.return_to_location.id,
            "origin_returned_move_id": move.id,
            "procure_method": "make_to_stock",
            "picking_id": False,
        }
        if self.show_to_refund:
            vals["to_refund"] = line.request_id.to_refund
        return vals

    def _prepare_move_line_values(self, line, return_move, qty, quant=False):
        """Extend to add values to the move lines with lots"""
        vals = {
            "product_id": line.product_id.id,
            "product_uom_id": line.product_uom_id.id,
            "lot_id": line.lot_id.id,
            "location_id": return_move.location_id.id,
            "location_dest_id": return_move.location_dest_id._get_putaway_strategy(
                line.product_id
            ).id
            or return_move.location_dest_id.id,
            "quantity": qty,
        }
        if not quant:
            return vals
        if line.request_id.return_type in ["internal", "customer"]:
            vals["location_dest_id"] = quant.location_id.id
        else:
            vals["location_id"] = quant.location_id.id
        return vals
    
    def action_confirm(self):
        self.ensure_one()

        # ✅ Validar condición: solo si es devolución de cliente
        if self.return_type == 'customer':
            for line in self.line_ids:
                if line.product_id.warranty_offered_by_supplier:
                    raise UserError(_(
                        "No se puede confirmar esta devolución porque el producto '%s' la garantia es directamente con el proveedor."
                    ) % line.product_id.display_name)

        if self.return_type != 'supplier':
            has_bueno = any(line.state_quality == 'good' for line in self.line_ids)
            if has_bueno and not self.authorized:
                raise UserError(_("No puede confirmar la devolución porque hay productos en estado 'Bueno' y no está autorizado."))

        if not self.line_ids:
            raise ValidationError(_("Debe agregar productos para devolver."))

        # 2️⃣ Validar historial si aplica
        if self.return_type in ['customer', 'supplier'] and not self.no_validate_history:
            for line in self.line_ids:
                bom = self._get_phantom_bom(line.product_id)

                # ✅ Para kit validamos por componentes, para normal validamos el mismo producto
                products_to_validate = bom.bom_line_ids.mapped('product_id') if bom else line.product_id

                for product in products_to_validate:
                    domain = [('state', '=', 'done'), ('product_id', '=', product.id)]

                    if self.return_type == 'customer':
                        domain += [
                            ('picking_id.picking_type_id.code', '=', 'outgoing'),
                            ('picking_id.partner_id', 'child_of', self.partner_id.id),
                        ]
                    else:
                        domain += [
                            ('picking_id.picking_type_id.code', '=', 'incoming'),
                            ('picking_id.partner_id', 'child_of', self.partner_id.id),
                        ]

                    if not self.env['stock.move'].search(domain, limit=1):
                        raise UserError(_(
                            "El producto %s no tiene historial con este contacto. "
                            "Solicite autorización o marque 'No validar historial'."
                        ) % product.display_name)

        Quant = self.env["stock.quant"]

        return_moves = self.env["stock.move"]
        done_moves = {}
        failed_moves = []

        # 3️⃣ Obtener movimientos retornables (incluye kits)
        returnable_moves = self.line_ids._get_returnable_move_ids() if not self.no_validate_history else {}

        for line in self.line_ids:
            bom = self._get_phantom_bom(line.product_id)

            # ==========================================================
            # ✅ KIT: NO crear moves manuales. Copiar moves ORIGINALES.
            # ==========================================================
            if bom and not self.no_validate_history:
                kit_moves = returnable_moves.get(line, [])
                if not kit_moves:
                    raise ValidationError(_(
                        "No se encontraron movimientos retornables para el kit %s."
                    ) % line.product_id.display_name)

                for qty, origin_move in kit_moves:
                    # origin_move es de COMPONENTE, y viene del picking real (OUT)
                    vals = self._prepare_return_vals_from_origin_move(origin_move, qty, uom=origin_move.product_uom)
                    return_move = origin_move.copy(vals)

                    return_move._action_confirm()
                    return_move._action_assign()

                    if return_move.state == "assigned":
                        return_move.quantity = qty
                        return_moves += return_move
                        line.returnable_move_ids += return_move
                    else:
                        failed_moves.append((line, return_move))
                continue

            # ==========================================================
            # ✅ KIT + NO VALIDAR HISTORIAL: aquí sí toca crear manual
            # (porque no hay origen). Mantengo tu lógica por componentes.
            # ==========================================================
            if bom and self.no_validate_history:
                for bom_line in bom.bom_line_ids:
                    component_qty = bom_line.product_qty * line.quantity

                    move = self.env['stock.move'].create({
                        'name': f'{self.name} - {bom_line.product_id.display_name}',
                        'product_id': bom_line.product_id.id,
                        'product_uom_qty': component_qty,
                        'product_uom': bom_line.product_id.uom_id.id,
                        'location_id': self.return_from_location.id,
                        'location_dest_id': self.return_to_location.id,
                        'state': 'draft',
                        'origin': self.name,
                        'procure_method': 'make_to_stock',
                    })
                    move._action_confirm()
                    move._action_assign()

                    return_moves += move
                    line.returnable_move_ids += move
                continue

            # ==========================================================
            # ✅ PRODUCTO NORMAL: tu flujo normal
            # ==========================================================
            if self.no_validate_history and not returnable_moves.get(line):
                move = self.env['stock.move'].create({
                    'name': f'{self.name} - {line.product_id.display_name}',
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_uom_id.id,
                    'location_id': self.return_from_location.id,
                    'location_dest_id': self.return_to_location.id,
                    'state': 'draft',
                    'picking_id': False,
                    'origin': self.name,
                    'procure_method': 'make_to_stock',
                })
                move._action_confirm()
                move._action_assign()
                return_moves += move
                line.returnable_move_ids += move
            else:
                for qty, origin_move in returnable_moves.get(line, []):
                    if origin_move not in done_moves:
                        vals = self._prepare_move_default_values(line, qty, origin_move)
                        return_move = origin_move.copy(vals)
                    else:
                        return_move = done_moves[origin_move]
                        return_move.product_uom_qty += qty

                    done_moves.setdefault(origin_move, self.env["stock.move"])
                    done_moves[origin_move] += return_move

                    if line.lot_id:
                        return_move.with_context(skip_assign_move=True)._action_confirm()
                        vals_list = []
                        if return_move.location_id.usage == "internal":
                            try:
                                quants = Quant._get_reserve_quantity(
                                    line.product_id,
                                    return_move.location_id,
                                    qty,
                                    lot_id=line.lot_id,
                                    strict=False,
                                )
                                for q in quants:
                                    vals_list.append((0, 0, self._prepare_move_line_values(line, return_move, q[1], q[0])))
                            except UserError:
                                failed_moves.append((line, return_move))
                        else:
                            vals_list.append((0, 0, self._prepare_move_line_values(line, return_move, qty)))

                        return_move.write({'move_line_ids': vals_list})
                        return_moves += return_move
                        line.returnable_move_ids += return_move
                    else:
                        return_move._action_confirm()
                        return_move._action_assign()
                        if return_move.state == "assigned":
                            return_move.quantity = qty
                            return_moves += return_move
                            line.returnable_move_ids += return_move
                        else:
                            failed_moves.append((line, return_move))
                            break

        # 4️⃣ Errores de reserva
        if failed_moves:
            failed_moves_str = "\n".join(
                "{}: {} {:.2f}".format(
                    x[0].product_id.display_name,
                    x[0].lot_id.name or "\t",
                    x[0].quantity,
                ) for x in failed_moves
            )
            raise ValidationError(_("No se pudo asignar el stock para estas devoluciones:\n%s") % failed_moves_str)

        # 5️⃣ Trazabilidad solo para movimientos con origen
        for move in return_moves.filtered(lambda m: m.origin_returned_move_id):
            origin_move = move.origin_returned_move_id
            move.write({
                "move_orig_ids": [(4, m.id) for m in origin_move.move_dest_ids.mapped("returned_move_ids") | origin_move],
                "move_dest_ids": [(4, m.id) for m in origin_move.move_orig_ids.mapped("returned_move_ids")],
            })

        # ✅ CLAVE: origin_pickings SOLO desde origin_returned_move_id (pickings reales)
        origin_pickings = return_moves.mapped("origin_returned_move_id.picking_id")

        # Si no hay origin_pickings, solo puede ser por NO_VALIDAR HISTORIAL
        if not origin_pickings:
            picking_type = self.picking_types[:1] or self.env['stock.picking.type'].search([
                ('code', '=', 'incoming' if self.return_type == 'supplier' else 'outgoing')
            ], limit=1)

            dummy_picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': self.return_from_location.id,
                'location_dest_id': self.return_to_location.id,
                'origin': self.name,
                'state': 'draft',
                'partner_id': self.partner_id.id,
            })
            origin_pickings = dummy_picking

        self.returned_picking_ids = self._create_picking(origin_pickings, return_moves)
        self.state = "confirmed"

    def action_validate(self):
        # check availability again not only on action_confirm
        self.line_ids._get_returnable_move_ids()
        self.returned_picking_ids.move_ids.picked = True
        self.returned_picking_ids._action_done()
        self.state = "done"

    def action_cancel_to_draft(self):
        """Set to draft again"""
        self.filtered(lambda x: x.state == "cancel").write({"state": "draft"})

    def action_cancel(self):
        """Cancel request and the associated pickings. We can set it to
        draft again."""
        self.filtered(lambda x: x.state == "draft").write({"state": "cancel"})
        confirmed = self.filtered(lambda x: x.state == "confirmed")
        for return_request in confirmed:
            return_request.mapped("returned_picking_ids").action_cancel()
            return_request.state = "cancel"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ht.stock.return.request"
                ) or _("New")
        return super().create(vals)

    @api.ondelete(at_uninstall=False)
    def _must_delete_request(self):
        for record in self:
            if record.state not in ['draft', 'cancel']:
                raise UserError(_("No se puede eliminar la solicitud porque no está en estado 'Abierto' o 'Cancelado'."))

    def action_view_pickings(self):
        """Display returned pickings"""
        xmlid = "stock.action_picking_tree_incoming"
        if self.return_type == "customer":
            xmlid = "stock.action_picking_tree_outgoing"
        elif self.return_type == "internal":
            xmlid = "stock.action_picking_tree_internal"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["context"] = {}
        pickings = self.returned_picking_ids
        if not pickings or len(pickings) > 1:
            action["domain"] = f"[('id', 'in', {pickings.ids})]"
        elif len(pickings) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            action["views"] = [(res and res.id or False, "form")]
            action["res_id"] = pickings.id
        return action

    def do_print_return_request(self):
        return self.env.ref(
            "stock_return_request_ht.action_report_stock_return_request"
        ).report_action(self)


class StockReturnRequestLine(models.Model):
    _name = "ht.stock.return.request.line"
    _description = "Product to search for returns"

    request_id = fields.Many2one(
        comodel_name="ht.stock.return.request",
        string="Return Request",
        ondelete="cascade",
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        domain=[("detailed_type", "in", ["product", "consu"])],
    )
    
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        related="product_id.uom_id",
        readonly=True,
    )
    tracking = fields.Selection(
        related="product_id.tracking",
        readonly=True,
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot / Serial",
        domain="[('product_id', '=', product_id)]",
    )
    quantity = fields.Float(
        string="Quantiy to return",
        digits="Product Unit of Measure",
        required=True,
    )
    max_quantity = fields.Float(
        string="Maximum available quantity",
        digits="Product Unit of Measure",
        compute="_compute_max_quantity",
    )
    returnable_move_ids = fields.Many2many(
        comodel_name="stock.move",
        string="Returnable Move Lines",
        copy=False,
        readonly=True,
    )
    
    state_quality = fields.Selection(
        [('good', 'Bueno'), ('bad', 'Malo')],
        string="Estado",
        required=True,
    )

    def _get_moves_domain(self):
        """Domain constructor for moves search"""
        self.ensure_one()
        domain = [
            ("state", "=", "done"),
            ("origin_returned_move_id", "=", False),
            ("product_id", "=", self.product_id.id),
        ]
        if not self.env.context.get("ignore_rr_lots"):
            domain += [("move_line_ids.lot_id", "=", self.lot_id.id)]
        if self.request_id.from_date:
            domain += [("date", ">=", self.request_id.from_date)]
        if self.request_id.picking_types:
            domain += [
                ("picking_id.picking_type_id", "in", self.request_id.picking_types.ids)
            ]
        return_type = self.request_id.return_type
        if return_type != "internal":
            domain += [
                (
                    "picking_id.partner_id",
                    "child_of",
                    self.request_id.partner_id.commercial_partner_id.id,
                )
            ]
        # Search for movements coming delivered to that location
        if return_type in ["internal", "customer"]:
            domain += [
                ("location_dest_id", "=", self.request_id.return_from_location.id)
            ]
        # Return to supplier. Search for moves that came from that location
        else:
            domain += [
                ("location_id", "child_of", self.request_id.return_to_location.id)
            ]
        return domain
    
    def _get_phantom_bom(self):
        return self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('type', '=', 'phantom')
        ], limit=1)

    def _get_returnable_move_ids(self):
        """
        Obtiene los movimientos de stock retornables.
        Soporta productos normales y kits (BoM phantom).
        """
        moves_for_return = {}
        stock_move_obj = self.env["stock.move"]

        for line in self.filtered("quantity"):

            moves_for_return[line] = []
            precision = line.product_uom_id.rounding

            bom = line._get_phantom_bom()

            # =====================================================
            # 🔹 CASO 1: PRODUCTO ES KIT (BoM Phantom)
            # =====================================================
            if bom:

                for bom_line in bom.bom_line_ids:

                    component = bom_line.product_id
                    component_qty_needed = bom_line.product_qty * line.quantity
                    qty_to_complete = component_qty_needed

                    # Construimos dominio igual al original pero para el componente
                    domain = [
                        ("state", "=", "done"),
                        ("origin_returned_move_id", "=", False),
                        ("product_id", "=", component.id),
                    ]

                    if not self.env.context.get("ignore_rr_lots"):
                        domain += [("move_line_ids.lot_id", "=", line.lot_id.id)]

                    if line.request_id.from_date:
                        domain += [("date", ">=", line.request_id.from_date)]

                    if line.request_id.picking_types:
                        domain += [
                            ("picking_id.picking_type_id",
                            "in",
                            line.request_id.picking_types.ids)
                        ]

                    return_type = line.request_id.return_type

                    if return_type != "internal":
                        domain += [
                            (
                                "picking_id.partner_id",
                                "child_of",
                                line.request_id.partner_id.commercial_partner_id.id,
                            )
                        ]

                    if return_type in ["internal", "customer"]:
                        domain += [
                            ("location_dest_id",
                            "=",
                            line.request_id.return_from_location.id)
                        ]
                    else:
                        domain += [
                            ("location_id",
                            "child_of",
                            line.request_id.return_to_location.id)
                        ]

                    moves = stock_move_obj.search(
                        domain,
                        order=line.request_id.return_order
                    )

                    moves = moves.filtered(lambda m: m.qty_returnable > 0.0)

                    for move in moves:

                        qty_available = move.qty_returnable
                        qty_to_return = min(qty_to_complete, qty_available)

                        if float_compare(
                            qty_to_return, 0.0,
                            precision_rounding=precision
                        ) > 0:

                            moves_for_return[line].append(
                                (qty_to_return, move)
                            )

                            qty_to_complete -= qty_to_return

                        if float_is_zero(
                            qty_to_complete,
                            precision_rounding=precision
                        ):
                            break

                    if qty_to_complete:
                        raise ValidationError(_(
                            "No hay suficientes movimientos para devolver el kit %s.\n"
                            "Faltan unidades del componente %s."
                        ) % (
                            line.product_id.display_name,
                            component.display_name,
                        ))

            # =====================================================
            # 🔹 CASO 2: PRODUCTO NORMAL (tu lógica original)
            # =====================================================
            else:

                moves = stock_move_obj.search(
                    line._get_moves_domain(),
                    order=line.request_id.return_order
                )

                moves = moves.filtered(lambda m: m.qty_returnable > 0.0)

                qty_to_complete = line.quantity

                for move in moves:

                    qty_returned = 0
                    return_moves = move.returned_move_ids.filtered(
                        lambda x: x.state == "done"
                    )

                    if return_moves:
                        qty_returned = sum(
                            return_moves.mapped("move_line_ids")
                            .filtered(lambda x, line=line: x.lot_id == line.lot_id)
                            .mapped("quantity")
                        )

                    quantity = sum(
                        move.mapped("move_line_ids")
                        .filtered(lambda x, line=line: x.lot_id == line.lot_id)
                        .mapped("quantity")
                    )

                    qty_remaining = quantity - qty_returned

                    if float_compare(
                        qty_remaining, 0.0,
                        precision_rounding=precision
                    ) > 0:

                        qty_to_return = min(qty_to_complete, qty_remaining)

                        moves_for_return[line] += [(qty_to_return, move)]
                        qty_to_complete -= qty_to_return

                    if float_is_zero(
                        qty_to_complete,
                        precision_rounding=precision
                    ):
                        break

                if qty_to_complete:
                    qty_found = line.quantity - qty_to_complete

                    if line.request_id.no_validate_history:
                        dummy_move = self.env['stock.move'].create({
                            'product_id': line.product_id.id,
                            'product_uom_qty': qty_to_complete,
                            'product_uom': line.product_uom_id.id,
                            'location_id': line.request_id.return_from_location.id,
                            'location_dest_id': line.request_id.return_to_location.id,
                            'name': f"Retorno sin historial - {line.product_id.display_name}",
                            'state': 'draft',
                            'picking_id': False,
                            'origin': line.request_id.name,
                        })

                        moves_for_return[line] += [
                            (qty_to_complete, dummy_move)
                        ]

                    else:
                        raise ValidationError(_(
                            "No hay suficientes movimientos para devolver este producto.\n"
                            "No fue posible encontrar movimientos suficientes para regresar "
                            "{line_quantity} {line_product_uom_id_name} "
                            "de {line_product_id_displayname}. "
                            "Un máximo de {qty_found} se puede devolver."
                        ).format(
                            line_quantity=line.quantity,
                            line_product_uom_id_name=line.product_uom_id.name,
                            line_product_id_displayname=line.product_id.display_name,
                            qty_found=qty_found,
                        ))

        return moves_for_return

    @api.model_create_multi
    def create(self, vals_list):
        new_records = super().create(vals_list)
        for record in new_records:
            existing = self.search_count(
                [
                    ("product_id", "=", record.product_id.id),
                    ("request_id.state", "in", ["draft", "confirm"]),
                    (
                        "request_id.return_from_location",
                        "=",
                        record.request_id.return_from_location.id,
                    ),
                    (
                        "request_id.return_to_location",
                        "=",
                        record.request_id.return_to_location.id,
                    ),
                    (
                        "request_id.partner_id",
                        "child_of",
                        record.request_id.partner_id.commercial_partner_id.id,
                    ),
                    ("lot_id", "=", record.lot_id.id),
                ]
            )
            if existing > 1:
                raise UserError(
                    _(
                        "No se pueden tener dos Solicitudes de Devolución de Acciones abiertas con el mismo "
                        "producto ({product_id}), locations ({return_from_location}, "
                        "{return_to_location}) contacto ({partner_id}) y lote.\n"
                        "Primero valide la primera solicitud de devolucion con este "
                        "producto antes de crear una nueva."
                    ).format(
                        product_id=record.product_id.display_name,
                        return_from_location=record.request_id.return_from_location.display_name,
                        return_to_location=record.request_id.return_to_location.display_name,
                        partner_id=record.request_id.partner_id.name,
                    )
                )
        return new_records

    @api.depends("product_id", "lot_id")
    def _compute_max_quantity(self):
        self.max_quantity = 0
        for line in self.filtered(lambda x: x.request_id.return_type != "customer"):
            request = line.request_id
            search_args = [
                ("location_id", "child_of", request.return_from_location.id),
                ("product_id", "=", line.product_id.id),
            ]
            if line.lot_id:
                search_args.append(("lot_id", "=", line.lot_id.id))
            else:
                search_args.append(("lot_id", "=", False))
            res = self.env["stock.quant"].read_group(search_args, ["quantity"], [])
            line.max_quantity = res[0]["quantity"]

    def action_lot_suggestion(self):
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        new_wizard = self.env["suggest.return.request.lot"].create(
            {"request_line_id": self.id}
        )
        moves = self.env["stock.move"].search(
            self.with_context(ignore_rr_lots=True)._get_moves_domain(),
            order=self.request_id.return_order,
        )
        suggested_lots_totals = {}
        suggested_lots_moves = {}
        vals_list = []
        for line in moves.move_line_ids:
            qty = line.move_id._get_lot_returnable_qty(line.lot_id)
            if float_compare(qty, 0, precision_digits=precision) > 0:
                suggested_lots_moves[line] = qty
                suggested_lots_totals.setdefault(line.lot_id, 0)
                suggested_lots_totals[line.lot_id] += qty
        for lot, qty in suggested_lots_totals.items():
            vals_list.append(
                {
                    "lot_id": lot.id,
                    "name": f"{lot.name} - {float_repr(qty, precision)}",
                    "lot_suggestion_mode": "sum",
                    "wizard_id": new_wizard.id,
                }
            )
        for move_line, qty in suggested_lots_moves.items():
            date_str = format_datetime(self.env, move_line.date, dt_format=None)
            name = (
                f"{date_str} - {move_line.lot_id.name} - "
                f"{move_line.reference} - {float_repr(qty, precision)}"
            )
            vals_list.append(
                {
                    "lot_id": move_line.lot_id.id,
                    "name": name,
                    "lot_suggestion_mode": "detail",
                    "wizard_id": new_wizard.id,
                }
            )
        if vals_list:
            self.env["ht.suggest.return.request.lot.line"].create(vals_list)
        return {
            "name": _("Suggest Lot"),
            "type": "ir.actions.act_window",
            "res_model": "suggest.return.request.lot",
            "view_mode": "form",
            "target": "new",
            "res_id": new_wizard.id,
        }
