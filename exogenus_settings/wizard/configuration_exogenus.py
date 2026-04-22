from odoo import fields, models, api
import io
import base64
import xlwt
from odoo.exceptions import ValidationError
from datetime import date
from collections import defaultdict

class GenerateExogenus(models.Model):
    _name = 'generate.exogenus'
    _description = 'Generate Exogenus'

    type_format_id = fields.Many2one('format.exogenus', string='Type Format')
    account_format_id = fields.Many2one('account.exogenus', string='account')
    description_id = fields.Char(
        string="Description", related='type_format_id.description_format')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="Start End")
    is_details = fields.Boolean(string="Detalles")

    def generate_report(self):
        wb = xlwt.Workbook()
        ws = wb.add_sheet(self.type_format_id.name, cell_overwrite_ok=True)

        # Conservar los encabezados originales
        original_headers = [column.name for column in self.type_format_id.column_ids]
        column_headers = original_headers.copy()
        column_indexes = {header: index for index, header in enumerate(column_headers)}

        # Escribir los encabezados
        for col, header in enumerate(column_headers):
            ws.write(1, col, header,
                     xlwt.easyxf('font: bold on, height 180; pattern: pattern solid, fore_colour grey25;'))

        # Escribir la descripción
        ws.write_merge(0, 0, 0, len(column_headers) - 1, self.description_id, xlwt.easyxf('font: bold on, height 200;'))
