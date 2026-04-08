#coding: utf-8

from dateutil.relativedelta import relativedelta
from datetime import date

from odoo import  _, api, fields, models


def return_start_and_end(interval, ttype, inclusive, period_direction, compared_to="today", compared_to_value=1,
    compared_to_type="months"):
    """
    The method to return start and end date based on interval

    0. If we compare not to today, then we should calculate real compared date
    1. If inclusive, it means we consider the current period as independant one. E.g. Today is 25/08.
       One last month inclusive means, we consider 01/08 - 31/08. Exclusive would be 01/07-31/07
       One next month inclusive means, we consider 01/08 - 31/08. Exclusive would be 01/09-30/09
    2. We take time_delta for start point (end point for the "next").
    3. We take time_delta for the opposite point
    4. We calculate start and end based on time_deltas

    Args:
     * interval - int
     * ttype - "days", "weeks", "months", "years"
     * inclusive - boolean
     * period_direction - either "last" or "next"
     * compared_to - "today",  "last" or "next"
     * compared_to_value - int
     * compared_to_type - "days", "weeks", "months", "years"

    Returns:
     * date.date, date.date
    """
    def _return_relative_delta(int_type, int_interval):
        """
        The method to find the point in X moments from

        Returns:
         * relativedelta object
        """
        days = int_type == "days" and int_interval or 0
        weeks = int_type == "weeks" and int_interval or 0
        months = int_type == "months" and int_interval or 0
        years = int_type == "years" and int_interval or 0
        return relativedelta(days=days, weeks=weeks, months=months, years=years)

    # 0
    today = date.today()
    if compared_to != "today" and compared_to_value:
        delta = _return_relative_delta(
            compared_to_type, compared_to == "next" and compared_to_value or -compared_to_value
        )
        today = today + delta
    # 1
    the_next_interval = 0
    if period_direction == "next":
        if not inclusive:
            the_next_interval = 1
            interval += 1
    elif inclusive:
        the_next_interval = 1
        interval -= 1
    # 2
    period_delta = _return_relative_delta(ttype, interval)
    # 3
    period_delta_2 = _return_relative_delta(ttype, the_next_interval)
    # 4
    calculated_start = calculated_end = today
    if period_direction == "next":
        calculated_start = today + period_delta_2
        calculated_end  = today + period_delta
    else:
        calculated_start = today - period_delta
        calculated_end = today + period_delta_2
    return calculated_start, calculated_end

def return_the_first_month_or_year_date(calc_date, year=False):
    """
    The method to return first date of the month or year

    Args:
     * calc_date - date.date
     * year - in case it should be the first day of year

    Returns:
     * date.date
    """
    month = year and 1 or calc_date.month
    return date(year=calc_date.year, month=month, day=1,)


class cloud_domain_period(models.Model):
    """
    The model to construct relative day domains
    """
    _name = "cloud.domain.period"
    _description = "Relative Period"

    @api.depends("field_id", "period_value", "period_type", "inclusive_this", "period_direction", "compared_to",
        "compared_to_type", "compared_to_value")
    def _compute_domain(self):
        """
        Compute method for domain
        It is not stored, since the date depends on today

        1. For days: we just take calculated dates
        2. Foe weeks: we take the first week date for both start and. Note (!): from Monday to Sunday
        3. For months: we take the first month day for both start and end
        4. For years: we take the first year day for both start and end
        5. Date end is 1 day deducted to show the period inclusive, not exlusive last date

        Methods:
         * return_start_and_end
         * return_the_first_month_or_year_date
         * _return_translation_for_field_label
        """
        for period in self:
            domain = "[]"
            title = False
            field = period.field_id
            interval = period.period_value
            interval_type = period.period_type
            inclusive = period.inclusive_this
            period_direction = period.period_direction
            compared_to = period.compared_to
            compared_to_value = period.compared_to_value
            compared_to_type = period.compared_to_type
            if field and interval > 0 and interval_type and period_direction:
                calculated_start, calculated_end = return_start_and_end(
                    interval=interval, ttype=interval_type, inclusive=inclusive, period_direction=period_direction,
                    compared_to=compared_to, compared_to_value=compared_to_value, compared_to_type=compared_to_type,
                )
                # 1
                if interval_type == "weeks":
                    # 2
                    calculated_start = calculated_start - relativedelta(days=calculated_start.weekday())
                    calculated_end = calculated_end - relativedelta(days=calculated_end.weekday())
                elif interval_type == "months":
                    # 3
                    calculated_start = return_the_first_month_or_year_date(calculated_start)
                    calculated_end = return_the_first_month_or_year_date(calculated_end)
                elif interval_type == "years":
                    # 4
                    calculated_start = return_the_first_month_or_year_date(calculated_start, year=True)
                    calculated_end = return_the_first_month_or_year_date(calculated_end, year=True)

                domain = "['&', ['{a}', '<', '{b}'], ['{a}', '>=', '{c}']]".format(
                    a=field.name, b=calculated_end, c=calculated_start,
                )
                # 5
                title = "{} - {}".format(calculated_start, calculated_end-relativedelta(days=1))
            period.domain = domain
            period.title = title

    sync_model_id = fields.Many2one("sync.model", string="Sync Model")
    field_id = fields.Many2one("ir.model.fields", string="Date", required=True, ondelete="cascade")
    period_direction = fields.Selection(
        [("last", "the last"), ("next", "the next")], string="In", default="last", required=True,
    )
    period_value = fields.Integer("Interval", required=True, default=1)
    period_type = fields.Selection(
        [("days", "days"), ("weeks", "weeks"), ("months", "months"), ("years", "years")],
        string="Interval Type",
        required=True,
        default="months",
    )
    compared_to = fields.Selection(
        [("today", "today"), ("last", "past"), ("next", "future")],
        string="Compared To",
        default="today",
        required=True,
    )
    compared_to_value = fields.Integer("Before/After Interval", required=True, default=0)
    compared_to_type = fields.Selection(
        [("days", "days"), ("weeks", "weeks"), ("months", "months"), ("years", "years")],
        string="Before/After Interval Type",
        required=True,
        default="months",
    )
    inclusive_this = fields.Boolean(
        string="Including current",
        help="If checked, then the current period will be also included. For example, today is 25/11/2022. We selected\
'the last 2 months'. If not checked, Odoo will consider September and October. Otherwise, October and November",
    )
    domain = fields.Text(string="Domain", compute=_compute_domain)
    title = fields.Char(string="Title", compute=_compute_domain)

    _sql_constraints = [("period_value_check", "check (period_value>0)", _("Intervals should be positive!"))]

    _order = "field_id, id"
