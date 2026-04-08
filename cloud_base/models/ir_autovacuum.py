# -*- coding: utf-8 -*-

import os

from odoo import models
from odoo.tools import config


class ir_autovacuum(models.AbstractModel):
    """
    Cloud storage basic settings
    """
    _inherit = "ir.autovacuum"

    def _run_vacuum_cleaner(self):
        """
        Re-write to recalculate the size of filestore
        @see https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python
        """
        super(ir_autovacuum, self)._run_vacuum_cleaner()
        filestore_size = 0
        for dirpath, dirnames, filenames in os.walk(config.filestore(self._cr.dbname)):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    filestore_size += os.path.getsize(fp)
        filestore_size = filestore_size / (1024 * 1024)
        self.env["ir.config_parameter"].sudo().set_param("cloud_base.filestore_size", filestore_size)
