from odoo import api, fields, models

class HrEmployeeDeductionRetention(models.Model):
    _inherit = 'hr.employee.deduction.retention'

    accum = fields.Boolean(default=False, help="Este campo discrimina si el registro fue creado desde los acumulados")

    @api.model_create_multi
    def create(self, vals):
        if self.env.context.get('acc_ret_ex_25'):
            for val in vals:
                encab_id = self.env['hr.employee.rtefte'].create({
                    'employee_id': val.get('employee_id'),
                    'year': val.get('year'),
                    'month': val.get('month'),
                    'accum': True,
                })
                val['encab_id'] = encab_id.id
                val['concept_deduction_id'] = self.env.ref('th360_hr_payroll.RE_RENTA_EXENTA_O').id
                val['contract_id'] = self.env['hr.employee'].search([('id', '=', val.get('employee_id'))]).contract_id.id
                val['accum'] = True

        return super(HrEmployeeDeductionRetention, self).create(vals)

class HrEmployeeRtefte(models.Model):
    _inherit = 'hr.employee.rtefte'

    accum = fields.Boolean(default=False, help="Este campo discrimina si el registro fue creado desde los acumulados")
