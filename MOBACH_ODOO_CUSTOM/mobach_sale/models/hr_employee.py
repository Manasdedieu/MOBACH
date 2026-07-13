# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    start_date = fields.Datetime(string="Date d'embauche")



class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    start_date = fields.Datetime(string="Date d'embauche")
