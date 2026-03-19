# -*- coding: utf-8 -*-
import xmlrpc.client
from odoo import models, fields, _

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()

        for move in self:
            move.message_post(body="🔁 Iniciando proceso de sincronización de orden de compra.")

            if move.move_type != "out_invoice":
                move.message_post(body="⛔ No es una factura de cliente. Se omite.")
                continue

            if not move.partner_id:
                move.message_post(body="⛔ La factura no tiene cliente asociado.")
                continue

            main_partner = move.partner_id.commercial_partner_id
            
            if not main_partner.conexion_odoo:
                # No hacer absolutamente nada
                continue
            
            partner_name = (main_partner.display_name or "").strip()
            move.message_post(body=f"🔍 Cliente principal detectado: {partner_name}")

            remote = self.env["remote.instance"].sudo().search([("name", "=", partner_name)], limit=1)
            if not remote:
                move.message_post(body=f"❌ No se encontró una instancia remota con nombre '{partner_name}'.")
                continue

            move.message_post(body=f"🌐 Instancia remota seleccionada: {remote.name} ({remote.db})")

            try:
                common = xmlrpc.client.ServerProxy(f"{remote.url}/xmlrpc/2/common")
                uid = common.authenticate(remote.db, remote.username, remote.password, {})
                if not uid:
                    move.message_post(body="⛔ Error de autenticación en la base remota.")
                    continue

                models_proxy = xmlrpc.client.ServerProxy(f"{remote.url}/xmlrpc/2/object")
                move.message_post(body="✅ Conexión remota exitosa.")

                # Buscar proveedor nuestra empresa
                company_partner = move.company_id.partner_id.commercial_partner_id
                remote_supplier_ids = models_proxy.execute_kw(
                    remote.db, uid, remote.password,
                    "res.partner", "search",
                    [[("vat", "ilike", company_partner.vat)]],
                    {"limit": 1}
                )
                if not remote_supplier_ids:
                    move.message_post(body="❌ No se encontró el proveedor en la base remota.")
                    continue

                # Buscar proveedor "Distribuciones Hoyostools"
                hoyostools_ids = models_proxy.execute_kw(
                    remote.db, uid, remote.password,
                    "res.partner", "search",
                    [[("name", "ilike", "Distribuciones Hoyostools")]],
                    {"limit": 1}
                )
                if not hoyostools_ids:
                    move.message_post(body="❌ No se encontró el proveedor 'Distribuciones Hoyostools'.")
                    continue
                hoyostools_id = hoyostools_ids[0]

                order_lines = []

                for line in move.invoice_line_ids:
                    product = line.product_id

                    # Buscar el código del proveedor asignado a Hoyostools
                    seller = product.seller_ids.filtered(
                        lambda s: "distribuciones hoyostools" in (s.partner_id.name or "").lower()
                    )
                    product_code = seller.product_code if seller else product.default_code

                    if not product_code:
                        move.message_post(body=f"⚠️ Producto sin código proveedor válido: {line.display_name}")
                        continue

                    # Buscar producto remoto por product_code (solo eso) y seller_ids.partner_id ilike Hoyostools
                    remote_template_ids = models_proxy.execute_kw(
                        remote.db, uid, remote.password,
                        "product.template", "search",
                        [[
                            ("seller_ids.product_code", "=", product_code),
                            ("seller_ids.partner_id.name", "ilike", "Distribuciones Hoyostools")
                        ]],
                        {"limit": 1}
                    )

                    if remote_template_ids:
                        template = models_proxy.execute_kw(
                            remote.db, uid, remote.password,
                            "product.template", "read",
                            [remote_template_ids[0]], {"fields": ["product_variant_id"]}
                        )
                        remote_product_id = template[0]["product_variant_id"][0]
                    else:
                        # Crear producto si no existe
                        try:
                            remote_template_id = models_proxy.execute_kw(
                                remote.db, uid, remote.password,
                                "product.template", "create",
                                [{
                                    "name": product.name,
                                    "type": "consu",
                                    "creado_api": True,
                                    "barcode": product.barcode or False,
                                    "seller_ids": [(0, 0, {
                                        "partner_id": hoyostools_id,
                                        "product_code": product_code or "GEN"
                                    })]
                                }]
                            )

                            template = models_proxy.execute_kw(
                                remote.db, uid, remote.password,
                                "product.template", "read",
                                [remote_template_id], {"fields": ["product_variant_id"]}
                            )
                            remote_product_id = template[0]["product_variant_id"][0]
                            move.message_post(body=f"🆕 Producto creado en base remota con ID: {remote_product_id}")
                        except Exception as e:
                            move.message_post(body=f"❌ Error creando producto: {str(e)}")
                            continue

                    # Agregar línea
                    order_lines.append((0, 0, {
                        "name": line.name,
                        "product_id": remote_product_id,
                        "product_qty": line.quantity,
                        "price_unit": line.price_unit,
                        "discount": line.discount,
                        "date_planned": fields.Datetime.now(),
                    }))

                if not order_lines:
                    move.message_post(body="⛔ No hay líneas válidas para la orden.")
                    continue

                # Campaña
                remote_campaign_id = False
                if move.campaign_id:
                    try:
                        campaign_ids = models_proxy.execute_kw(
                            remote.db, uid, remote.password,
                            "utm.campaign", "search",
                            [[("name", "=", move.campaign_id.name)]],
                            {"limit": 1}
                        )
                        if campaign_ids:
                            remote_campaign_id = campaign_ids[0]
                        else:
                            remote_campaign_id = models_proxy.execute_kw(
                                remote.db, uid, remote.password,
                                "utm.campaign", "create",
                                [{"name": move.campaign_id.name}]
                            )
                    except Exception:
                        remote_campaign_id = False

                po_vals = {
                    "partner_id": remote_supplier_ids[0],
                    "order_line": order_lines,
                    "origin": move.ref or move.name,
                    "partner_ref": move.name,
                }

                if remote_campaign_id:
                    has_campaign_field = models_proxy.execute_kw(
                        remote.db, uid, remote.password,
                        "ir.model.fields", "search_count",
                        [[("model", "=", "purchase.order"), ("name", "=", "campaign_id")]]
                    )
                    if has_campaign_field:
                        po_vals["campaign_id"] = remote_campaign_id

                po_id = models_proxy.execute_kw(
                    remote.db, uid, remote.password,
                    "purchase.order", "create",
                    [po_vals]
                )

                move.message_post(body=_("✅ Orden de Compra creada en '%s' (ID %s).") % (remote.db, po_id))

            except Exception as e:
                move.message_post(body=_("❌ Error en sincronización con '%s': %s") % (remote.db, str(e)))

        return res
