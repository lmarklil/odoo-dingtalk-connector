# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dingtalk_id = fields.Char(string='钉钉用户Id')
