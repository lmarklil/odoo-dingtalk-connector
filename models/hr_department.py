# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.dingtalk_connector.dingtalk.main import DingTalk


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    dingtalk_id = fields.Char(string='钉钉部门ID')

    # 根据钉钉的部门信息创建部门
    def create_departments_from_dingtalk(self):
        # 从根部门开始扫描并创建，根部门为1
        self.scan_and_create_departments(1, None)

    # 扫描并创建子部门
    def scan_and_create_departments(self, department_id, parent_department_id):
        # 获取配置信息
        config = self.env['ir.config_parameter'].sudo()
        # 返回钉钉API服务
        dingtalk = DingTalk(config.get_param('dingtalk_app_key'), config.get_param('dingtalk_app_secret'))
        departments = dingtalk.get_departments(department_id).get('department')
        if departments != []:
            # 遍历部门列表
            for department in departments:
                # 检查部门是否存在，不存在时创建部门，否则跳过创建继续扫描
                existing_department = self.search([('dingtalk_id', '=', department['id'])])
                if not existing_department:
                    parent_department = self.env['hr.department'].sudo().create({
                        'dingtalk_id': department['id'],
                        'name': department['name'],
                        'parent_id': parent_department_id
                    })
                    self.scan_and_create_departments(department['id'], parent_department['id'])
                else:
                    self.scan_and_create_departments(department['id'], existing_department['id'])
