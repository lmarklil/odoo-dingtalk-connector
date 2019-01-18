# -*- coding: utf-8 -*-
import random
from odoo.addons.dingtalk_connector.dingtalk.main import DingTalk
from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = 'res.users'
    dingtalk_id = fields.Char(string='钉钉用户ID')

    def _check_credentials(self, dingtalk_id):
        """
        用户验证
        """
        try:
            return super(ResUsers, self)._check_credentials(dingtalk_id)
        except AccessDenied:
            # 判断是否为钉钉免登触发的用户验证方法
            if request.session.dingtalk_auth:
                request.session.dingtalk_auth = None
            else:
                raise AccessDenied

    def get_dingtalk(self):
        """
        获取钉钉API服务
        """
        # 获取配置信息
        config = self.env['ir.config_parameter'].sudo()
        # 返回钉钉API服务
        return DingTalk(config.get_param('dingtalk_app_key'), config.get_param('dingtalk_app_secret'))

    def create_users_from_dingtalk(self):
        """
        获取所有钉钉用户并以此创建Odoo用户
        """
        # 获取钉钉API服务
        dingtalk = self.get_dingtalk()

        def create_user(user_id, active=True):
            """
            通过钉钉Id创建Odoo用户
            """
            if not self.sudo().search([('dingtalk_id', '=', user_id), ('active', '=', active)]):
                password = 'dingtalk_id:' + user_id + '|key:' + str(random.randint(100000, 999999))
                self.create_user_by_dingtalk_id(user_id, password, active=active)

        # 获取并创建在职用户
        user_id_list = dingtalk.get_user_id_list()
        for user_id in user_id_list:
            create_user(user_id)
        # 获取并创建离职用户
        dimission_user_id_list = dingtalk.get_dimission_user_id_list()
        for user_id in dimission_user_id_list:
            create_user(user_id, active=False)

    def create_user_by_dingtalk_id(self, dingtalk_id, password, active=True):
        """
        通过钉钉用户Id创建Odoo用户
        """
        # 获取钉钉API服务
        dingtalk = self.get_dingtalk()
        user_detail = dingtalk.get_user_detail_by_ids(dingtalk_id).get('result')[0].get('field_list')
        # 将UserInfo转换成写入到Odoo的格式
        user_info = self.sudo().get_user_info_from_user_detail(user_detail)
        # 创建Odoo用户
        values = {
            'active': active,
            "login": dingtalk_id + '-' + user_info.get('mobile'),
            "password": password,
            "name": user_info.get('name'),
            'email': user_info.get('email'),
            'groups_id': request.env.ref('base.group_user'),
            'dingtalk_id': dingtalk_id
        }
        user = self.sudo().create(values)
        # 搜索部门
        department = self.env['hr.department'].sudo().search(
            [('dingtalk_id', '=', user_info.get('department'))])

        # 创建员工
        def create_employee(department_id):
            values = {
                'user_id': user.id,
                'name': user_info.get('name'),
                'department_id': department_id,
                'dingtalk_id': dingtalk_id
            }
            employee = self.env['hr.employee'].sudo().create(values)

        # 判断部门是否存在，如果存在则创建员工，如果不存在则执行部门同步
        if department:
            create_employee(department.id)
        else:
            self.env['hr.department'].sudo().create_departments_from_dingtalk()
            # 再次搜索部门
            department = self.env['hr.department'].sudo().search(
                [('dingtalk_id', '=', user_info.get('department'))])
            create_employee(department.id)

    def get_user_info_from_user_detail(self, user_detail):
        """
        从用户详情中生成用户基本信息
        """
        user_info = {}
        for info in user_detail:
            fildcode = info.get('field_code')
            if fildcode == 'sys00-name':
                user_info['name'] = info.get('value')
            elif fildcode == 'sys00-email':
                user_info['email'] = info.get('value')
            elif fildcode == 'sys00-mainDeptId':
                user_info['department'] = info.get('value')
            elif fildcode == 'sys00-mobile':
                user_info['mobile'] = info.get('value').split('-')[1]
        return user_info

    def start_leave_users_auto_cleaner(self):
        """
        定时清理离职用户
        """
        # TODO 待重构或废弃
        isCreated = self.env['ir.cron'].sudo().search(
            [('name', '=', 'clean user task')])
        if not isCreated:
            self.env['ir.cron'].sudo().create({
                'name': 'clean user task',
                'interval_numbe': 1,
                'interval_type': 'days',
                'numbercall': -1,
                'doall': True,
                'state': 'code',
                'model_id': 86,
                'code': 'model.cleanUser()'
            })
            return '定时禁用离职人员任务已开启'
        return '定时禁用离职人员任务已存在，请勿重复开启'