#FORMATO 1012
        if self.type_format_id.type_format == 'format_1012':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted'])
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Obtener el concepto y el tercero
                        concept_name = general_record.concept_id.name
                        partner_id = line.partner_id

                        # Calcular el saldo según el tipo de cuenta seleccionado
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[(concept_name, partner_id)][total_column_index] += total_value

            # Escribir datos en el archivo Excel
            row = 2
            for (concept_name, partner_id), data_dict in grouped_data.items():
                # Calcular el saldo total para el tercero
                total_saldo_tercero = sum(data_dict.values())

                # Omitir la fila si el saldo total es igual a 0
                if round(total_saldo_tercero) == 0:
                    continue

                # Escribir los datos del tercero y la cuenta
                if partner_id:
                    ws.write(row, 0, concept_name)
                    ws.write(row, 1, partner_id.document_type_id.code if partner_id.document_type_id else '')
                    ws.write(row, 2, partner_id.identification_document if partner_id.identification_document else '')
                    ws.write(row, 3,
                             '' if partner_id.document_type_id and partner_id.document_type_id.code == '13' else (
                                 partner_id.check_digit if partner_id.check_digit else ''))
                    ws.write(row, 4,
                             partner_id.lastname if partner_id.person_exo == '01' and partner_id.lastname else '')
                    ws.write(row, 5,
                             partner_id.lastname2 if partner_id.person_exo == '01' and partner_id.lastname2 else '')
                    ws.write(row, 6,
                             partner_id.firstname if partner_id.person_exo == '01' and partner_id.firstname else '')
                    ws.write(row, 7,
                             partner_id.othernames if partner_id.person_exo == '01' and partner_id.othernames else '')
                    ws.write(row, 8, partner_id.name if partner_id.person_exo == '02' and partner_id.name else '')
                    ws.write(row, 9, partner_id.country_id.code_dian if partner_id.country_id else '')
                else:
                    ws.write(row, 8, 'NINGUNO')

                # Escribir los saldos en las columnas correspondientes
                for column_index, total_balance in data_dict.items():
                    # Redondear el saldo al entero más cercano y obtener su valor absoluto
                    rounded_positive_balance = abs(round(total_balance))
                    # Si el saldo es 0, omitir la columna
                    if rounded_positive_balance == 0:
                        continue
                    # Escribir el saldo redondeado y positivo en la columna correspondiente
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1
#FORMATO 1011
        if self.type_format_id.type_format == 'format_1011':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted'])
                    ])

                    # Diccionario para almacenar los datos agrupados solo por concepto
                    grouped_data = defaultdict(lambda: defaultdict(float))

                    # Recorrer los apuntes contables
                    for line in move_lines:
                        concept_name = general_record.concept_id.name

                        # Calcular el saldo
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Agrupar solo por concepto
                        grouped_data[concept_name][total_column_index] += total_value

            row = 2
            for concept_name, data_dict in grouped_data.items():
                total_saldo = sum(data_dict.values())

                if round(total_saldo) == 0:
                    continue

                ws.write(row, 0, concept_name)  # Solo se escribe el nombre del concepto

                for column_index, total_balance in data_dict.items():
                    rounded_positive_balance = abs(round(total_balance))
                    if rounded_positive_balance == 0:
                        continue
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1

        #FORMATO 1009
        if self.type_format_id.type_format == 'format_1009':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted'])
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Obtener el concepto y el tercero
                        concept_name = general_record.concept_id.name
                        partner_id = line.partner_id

                        # Calcular el saldo según el tipo de cuenta seleccionado
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[(concept_name, partner_id)][total_column_index] += total_value

            # Escribir datos en el archivo Excel
            row = 2
            for (concept_name, partner_id), data_dict in grouped_data.items():
                # Calcular el saldo total para el tercero
                total_saldo_tercero = sum(data_dict.values())

                # Omitir la fila si el saldo total es igual a 0
                if round(total_saldo_tercero) == 0:
                    continue

                # Escribir los datos del tercero y la cuenta
                if partner_id:
                    ws.write(row, 0, concept_name)
                    ws.write(row, 1, partner_id.document_type_id.code if partner_id.document_type_id else '')
                    ws.write(row, 2, partner_id.identification_document if partner_id.identification_document else '')
                    ws.write(row, 3,
                             '' if partner_id.document_type_id and partner_id.document_type_id.code == '13' else (
                                 partner_id.check_digit if partner_id.check_digit else ''))
                    ws.write(row, 4,
                             partner_id.lastname if partner_id.person_exo == '01' and partner_id.lastname else '')
                    ws.write(row, 5,
                             partner_id.lastname2 if partner_id.person_exo == '01' and partner_id.lastname2 else '')
                    ws.write(row, 6,
                             partner_id.firstname if partner_id.person_exo == '01' and partner_id.firstname else '')
                    ws.write(row, 7,
                             partner_id.othernames if partner_id.person_exo == '01' and partner_id.othernames else '')
                    ws.write(row, 8, partner_id.name if partner_id.person_exo == '02' and partner_id.name else '')
                    ws.write(row, 9, partner_id.street if partner_id.street else (
                        partner_id.field_1 if partner_id.field_1 else ''))
                    ws.write(row, 11, partner_id.zip_id.dian_code[
                                      -3:] if partner_id.zip_id and partner_id.zip_id.dian_code else '')
                    ws.write(row, 10, partner_id.zip_id.dian_code[
                                      :2] if partner_id.zip_id and partner_id.zip_id.dian_code else '')
                    ws.write(row, 12, partner_id.country_id.code_dian if partner_id.country_id else '')
                else:
                    ws.write(row, 8, 'NINGUNO')

                # Escribir los saldos en las columnas correspondientes
                for column_index, total_balance in data_dict.items():
                    # Redondear el saldo al entero más cercano y obtener su valor absoluto
                    rounded_positive_balance = round(total_balance)
                    # Si el saldo es 0, omitir la columna
                    if rounded_positive_balance == 0:
                        continue
                    # Escribir el saldo redondeado y positivo en la columna correspondiente
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1
                # Hoja de detalle con movimientos contables


        # FORMATO 1008
        if self.type_format_id.type_format == 'format_1008':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(list))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted', 'reconciled'])
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Calcular el saldo según la opción seleccionada
                        total_account_type = general_record.total_account
                        if total_account_type == 'debit':
                            total_value = line.debit
                        elif total_account_type == 'credit':
                            total_value = line.credit
                        elif total_account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif total_account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif total_account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[general_record.concept_id.name][line.partner_id.id].append({
                            'document_type_code': line.partner_id.document_type_id.code if line.partner_id.document_type_id else '',
                            'identification_document': line.partner_id.identification_document if line.partner_id.identification_document else '',
                            'check_digit': '' if line.partner_id.document_type_id and line.partner_id.document_type_id.code == '13' else (
                                line.partner_id.check_digit if line.partner_id.check_digit else ''),
                            'lastname': line.partner_id.lastname if line.partner_id.person_exo == '01' and line.partner_id.lastname else '',
                            'firstname': line.partner_id.firstname if line.partner_id.person_exo == '01' and line.partner_id.firstname else '',
                            'lastname2': line.partner_id.lastname2 if line.partner_id.person_exo == '01' and line.partner_id.lastname2 else '',
                            'othernames': line.partner_id.othernames if line.partner_id.person_exo == '01' and line.partner_id.othernames else '',
                            'name': line.partner_id.name if line.partner_id.person_exo == '02' and line.partner_id.name else '',
                            'country': line.partner_id.country_id.code_dian if line.partner_id.country_id else '',
                            'zip_id': line.partner_id.zip_id.dian_code[
                                      -3:] if line.partner_id.zip_id and line.partner_id.zip_id.dian_code else '',
                            'dpto': line.partner_id.zip_id.dian_code[
                                    :2] if line.partner_id.zip_id and line.partner_id.zip_id.dian_code else '',
                            'street': line.partner_id.street if line.partner_id.street else (
                                line.partner_id.field_1 if line.partner_id.field_1 else ''),
                            'total_value': total_value
                        })

            # Escribir datos en el archivo Excel
            row = 2
            for concept, partner_data in grouped_data.items():
                for partner_id, data_list in partner_data.items():
                    # Calcular el saldo total y redondearlo
                    total_balance = sum(data['total_value'] for data in data_list)
                    rounded_total_balance = round(total_balance)

                    # Si el saldo total redondeado es 0, omitir esta fila
                    if rounded_total_balance == 0:
                        continue

                    # Tomar los datos del primer apunte
                    partner_data = data_list[0]

                    # Escribir los datos del tercero y la cuenta
                    ws.write(row, 0, concept)  # Concepto
                    if partner_id:
                        ws.write(row, 1, str(partner_data['document_type_code']))
                        ws.write(row, 2, str(partner_data['identification_document']))
                        ws.write(row, 3, str(partner_data['check_digit']))
                        ws.write(row, 4, str(partner_data['lastname']))
                        ws.write(row, 5, str(partner_data['lastname2']))
                        ws.write(row, 6, str(partner_data['firstname']))
                        ws.write(row, 7, str(partner_data['othernames']))
                        ws.write(row, 8, str(partner_data['name']))
                        ws.write(row, 9, str(partner_data['street']))  # Dirección como string
                        ws.write(row, 10, str(partner_data['dpto']))  # Departamento como string
                        ws.write(row, 11, str(partner_data['zip_id']))  # Código postal como string
                        ws.write(row, 12, str(partner_data['country']))  # País como string
                    # Escribir el país aquí
                    else:
                        ws.write(row, 8, 'NINGUNO')

                    # Escribir el saldo total redondeado en la celda correspondiente
                    ws.write(row, 13, rounded_total_balance)

                    row += 1

        # FORMATO 1007
        if self.type_format_id.type_format == 'format_1007':
            ws2 = wb.add_sheet('Detalle movimientos', cell_overwrite_ok=True)
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', '=', 'posted')
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Obtener el concepto y el tercero
                        concept_name = general_record.concept_id.name
                        partner_id = line.partner_id

                        # Calcular el saldo según el tipo de cuenta seleccionado
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[(concept_name, partner_id)][total_column_index] += total_value

            # Escribir datos en el archivo Excel
            row = 2
            for (concept_name, partner_id), data_dict in grouped_data.items():
                # Verificar si todos los saldos son cero
                if all(abs(round(total_balance)) == 0 for total_balance in data_dict.values()):
                    continue  # Saltar este registro si todos los saldos son cero

                # Escribir los datos del tercero y la cuenta
                if partner_id:
                    ws.write(row, 0, concept_name)
                    ws.write(row, 1, partner_id.document_type_id.code if partner_id.document_type_id else '')
                    ws.write(row, 2, partner_id.identification_document if partner_id.identification_document else '')
                    ws.write(row, 3,
                             partner_id.lastname if partner_id.person_exo == '01' and partner_id.lastname else '')
                    ws.write(row, 4,
                             partner_id.lastname2 if partner_id.person_exo == '01' and partner_id.lastname2 else '')
                    ws.write(row, 5,
                             partner_id.firstname if partner_id.person_exo == '01' and partner_id.firstname else '')
                    ws.write(row, 6,
                             partner_id.othernames if partner_id.person_exo == '01' and partner_id.othernames else '')
                    ws.write(row, 7, partner_id.name if partner_id.person_exo == '02' and partner_id.name else '')
                    ws.write(row, 8,
                             partner_id.country_id.code_dian if partner_id.country_id and partner_id.country_id.code_dian else '')
                else:
                    # Buscar el nombre del primer apunte
                    first_line_name = 'NINGUNO'
                    ws.write(row, 7, first_line_name)

                # Escribir los saldos en las columnas correspondientes
                for column_index, total_balance in data_dict.items():
                    # Redondear el saldo al entero más cercano y obtener su valor absoluto
                    rounded_positive_balance = round(total_balance)
                    # Escribir el saldo redondeado y positivo en la columna correspondiente
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1


