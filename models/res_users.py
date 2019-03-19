# -*- coding: utf-8 -*-
import random
from odoo.addons.dingtalk_connector.dingtalk.main import DingTalk
from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = 'res.users'

    main_department_id = fields.Many2one(comodel_name="hr.department", string='主部门ID')
    department_ids = fields.Many2many(comodel_name="hr.department", string='部门IDS')
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
        # 获取并创建在职用户
        user_id_list = dingtalk.get_user_id_list()
        for user_id in user_id_list:
            self.create_user(user_id)
        self.user_clean_up(user_id_list)

    def create_user(self, user_id, active=True):
        """
        通过钉钉Id创建Odoo用户
        """
        user = self.sudo().search([('dingtalk_id', '=', user_id), ('active', '=', active)])
        if not user:
            password = 'dingtalk_id:' + user_id + '|key:' + str(random.randint(100000, 999999))
            self.create_user_by_dingtalk_id(user_id, password, active=active)
        else:
            self.update_user_by_dingtalk_id(user)

    def create_user_by_dingtalk_id(self, dingtalk_id, password, active=True):
        """
        通过钉钉用户Id创建Odoo用户
        """
        # 获取钉钉API服务
        dingtalk = self.get_dingtalk()
        user_detail = dingtalk.get_user_detail_by_ids(dingtalk_id).get('result')[0].get('field_list')

        # 将UserInfo转换成写入到Odoo的格式
        user_info = self.sudo().get_user_info_from_user_detail(user_detail)

        # 获取不重复的账号
        email = user_info.get('email')
        if email:
            email_str_array = email.split('@')
            email_name = email_str_array[0]
            email_host = email_str_array[1]
            if email_host != 'szpdc.com':
                # 返回True是因为免登的时候会判断是否注册失败，如果为True则注册失败，重定向到Odoo登陆页面
                return True
            email_count = len(self.search([('login', 'like', email_name)]).sudo())
            if email_count > 0:
                email = email_name + str(email_count + 1) + '@' + email_host
        else:
            return True

        # 获取不重复的姓名
        name = user_info.get('name')
        name_count = len(self.search([('name', 'like', name)]).sudo())
        if name_count > 0:
            name = name + str(name_count + 1)

        # 获取主部门ID
        main_department_id = self.env['hr.department'].search_department_by_dingtalk_id(
            user_info.get('main_department_id')).id

        # 获取部门IDS
        department_ids = []
        for department_id in user_info.get('department_ids'):
            id = self.env['hr.department'].search_department_by_dingtalk_id(department_id).id
            if id:
                department_ids.append(id)

        # 创建Odoo用户
        values = {
            'active': active,
            "login": email,
            "password": password,
            "name": name,
            'email': email,
            'department_ids': [(6, 0, department_ids)],
            'main_department_id': main_department_id,
            'groups_id': request.env.ref('base.group_user'),
            'dingtalk_id': dingtalk_id
        }
        user = self.sudo().create(values)

        # 创建员工
        values = {
            'user_id': user.id,
            'name': name,
            'department_id': main_department_id,
            'mobile_phone': user_info.get('mobile')
        }
        employee = self.env['hr.employee'].sudo().create(values)

    def update_user_by_dingtalk_id(self, user):
        """
        更新用户信息
        """
        # 获取钉钉API服务
        dingtalk = self.get_dingtalk()
        user_detail = dingtalk.get_user_detail_by_ids(user.dingtalk_id).get('result')[0].get('field_list')

        # 将UserInfo转换成写入到Odoo的格式
        user_info = self.sudo().get_user_info_from_user_detail(user_detail)
        # 获取主部门ID
        main_department_id = self.env['hr.department'].search_department_by_dingtalk_id(
            user_info.get('main_department_id')).id

        # 获取部门IDS
        department_ids = []
        for department_id in user_info.get('department_ids'):
            id = self.env['hr.department'].search_department_by_dingtalk_id(department_id).id
            if id:
                department_ids.append(id)
        values = {
            'department_ids': [(6, 0, department_ids)],
            'main_department_id': main_department_id,
        }
        user.write(values)
        user_employee = user.employee_ids[0]
        values = {
            'department_id': main_department_id
        }
        user_employee.write(values)

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
            elif fildcode == 'sys00-deptIds':
                department_ids = info.get('value').split('|')
                user_info['department_ids'] = department_ids
            elif fildcode == 'sys00-mainDeptId':
                user_info['main_department_id'] = info.get('value')
            elif fildcode == 'sys00-mobile':
                user_info['mobile'] = info.get('value')
        return user_info

    def user_clean_up(self, dingtalk_user_ids):
        """
        清理离职用户
        """
        local_users = self.search([('dingtalk_id', '!=', None)]).sudo()
        for local_user in local_users:
            unlink = True
            for dingtalk_user in dingtalk_user_ids:
                if str(local_user.dingtalk_id) == str(dingtalk_user):
                    unlink = False
                    break;
            if unlink:
                local_user.write({
                    'active': False
                })
