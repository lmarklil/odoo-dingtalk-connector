# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.dingtalk_connector.dingtalk.main import DingTalk


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dingtalk_id = fields.Char(string='钉钉部门ID')

    # 生成钉钉SDK实例
    def get_dingtalk(self):
        # 获取配置信息
        config = self.env['ir.config_parameter'].sudo()
        return DingTalk(config.get_param('dingtalk_app_key'), config.get_param('dingtalk_app_secret'))

    # 根据钉钉的部门信息创建部门
    def create_departments_from_dingtalk(self):
        # 删除系统创建的无用部门
        self.search([('name', '=', 'Administration')]).sudo().unlink()
        self.search([('name', '=', 'Sales')]).sudo().unlink()

        # 检查根部门是否存在
        root_department = self.search([('dingtalk_id', '=', 1)]).sudo()
        if not root_department:
            dingtalk = self.get_dingtalk()
            root_department_info = dingtalk.get_department_info(1)
            # 创建根部门
            root_department = self.env['hr.department'].sudo().create({
                'dingtalk_id': 1,
                'name': root_department_info['name']
            })

        # 从根部门开始扫描并创建，根部门为1
        self.scan_and_create_departments(1, root_department['id'])
        self.department_clean_up()

    # 扫描并创建子部门
    def scan_and_create_departments(self, department_id, parent_department_id):
        # 调用钉钉API服务
        dingtalk = self.get_dingtalk()
        departments = dingtalk.get_departments(department_id).get('department')
        if departments != []:
            # 遍历部门列表
            for department in departments:
                # 检查部门是否存在，不存在时创建部门，否则检测部门信息是否更新，未更新则跳过创建继续扫描
                existing_department = self.search([('dingtalk_id', '=', department['id'])])
                if not existing_department:
                    parent_department = self.env['hr.department'].sudo().create({
                        'dingtalk_id': department['id'],
                        'name': department['name'],
                        'parent_id': parent_department_id
                    })
                    self.scan_and_create_departments(department['id'], parent_department['id'])
                else:
                    # 检测数据是否更新
                    if existing_department.name != department['name']:
                        existing_department.write({
                            'name': department['name']
                        })
                        self.scan_and_create_departments(department['id'], existing_department['id'])

    # 检查部门是否需要清理
    def department_clean_up(self):
        dingtalk = self.get_dingtalk()
        dingtalk_departments = dingtalk.get_departments(1, fetch_child=True).get('department')
        local_departments = self.search([]).sudo()
        for local_department in local_departments:
            unlink = True
            if int(local_department.dingtalk_id) != 1:
                for dingtalk_department in dingtalk_departments:
                    if str(local_department.dingtalk_id) == str(dingtalk_department['id']):
                        unlink = False
                        break
            else:
                unlink = False
            if unlink:
                local_department.unlink()

    # 通过钉钉ID查找部门
    def search_department_by_dingtalk_id(self, id):
        department = self.search([('dingtalk_id', '=', id)]).sudo()
        # 检查部门是否存在，若不存在则同步部门
        if not department:
            self.create_departments_from_dingtalk()
            department = self.search([('dingtalk_id', '=', id)]).sudo()
        return department
