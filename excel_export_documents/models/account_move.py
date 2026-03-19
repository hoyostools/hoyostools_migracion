from odoo import models
import xlsxwriter
import io
import base64
import tempfile
from PIL import Image


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _safe_insert_image(self, worksheet, row, col, image_base64):
        """
        Inserta una imagen en Excel de forma segura.
        Si la imagen está vacía, corrupta o inválida, NO rompe el Excel.
        """
        try:
            if not image_base64:
                raise ValueError("Sin imagen")

            image_data = base64.b64decode(image_base64)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as image_file:
                image_file.write(image_data)
                image_path = image_file.name

            img = Image.open(image_path)
            img.verify()

            img = Image.open(image_path)
            width, height = img.size

            max_height_px = 80
            max_width_px = 80
            x_scale = min(1, max_width_px / width)
            y_scale = min(1, max_height_px / height)

            worksheet.set_row(row, height * y_scale * 0.75)
            worksheet.set_column(col, col, width * x_scale * 0.14)

            worksheet.insert_image(row, col, image_path, {
                'x_scale': x_scale,
                'y_scale': y_scale,
                'x_offset': 2,
                'y_offset': 2
            })

        except Exception:
            worksheet.set_row(row, 20)
            worksheet.set_column(col, col, 15)
            worksheet.write(row, col, "Sin imagen")

    def action_export_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Facturas")

        headers = [
            "Cliente", "Identificación", "Dirección", "Número de Documento",
            "Referencia Interna", "Código de Barras", "Manufacturer Pref.",
            "Nombre Producto", "Categoría", "Cantidad",
            "Precio Unitario", "Impuesto (%)", "Descuento", "Subtotal", "Imagen"
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        row = 1

        for move in self:
            partner = move.partner_id

            for line in move.invoice_line_ids:
                product = line.product_id
                tax = line.tax_ids[:1]
                tax_amount = tax.amount if tax else ''

                worksheet.write(row, 0, partner.name or '')
                worksheet.write(row, 1, partner.vat or '')
                worksheet.write(row, 2, partner.contact_address or '')
                worksheet.write(row, 3, move.name or '')
                worksheet.write(row, 4, product.default_code or '')
                worksheet.write(row, 5, product.barcode or '')
                worksheet.write(row, 6, product.product_tmpl_id.manufacturer_pref or '')
                worksheet.write(row, 7, product.name or '')
                worksheet.write(row, 8, product.categ_id.name or '')
                worksheet.write(row, 9, line.quantity)
                worksheet.write(row, 10, line.price_unit)
                worksheet.write(row, 11, tax_amount)
                worksheet.write(row, 12, line.discount)
                worksheet.write(row, 13, line.price_subtotal)

                # 🔥 Imagen segura (NUNCA rompe el Excel)
                self._safe_insert_image(
                    worksheet=worksheet,
                    row=row,
                    col=14,
                    image_base64=product.image_128
                )

                row += 1

        workbook.close()
        output.seek(0)
        excel_data = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'Facturas.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': 'account.move',
            'res_id': self.ids[0] if len(self) == 1 else False,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