#FORMATO 1006
        if self.type_format_id.type_format == 'format_1006':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted'])
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Obtener el concepto y el tercero
                        concept_name = general_record.concept_id.name
                        partner_id = line.partner_id

                        # Calcular el saldo según el tipo de cuenta seleccionado
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[(concept_name, partner_id)][total_column_index] += total_value

            # Escribir datos en el archivo Excel
            row = 2
            for (concept_name, partner_id), data_dict in grouped_data.items():
                # Verificar si todos los saldos son cero
                if all(abs(round(total_balance)) == 0 for total_balance in data_dict.values()):
                    continue  # Saltar este registro si todos los saldos son cero

                # Escribir los datos del tercero y la cuenta
                if partner_id:
                    ws.write(row, 0, partner_id.document_type_id.code if partner_id.document_type_id else '')
                    ws.write(row, 1, partner_id.identification_document if partner_id.identification_document else '')
                    ws.write(row, 2,
                             '' if partner_id.document_type_id and partner_id.document_type_id.code == '13' else (
                                 partner_id.check_digit if partner_id.check_digit else ''))
                    ws.write(row, 3,
                             partner_id.lastname if partner_id.person_exo == '01' and partner_id.lastname else '')
                    ws.write(row, 4,
                             partner_id.lastname2 if partner_id.person_exo == '01' and partner_id.lastname2 else '')
                    ws.write(row, 5,
                             partner_id.firstname if partner_id.person_exo == '01' and partner_id.firstname else '')
                    ws.write(row, 6,
                             partner_id.othernames if partner_id.person_exo == '02' and partner_id.othernames else '')
                    ws.write(row, 7, partner_id.name if partner_id.name else '')
                else:
                    # Buscar el nombre del primer apunte
                    first_line_name = 'NINGUNO'
                    ws.write(row, 7, first_line_name)

                # Escribir los saldos en las columnas correspondientes
                for column_index, total_balance in data_dict.items():
                    # Redondear el saldo al entero más cercano y obtener su valor absoluto
                    rounded_positive_balance = round(total_balance)
                    # Escribir el saldo redondeado y positivo en la columna correspondiente
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1

        #FORMATO 1005
        if self.type_format_id.type_format == 'format_1005':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted'])
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Obtener el concepto y el tercero
                        concept_name = general_record.concept_id.name
                        partner_id = line.partner_id

                        # Calcular el saldo según el tipo de cuenta seleccionado
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[(concept_name, partner_id)][total_column_index] += total_value

            # Escribir datos en el archivo Excel
            row = 2
            for (concept_name, partner_id), data_dict in grouped_data.items():
                # Verificar si todos los saldos son cero
                if all(abs(round(total_balance)) == 0 for total_balance in data_dict.values()):
                    continue  # Saltar este registro si todos los saldos son cero

                # Escribir los datos del tercero y la cuenta
                if partner_id:
                    ws.write(row, 0,
                             partner_id.document_type_id.code if partner_id.document_type_id and partner_id.document_type_id.code else '')
                    ws.write(row, 1, partner_id.identification_document if partner_id.identification_document else '')
                    ws.write(row, 2,
                             '' if partner_id.document_type_id and partner_id.document_type_id.code == '13' else partner_id.check_digit if partner_id.document_type_id and partner_id.document_type_id.code != '13' else '')
                    ws.write(row, 3, partner_id.lastname if partner_id.person_exo == '01' else '')
                    ws.write(row, 4, partner_id.lastname2 if partner_id.person_exo == '01' else '')
                    ws.write(row, 5, partner_id.firstname if partner_id.person_exo == '01' else '')
                    ws.write(row, 6, partner_id.othernames if partner_id.person_exo == '02' and partner_id.othernames else '')
                    ws.write(row, 7, partner_id.name if partner_id.person_exo else '')
                else:
                    # Buscar el nombre del primer apunte
                    first_line_name = 'NINGUNO'
                    ws.write(row, 7, first_line_name)

                # Escribir los saldos en las columnas correspondientes
                for column_index, total_balance in data_dict.items():
                    # Redondear el saldo al entero más cercano y obtener su valor absoluto
                    rounded_positive_balance = abs(round(total_balance))
                    # Escribir el saldo redondeado y positivo en la columna correspondiente
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1

        #FORMATO 1004
        if self.type_format_id.type_format == 'format_1004':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted'])
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Obtener el concepto y el tercero
                        concept_name = general_record.concept_id.name
                        partner_id = line.partner_id

                        # Calcular el saldo según el tipo de cuenta seleccionado
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[(concept_name, partner_id)][total_column_index] += total_value

            # Escribir datos en el archivo Excel
            row = 2
            for (concept_name, partner_id), data_dict in grouped_data.items():
                # Escribir los datos del tercero y la cuenta
                if partner_id:
                    ws.write(row, 0, partner_id.document_type_id.code if partner_id.document_type_id else '')
                    ws.write(row, 1, partner_id.identification_document)
                    ws.write(row, 2, partner_id.lastname if partner_id.person_exo == '01' else '')
                    ws.write(row, 3, partner_id.lastname2 if partner_id.person_exo == '01' else '')
                    ws.write(row, 4, partner_id.firstname if partner_id.person_exo == '01' else '')
                    ws.write(row, 5, partner_id.othernames if partner_id.person_exo == '01' else '')
                    ws.write(row, 6, partner_id.name if partner_id.person_exo == '02' else '')
                    ws.write(row, 7, partner_id.street if partner_id.street else (partner_id.field_1 if partner_id.field_1 else ''))
                    ws.write(row, 8, partner_id.country_id.code_dian if partner_id.country_id else '')
                    ws.write(row, 9, partner_id.zip_id.dian_code[-3:] if partner_id.zip_id and partner_id.zip_id.dian_code else '',)
                    ws.write(row, 10, partner_id.email if partner_id.email  else '')
                else:
                    # Buscar el nombre del primer apunte
                    first_line_name = 'NINGUNO'
                    ws.write(row, 7, first_line_name)

                # Escribir los saldos en las columnas correspondientes
                for column_index, total_balance in data_dict.items():
                    # Redondear el saldo al entero más cercano y obtener su valor absoluto
                    rounded_positive_balance = abs(round(total_balance))
                    # Escribir el saldo redondeado y positivo en la columna correspondiente
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1
#FORMATO 1003
        if self.type_format_id.type_format == 'format_1003':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener el tipo de cuenta asociado al registro general
                    account_type = general_record.total_account

                    # Obtener el índice de la columna correspondiente al tipo de cuenta
                    total_column_index = column_indexes.get(general_record.column_id.name, None)

                    # Obtener los movimientos de la cuenta en el rango de fechas
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.account_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('move_id.state', 'in', ['posted'])
                    ])

                    # Recorrer los apuntes contables de la cuenta
                    for line in move_lines:
                        # Obtener el concepto y el tercero
                        concept_name = general_record.concept_id.name
                        partner_id = line.partner_id

                        # Calcular el saldo según el tipo de cuenta seleccionado
                        if account_type == 'debit':
                            total_value = line.debit
                        elif account_type == 'credit':
                            total_value = line.credit
                        elif account_type == 'deb_cre':
                            total_value = line.debit - line.credit
                        elif account_type == 'cre_deb':
                            total_value = line.credit - line.debit
                        elif account_type == 'total':
                            total_value = line.balance

                        # Actualizar los datos agrupados por concepto y tercero
                        grouped_data[(concept_name, partner_id)][total_column_index] += total_value

            # Escribir datos en el archivo Excel
            row = 2
            for (concept_name, partner_id), data_dict in grouped_data.items():
                # Escribir los datos del tercero y la cuenta
                if partner_id:
                    ws.write(row, 0, concept_name)
                    ws.write(row, 1, partner_id.document_type_id.code if partner_id.document_type_id else '')
                    ws.write(row, 2, partner_id.identification_document)
                    ws.write(row, 3, '' if partner_id.document_type_id.code == '13' else partner_id.check_digit if partner_id.document_type_id.code != '13' else '')
                    ws.write(row, 4, partner_id.lastname if partner_id.person_exo == '01' else '')
                    ws.write(row, 5, partner_id.lastname2 if partner_id.person_exo == '01' else '')
                    ws.write(row, 6, partner_id.firstname if partner_id.person_exo == '01' else '')
                    ws.write(row, 7, partner_id.othernames if partner_id.person_exo == '01' else '')
                    ws.write(row, 8, partner_id.name if partner_id.person_exo == '02' else '')
                    ws.write(row, 9, partner_id.street if partner_id.street else ( partner_id.field_1 if partner_id.field_1 else ''))
                    ws.write(row, 11, partner_id.zip_id.dian_code[-3:] if partner_id.zip_id and partner_id.zip_id.dian_code else '')
                    ws.write(row, 10, partner_id.zip_id.dian_code[:2] if partner_id.zip_id and partner_id.zip_id.dian_code else '' )
                else:
                    # Buscar el nombre del primer apunte
                    first_line_name = 'NINGUNO'
                    ws.write(row, 7, first_line_name)

                # Escribir los saldos en las columnas correspondientes
                for column_index, total_balance in data_dict.items():
                    # Redondear el saldo al entero más cercano y obtener su valor absoluto
                    rounded_positive_balance = abs(round(total_balance))
                    # Escribir el saldo redondeado y positivo en la columna correspondiente
                    ws.write(row, column_index, rounded_positive_balance)

                row += 1
