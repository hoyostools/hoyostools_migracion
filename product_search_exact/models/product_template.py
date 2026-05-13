from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _fix_default_code_operator(self, domain):
        if not domain:
            return domain

        new_domain = []
        for cond in domain:
            if isinstance(cond, (list, tuple)) and cond[0] == 'default_code' and cond[1] == 'ilike':
                new_domain.append((cond[0], '=', cond[2]))
            else:
                new_domain.append(cond)

        return new_domain

    @api.model
    def search(self, domain=None, offset=0, limit=None, order=None):
        domain = self._fix_default_code_operator(domain)
        return super().search(domain=domain, offset=offset, limit=limit, order=order)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kwargs):
        domain = self._fix_default_code_operator(domain)
        return super().search_read(
            domain=domain,
            fields=fields,
            offset=offset,
            limit=limit,
            order=order,
            **kwargs
        )