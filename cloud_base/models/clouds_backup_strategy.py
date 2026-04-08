# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models


class clouds_backup_strategy(models.Model):
    """
    The model to systemize cloud tags
    """
    _name = "clouds.backup.strategy"
    _description = "Backup Strategy"

    name = fields.Char(string="Name", required=True)
    client_id = fields.Many2one("clouds.client", string="Client", ondelete="cascade", required=True)
    next_backup = fields.Datetime(string="Next backup time (approx.)")
    backup_time = fields.Float("Frequency (days)", default=1.0)
    backup_folder_id = fields.Many2one("clouds.folder", string="Backup Folder", required=True)
    backups_count = fields.Integer(
        "Backups count",
        help="How many should be kept? Excess (oldest) ones will be removed. If zero, all backups will be kept",
    )
    backup_ids = fields.Many2many("ir.attachment", string="Backups")
    filestore = fields.Boolean(string="Include filestore", default=True)
    manifest = fields.Boolean(string="Include manifest")
    fail_num = fields.Integer("Failed attempts", default=0)

    _order = "backup_time DESC, id"
    _sql_constraints = [
        ("backup_time_check", "check (backup_time>0.02)", "Frequency could not be less than 30 minutes!"),
    ]

    @api.model
    def action_make_backups(self):
        """
        The method to find all clients which should prepare and sync the automatic backups
        For each client we do one backup for the longest found frequency. This is done since when monthly backup is
        done, daily or weekly one is not anymore required. So, others we move if the time is too close.

        Methods:
         * _caclulate_time_and_check_lock
         * action_make_backup of clouds.queue
         * _get_the_next_backup_datetime
        """
        strategy_ids = self.env["clouds.backup.strategy"].search([
            ("client_id.state", "=", "confirmed"), ("client_id.turn_backups", "=", True),
            ("backup_folder_id", "!=", False),
            "|", ("next_backup", "<=", fields.Datetime.now()), ("next_backup", "=", False),
        ])
        processed_client_ids = self.env["clouds.client"]
        for strategy in strategy_ids:
            client_id = strategy.client_id
            if client_id in processed_client_ids:
                continue
            processed_client_ids |= client_id
            attachment_id = strategy.action_make_backup()
            if attachment_id:
                for bstrategy in client_id.backup_ids:
                    if bstrategy.backup_time >= strategy.backup_time:
                        # longer and this frequency strategies are not moved
                        continue
                    new_time = bstrategy._get_the_next_backup_datetime()
                    if bstrategy.next_backup and bstrategy.next_backup >= new_time:
                        # if lower frequency strategy is already after the move time, we do not touch it
                        continue
                    bstrategy.write({"next_backup": new_time})
                    self.env.cr.commit()

    def action_make_backup(self):
        """
        The method to prepare a backup for the strategy
        1. Ensure no backups is now in the process (e.g., do not do monhly when yearly started and not timeouted)
        2. Move the next date to avoid each cron trigger when timeouted
        3. Ensure the strategy folder is fine
        4. Create and send the backup
        5. Save the backup to the strategy attachment and unlink the exceeding number
        6. If failed save the failed numbers; if exceeds the configured number - move to the next time

        Methods:
         * _caclulate_time_and_check_lock of clouds.queue
         * _make_backup of clouds.client
         * _get_the_next_backup_datetime

        Extra info:
         * Expected singelton
        """
        self.client_id._cloud_log(True, "Start creating {} database backup".format(self.name))
        # 1
        Config = self.env["ir.config_parameter"].sudo()
        timeout = int(Config.get_param("cloud_base_backup_timeout", "900"))
        cron_timeout = self.env["clouds.queue"]._caclulate_time_and_check_lock(
            "cloud_base_backups_lock_time", "Auto backup", timeout >= 900 and timeout or 900,
        )
        if not cron_timeout:
            return
        # 2
        prev_time = self.next_backup
        self.next_backup = self._get_the_next_backup_datetime()
        self.env.cr.commit()
        # 3
        folder_id = self.backup_folder_id
        if not folder_id or self.client_id != folder_id.client_id or not folder_id.cloud_key:
            self.client_id._cloud_log(
                False, "The database auto backup failed. Reason: the client backup folder or is not synced",
            )
            return False
        # 4
        attachment_id = self.client_id._make_backup(folder_id, self.name, self.filestore, self.manifest)
        self.client_id._cloud_log(True, "The database auto backup result: {}".format(attachment_id))
        if attachment_id:
            # 5
            self.backup_ids = [(4, attachment_id.id)]
            if self.backups_count > 0 and len(self.backup_ids) > self.backups_count:
                number_to_remove = self.backups_count - len(self.backup_ids)
                existing_backup_ids = self.backup_ids.sorted("create_date", reverse=True)
                self.client_id._cloud_log(
                    True,
                    "Unlink obsolete backups: {}".format(existing_backup_ids[number_to_remove:]),
                    need_commit=True,
                )
                existing_backup_ids[number_to_remove:].unlink()
            self.write({"fail_num": 0})
            self.client_id._cloud_log(
                True,
                "The database auto backup success: {}. Next execution: {}".format(self.name, self.next_backup),
                need_commit=True,
            )
        else:
            # 6
            try:
                max_retries = int(self.env["ir.config_parameter"].sudo().get_param("cloud_base.max_retries", "0"))
            except:
                max_retries = 7
            max_retries = max_retries > 0 and max_retries or 7
            fail_num = self.fail_num + 1
            if fail_num >= max_retries:
                self.write({"fail_num": 0})
            else:
                self.write({"fail_num": fail_num, "next_backup": prev_time})
        Config.sudo().set_param("cloud_base_backups_lock_time", "")
        self.client_id._cloud_log(True, "Finish creating {} database backup".format(self.name), need_commit=True)
        return attachment_id

    def _get_the_next_backup_datetime(self):
        """
        The method to define the next exceution time

        Returns:
         * datetime object

        Extra info:
         * Expected singleton
        """
        now = fields.Datetime.now()
        next_now = self.next_backup or now + timedelta(days=self.backup_time)
        while next_now <= now:
            next_now += timedelta(days=self.backup_time)
        return next_now
