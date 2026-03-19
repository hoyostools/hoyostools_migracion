from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController
from odoo.http import request, route

class StockBarcodeControllerInherit(StockBarcodeController):

    @route('/stock_barcode/get_barcode_data', type='json', auth='user')
    def get_barcode_data(self, model, res_id):
        data = super().get_barcode_data(model, res_id)

        if model == 'stock.picking':
            picking = request.env['stock.picking'].browse(res_id)

            if data['data'].get('records') and data['data']['records'].get('stock.picking'):
                data['data']['records']['stock.picking'][0]['cajas_maximas'] = str(picking.cantidad_maxima_cajas)

        return data