# FORMATO 1001
        if self.type_format_id.type_format == 'format_1001':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id
            # Diccionario para almacenar los datos agrupados por concepto y tercero
            grouped_data = defaultdict(lambda: defaultdict(int))
            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener el concepto
                concept = general_record.concept_id.name
                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    # Obtener los diarios exógena específicos para esta cuenta
                    exogena_journals = general_record.exogena_journal_ids
                    exogena_journal_ids = tuple(journal.id for journal in exogena_journals)

                    if exogena_journal_ids:
                        # Consulta SQL con filtrado por diarios exógena
                        query = """
                                SELECT DISTINCT
                                    rdt.code AS document_type_id,
                                    rpd.identification_document,
                                    rpd.lastname,
                                    rpd.lastname2,
                                    rpd.firstname,
                                    rpd.othernames,
                                    rpd.name,
                                    rpd.street,
                                    rcs.dian_code AS zip_dian_code,
                                    rc.code_dian AS country_code_dian,
                                    aml.account_id,
                                    SUM(CASE 
                                        WHEN %s = 'debit' THEN aml.debit
                                        WHEN %s = 'credit' THEN aml.credit
                                        WHEN %s = 'deb_cre' THEN aml.debit - aml.credit
                                        WHEN %s = 'cre_deb' THEN aml.credit - aml.debit
                                        WHEN %s = 'total' THEN aml.balance
                                        ELSE 0 END) AS total_balance
                                FROM
                                    account_move_line aml
                                LEFT JOIN
                                    res_partner rpd ON aml.partner_id = rpd.id
                                LEFT JOIN
                                    res_country rc ON rpd.country_id = rc.id
                                LEFT JOIN
                                    res_city_zip rcs ON rpd.zip_id = rcs.id  
                                LEFT JOIN
                                    res_partner_document_type rdt ON rpd.document_type_id = rdt.id       
                                WHERE
                                    aml.account_id = %s
                                    AND aml.date >= %s
                                    AND aml.date <= %s
                                    AND aml.journal_id IN %s
                                    AND aml.move_id IN (
                                        SELECT id
                                        FROM account_move
                                        WHERE state = 'posted'
                                    )
                                 GROUP BY
                                    rdt.code,
                                    rpd.identification_document,
                                    rpd.lastname,
                                    rpd.lastname2,
                                    rpd.firstname,
                                    rpd.othernames,
                                    rpd.name,
                                    rpd.street,
                                    rcs.dian_code, 
                                    rc.code_dian,
                                    aml.account_id
                                """
                        params = (
                            general_record.total_account, general_record.total_account,
                            general_record.total_account,
                            general_record.total_account, general_record.total_account, account.account_id.id,
                            self.start_date,
                            self.end_date, exogena_journal_ids)
                    else:
                        # Consulta SQL sin filtrado por diarios exógena
                        query = """
                                SELECT DISTINCT
                                    rdt.code AS document_type_id,
                                    rpd.identification_document,
                                    rpd.lastname,
                                    rpd.lastname2,
                                    rpd.firstname,
                                    rpd.othernames,
                                    rpd.name,
                                    rpd.street,
                                    rcs.dian_code AS zip_dian_code,
                                    rc.code_dian AS country_code_dian,
                                    aml.account_id,
                                    SUM(CASE 
                                        WHEN %s = 'debit' THEN aml.debit
                                        WHEN %s = 'credit' THEN aml.credit
                                        WHEN %s = 'deb_cre' THEN aml.debit - aml.credit
                                        WHEN %s = 'cre_deb' THEN aml.credit - aml.debit
                                        WHEN %s = 'total' THEN aml.balance
                                        ELSE 0 END) AS total_balance
                                FROM
                                    account_move_line aml
                                LEFT JOIN
                                    res_partner rpd ON aml.partner_id = rpd.id
                                LEFT JOIN
                                    res_country rc ON rpd.country_id = rc.id
                                LEFT JOIN
                                    res_city_zip rcs ON rpd.zip_id = rcs.id     
                                LEFT JOIN
                                    res_partner_document_type rdt ON rpd.document_type_id = rdt.id           
                                WHERE
                                    aml.account_id = %s
                                    AND aml.date >= %s
                                    AND aml.date <= %s
                                    AND aml.move_id IN (
                                        SELECT id
                                        FROM account_move
                                        WHERE state = 'posted'
                                    )
                               GROUP BY
                                rdt.code,
                                rpd.identification_document,
                                rpd.lastname,
                                rpd.lastname2,
                                rpd.firstname,
                                rpd.othernames,
                                rpd.name,
                                rpd.street,
                                rcs.dian_code, 
                                rc.code_dian,
                                aml.account_id

                            """
                        params = (
                            general_record.total_account, general_record.total_account,
                            general_record.total_account,
                            general_record.total_account, general_record.total_account, account.account_id.id,
                            self.start_date,
                            self.end_date)

                    # Ejecutar la consulta SQL
                    self._cr.execute(query, params)
                    query_results = self._cr.fetchall()
                    # Agregar los resultados a grouped_data y asignar los valores adicionales
                    for result in query_results:
                        document_type_id, identification_document, lastname, lastname2, firstname, othernames, name, street, zip_dian_code, country_code_dian, account_id, total_balance = result

                        partner_person_exo = self.env['res.partner'].search([('name', '=', result[6])], limit=1)
                        person_exo = False

                        if partner_person_exo:
                            person_exo = partner_person_exo.person_exo

                        # Redondear el saldo antes de agregarlo al diccionario agrupado por tercero y concepto
                        total_balance_rounded = round(total_balance, 2)

                        # Agregar el saldo al diccionario agrupado por tercero y concepto
                        grouped_data[(name, concept)]['total_balance'] += total_balance_rounded

                        # Asignar los valores a cada registro dentro de grouped_data
                        grouped_data[(name, concept)]['document_type_id'] = document_type_id
                        grouped_data[(name, concept)]['identification_document'] = identification_document

                        if person_exo == '01':  # Persona Natural
                            grouped_data[(name, concept)]['lastname'] = lastname
                            grouped_data[(name, concept)]['lastname2'] = lastname2
                            grouped_data[(name, concept)]['firstname'] = firstname
                            grouped_data[(name, concept)]['othernames'] = othernames
                        elif person_exo == '02':  # Persona Juridica
                            grouped_data[(name, concept)]['name'] = name

                        grouped_data[(name, concept)]['street'] = street
                        grouped_data[(name, concept)]['zip_dian_code'] = zip_dian_code
                        grouped_data[(name, concept)]['country_code_dian'] = country_code_dian
                        # Verificar si la columna es "Pago o abono en cuenta deducible", "Pago o abono en cuenta NO deducible", "IVA mayor valor del costo o gasto. deducible", "IVA mayor valor del costo o gasto no deducible", "Retención en la fuente practicada Renta", "Retención en la fuente asumida Renta", "Retención en la fuente practicada IVA Régimen común" o "Retención en la fuente practicada IVA no domiciliados"
                        for column in general_record.column_id:
                            if column.name == 'Pago o abono en cuenta deducible':
                                grouped_data[(name, concept)]['deducible_balance'] += total_balance_rounded
                            elif column.name == 'Pago o abono en cuenta NO deducible':
                                grouped_data[(name, concept)]['no_deducible_balance'] += total_balance_rounded
                            elif column.name == 'IVA mayor valor del costo o gasto. deducible':
                                grouped_data[(name, concept)]['iva_deducible_balance'] += total_balance_rounded
                            elif column.name == 'IVA mayor valor del costo o gasto no deducible':
                                grouped_data[(name, concept)][
                                    'iva_no_deducible_balance'] += total_balance_rounded
                            elif column.name == 'Retención en la fuente practicada Renta':
                                grouped_data[(name, concept)][
                                    'retencion_renta_balance'] += total_balance_rounded
                            elif column.name == 'Retención en la fuente asumida Renta':
                                grouped_data[(name, concept)][
                                    'retencion_asumida_renta_balance'] += total_balance_rounded
                            elif column.name == 'Retención en la fuente practicada IVA Régimen común':
                                grouped_data[(name, concept)][
                                    'retencion_iva_regimen_comun_balance'] += total_balance_rounded
                            elif column.name == 'Retención en la fuente practicada IVA no domiciliados':
                                grouped_data[(name, concept)][
                                    'retencion_iva_no_domiciliados_balance'] += total_balance_rounded
            # Escribir datos en el archivo Excel
            row = 2
            for (name, concept), data_dict in grouped_data.items():
                ws.write(row, 0, concept)
                ws.write(row, 1, data_dict.get('document_type_id', ''))
                ws.write(row, 2, data_dict.get('identification_document', ''))
                ws.write(row, 3, data_dict.get('lastname', ''))
                ws.write(row, 4, data_dict.get('lastname2', ''))
                ws.write(row, 5, data_dict.get('firstname', ''))
                ws.write(row, 6, data_dict.get('othernames', ''))
                ws.write(row, 7, data_dict.get('name', ''))
                ws.write(row, 8, data_dict.get('street', ''))
                zip_dian_code = str(data_dict.get('zip_dian_code', ''))
                ws.write(row, 9, zip_dian_code[:2])  # Primeros dos dígitos
                ws.write(row, 10, zip_dian_code[-3:])  # Últimos tres dígitos
                ws.write(row, 11, data_dict.get('country_code_dian', ''))
                # Escribir el saldo en la columna correspondiente sin redondear
                ws.write(row, 12, int(data_dict.get('deducible_balance', 0)))
                ws.write(row, 13, int(data_dict.get('no_deducible_balance', 0)))
                ws.write(row, 14, int(data_dict.get('iva_deducible_balance', 0)))
                ws.write(row, 15, int(data_dict.get('iva_no_deducible_balance', 0)))
                ws.write(row, 16, int(data_dict.get('retencion_renta_balance', 0)))
                ws.write(row, 17, int(data_dict.get('retencion_asumida_renta_balance', 0)))
                ws.write(row, 18, int(data_dict.get('retencion_iva_regimen_comun_balance', 0)))
                ws.write(row, 19, int(data_dict.get('retencion_iva_no_domiciliados_balance', 0)))
                row += 1

        #FORMATO 2276
        if self.type_format_id.type_format == 'format_2276':
            # Obtener todos los registros de general.exogenus relacionados
            general_records = self.type_format_id.general_id

            # Diccionario para almacenar los datos agrupados por tercero
            grouped_data = defaultdict(lambda: defaultdict(float))

            # Recorrer todos los registros generales
            for general_record in general_records:
                # Obtener el concepto
                concept = general_record.concept_id.name

                # Obtener las cuentas relacionadas
                accounts = general_record.format_account_id

                # Recorrer todas las cuentas
                for account in accounts:
                    query = """
                        SELECT DISTINCT
                            rdt.code AS document_type_id,
                            rpd.identification_document,
                            rpd.lastname,
                            rpd.lastname2,
                            rpd.firstname,
                            rpd.othernames,
                            rpd.name,
                            rpd.street,
                            rcs.dian_code AS zip_id,
                            rc.code_dian AS country_code_dian,
                            aml.account_id,
                            SUM(CASE 
                                WHEN %s = 'debit' THEN aml.debit
                                WHEN %s = 'credit' THEN aml.credit
                                WHEN %s = 'deb_cre' THEN aml.debit - aml.credit
                                WHEN %s = 'cre_deb' THEN aml.credit - aml.debit
                                WHEN %s = 'total' THEN aml.balance
                                ELSE 0 END) AS total_balance
                        FROM
                            account_move_line aml
                        LEFT JOIN
                            res_partner rpd ON aml.partner_id = rpd.id
                        LEFT JOIN
                            res_country rc ON rpd.country_id = rc.id
                        LEFT JOIN
                                    res_city_zip rcs ON rpd.zip_id = rcs.id    
                        LEFT JOIN
                                    res_partner_document_type rdt ON rpd.document_type_id = rdt.id       
                        WHERE
                            aml.account_id = %s
                            AND aml.date BETWEEN %s AND %s
                            AND aml.move_id IN (
                                SELECT id
                                FROM account_move
                                WHERE state = 'posted'
                            )
                        GROUP BY
                            rdt.code,
                            rpd.document_type_id,
                            rpd.identification_document,
                            rpd.lastname,
                            rpd.lastname2,
                            rpd.firstname,
                            rpd.othernames,
                            rpd.name,
                            rpd.street,
                            rcs.dian_code,
                            rc.code_dian,
                            aml.account_id
                    """

                    # Ejecutar la consulta SQL
                    self._cr.execute(query, (
                        general_record.total_account, general_record.total_account, general_record.total_account,
                        general_record.total_account, general_record.total_account, account.account_id.id,
                        self.start_date,
                        self.end_date))
                    query_results = self._cr.fetchall()

                    # Agregar los resultados a grouped_data y asignar los valores adicionales
                    for result in query_results:
                        document_type_id, identification_document, lastname, lastname2, firstname, othernames, name, street, zip_id, country_code_dian, account_id, total_balance = result

                        # Redondear el saldo antes de agregarlo al diccionario agrupado por tercero
                        total_balance_rounded = round(total_balance, 2)

                        # Usar el `identification_document` como clave para agrupar por tercero
                        key = identification_document

                        # Agregar el saldo al diccionario agrupado por tercero
                        grouped_data[key]['total_balance'] += total_balance_rounded

                        # Asignar los valores a cada registro dentro de grouped_data
                        grouped_data[key]['identification_document'] = identification_document
                        grouped_data[key]['document_type_id'] = document_type_id
                        grouped_data[key]['lastname'] = lastname
                        grouped_data[key]['lastname2'] = lastname2
                        grouped_data[key]['firstname'] = firstname
                        grouped_data[key]['othernames'] = othernames
                        grouped_data[key]['name'] = name
                        grouped_data[key]['street'] = street
                        grouped_data[key]['zip_id'] = zip_id
                        grouped_data[key]['country_code_dian'] = country_code_dian

                        # Verificar si la columna es una de las nuevas categorías y agrupar los datos en consecuencia
                        for column in general_record.column_id:
                            if column.name == 'Pagos por Salarios':
                                grouped_data[key]['salarios_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por emolumentos eclesiásticos':
                                grouped_data[key]['emolumentos_eclesiasticos_balance'] += total_balance_rounded
                            elif column.name == 'Pagos realizados con bonos electrónicos o de papel de servicio':
                                grouped_data[key]['bonos_servicio_balance'] += total_balance_rounded
                            elif column.name == 'Valor del exceso de los pagos por alimentación mayores a 41 UVT':
                                grouped_data[key]['exceso_alimentacion_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por honorarios':
                                grouped_data[key]['honorarios_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por servicios':
                                grouped_data[key]['servicios_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por comisiones':
                                grouped_data[key]['comisiones_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por prestaciones sociales':
                                grouped_data[key]['prestaciones_sociales_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por viáticos':
                                grouped_data[key]['viaticos_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por gastos de representación':
                                grouped_data[key]['gastos_representacion_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por compensaciones trabajo asociado cooperativo':
                                grouped_data[key]['compensaciones_cooperativo_balance'] += total_balance_rounded
                            elif column.name == 'Valor apoyos económicos no reembolsables o condonados':
                                grouped_data[key]['apoyos_economicos_balance'] += total_balance_rounded
                            elif column.name == 'Otros pagos':
                                grouped_data[key]['otros_pagos_balance'] += total_balance_rounded
                            elif column.name == 'Cesantías e intereses de cesantías efectivamente pagadas al empleado':
                                grouped_data[key]['cesantias_pagadas_balance'] += total_balance_rounded
                            elif column.name == 'Cesantías consignadas al fondo de cesantías':
                                grouped_data[key]['cesantias_fondo_balance'] += total_balance_rounded
                            elif column.name == 'Auxilio de cesantías reconocido a trabajadores del régimen tradicional del Código Sustantivo del Trabajo':
                                grouped_data[key]['auxilio_cesantias_balance'] += total_balance_rounded
                            elif column.name == 'Pensiones de Jubilación':
                                grouped_data[key]['pensiones_jubilacion_balance'] += total_balance_rounded
                            elif column.name == 'Total ingresos brutos por rentas de trabajo y pensión':
                                grouped_data[key]['ingresos_brutos_balance'] += total_balance_rounded
                            elif column.name == 'Aportes obligatorios por salud a cargo del trabajador':
                                grouped_data[key]['aportes_salud_balance'] += total_balance_rounded
                            elif column.name == 'Aportes obligatorios a fondos de pensiones y solidaridad pensional a cargo del trabajador':
                                grouped_data[key]['aportes_pensiones_balance'] += total_balance_rounded
                            elif column.name == 'Aportes voluntarios al régimen de ahorro individual con solidaridad - RAIS':
                                grouped_data[key]['aportes_voluntarios_rais_balance'] += total_balance_rounded
                            elif column.name == 'Aportes voluntarios a fondos de pensiones voluntarias':
                                grouped_data[key]['aportes_voluntarios_balance'] += total_balance_rounded
                            elif column.name == 'Aportes a cuentas AFC':
                                grouped_data[key]['aportes_afc_balance'] += total_balance_rounded
                            elif column.name == 'Aportes a cuentas AVC':
                                grouped_data[key]['aportes_avc_balance'] += total_balance_rounded
                            elif column.name == 'Valor de las retenciones en la fuente por pagos de rentas de trabajo o pensiones':
                                grouped_data[key]['retenciones_renta_balance'] += total_balance_rounded
                            elif column.name == 'Impuesto sobre las ventas – IVA. mayor valor del costo o gasto':
                                grouped_data[key]['iva_costo_gasto_balance'] += total_balance_rounded
                            elif column.name == 'Retención en la fuente a título de impuesto sobre las ventas – IVA.':
                                grouped_data[key]['retencion_iva_balance'] += total_balance_rounded
                            elif column.name == 'Pagos por alimentación hasta 41 UVT':
                                grouped_data[key]['alimentacion_41_uvt_balance'] += total_balance_rounded
                            elif column.name == 'Valor ingreso laboral promedio de los últimos seis meses':
                                grouped_data[key]['ingreso_promedio_seis_meses_balance'] += total_balance_rounded

            # Escribir datos en el archivo Excel
            row = 2
            for identification_document, data_dict in grouped_data.items():
                ws.write(row, 0, data_dict.get('identification_document', ''))
                ws.write(row, 2, data_dict.get('document_type_id', ''))
                ws.write(row, 3, data_dict.get('lastname', ''))
                ws.write(row, 4, data_dict.get('lastname2', ''))
                ws.write(row, 5, data_dict.get('firstname', ''))
                ws.write(row, 6, data_dict.get('othernames', ''))
                ws.write(row, 7, data_dict.get('street', ''))
                zip_dian_code = str(data_dict.get('zip_id', ''))
                ws.write(row, 8, zip_dian_code[:2])  # Primeros dos dígitos
                ws.write(row, 9, zip_dian_code[-3:])  # Últimos tres dígitos
                ws.write(row, 10, data_dict.get('country_code_dian', ''))

                # Escribir el saldo en la columna correspondiente sin redondear
                ws.write(row, 11, int(data_dict.get('salarios_balance', 0)))
                ws.write(row, 12, int(data_dict.get('emolumentos_eclesiasticos_balance', 0)))
                ws.write(row, 13, int(data_dict.get('bonos_servicio_balance', 0)))
                ws.write(row, 14, int(data_dict.get('exceso_alimentacion_balance', 0)))
                ws.write(row, 15, int(data_dict.get('honorarios_balance', 0)))
                ws.write(row, 16, int(data_dict.get('servicios_balance', 0)))
                ws.write(row, 17, int(data_dict.get('comisiones_balance', 0)))
                ws.write(row, 18, int(data_dict.get('prestaciones_sociales_balance', 0)))
                ws.write(row, 19, int(data_dict.get('viaticos_balance', 0)))
                ws.write(row, 20, int(data_dict.get('gastos_representacion_balance', 0)))
                ws.write(row, 21, int(data_dict.get('compensaciones_cooperativo_balance', 0)))
                ws.write(row, 22, int(data_dict.get('apoyos_economicos_balance', 0)))
                ws.write(row, 23, int(data_dict.get('otros_pagos_balance', 0)))
                ws.write(row, 24, int(data_dict.get('cesantias_pagadas_balance', 0)))
                ws.write(row, 25, int(data_dict.get('cesantias_fondo_balance', 0)))
                ws.write(row, 26, int(data_dict.get('auxilio_cesantias_balance', 0)))
                ws.write(row, 27, int(data_dict.get('pensiones_jubilacion_balance', 0)))
                ws.write(row, 28, int(data_dict.get('ingresos_brutos_balance', 0)))
                ws.write(row, 29, int(data_dict.get('aportes_salud_balance', 0)))
                ws.write(row, 30, int(data_dict.get('aportes_pensiones_balance', 0)))
                ws.write(row, 31, int(data_dict.get('aportes_voluntarios_rais_balance', 0)))
                ws.write(row, 32, int(data_dict.get('aportes_voluntarios_balance', 0)))
                ws.write(row, 33, int(data_dict.get('aportes_afc_balance', 0)))
                ws.write(row, 34, int(data_dict.get('aportes_avc_balance', 0)))
                ws.write(row, 35, int(data_dict.get('retenciones_renta_balance', 0)))
                ws.write(row, 36, int(data_dict.get('iva_costo_gasto_balance', 0)))
                ws.write(row, 37, int(data_dict.get('retencion_iva_balance', 0)))
                ws.write(row, 38, int(data_dict.get('alimentacion_41_uvt_balance', 0)))
                ws.write(row, 39, int(data_dict.get('ingreso_promedio_seis_meses_balance', 0)))

                row += 1

        archivo = io.BytesIO()
        wb.save(archivo)
        archivo.seek(0)
        data = archivo.read()
        if data:
            file_id = self.env['file.imp'].create({'filecontent': base64.b64encode(data)})
            filename_field = 'Exógena'
            if file_id and file_id.id:
                return {
                    'res_model': 'ir.actions.act_url',
                    'type': 'ir.actions.act_url',
                    'target': 'new',
                    'url': (
                        'web/content/?model=file.imp&id={0}'
                        '&filename_field={1}'
                        '&field=filecontent&download=true'
                        '&filename={1}.xls'.format(
                            file_id.id,
                            filename_field,
                        )
                    ),
                }
        else:
            raise ValueError(
                'Error de Descarga - No se pudo generar el archivo solicitado.'
            )

class FileImp(models.TransientModel):
    _name = 'file.imp'
    _description = u'Documentos para descargar'

    filecontent = fields.Binary(string="Impresión")
