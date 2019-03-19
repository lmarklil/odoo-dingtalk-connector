# -*- coding: utf-8 -*-
import base64, string
from random import choice
from odoo.addons.dingtalk_connector.dingtalk.main import DingTalk
from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dingtalk_corp_id = fields.Char(string='钉钉corpId')
    dingtalk_app_key = fields.Char(string='钉钉AppKey')
    dingtalk_app_secret = fields.Char(string='钉钉AppSecret')
    dingtalk_sns_app_id = fields.Char(string='钉钉SNSAppId')
    dingtalk_sns_app_secret = fields.Char(string='钉钉SNSAppSecret')

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('dingtalk_corp_id', self[0].dingtalk_corp_id)
        params.set_param('dingtalk_app_key', self[0].dingtalk_app_key)
        params.set_param('dingtalk_sns_app_id', self[0].dingtalk_sns_app_id)
        params.set_param('dingtalk_sns_app_secret', self[0].dingtalk_sns_app_secret)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            dingtalk_corp_id=params.get_param('dingtalk_corp_id'),
            dingtalk_app_key=params.get_param('dingtalk_app_key'),
            dingtalk_app_secret=params.get_param('dingtalk_app_secret'),
            dingtalk_sns_app_id=params.get_param('dingtalk_sns_app_id'),
            dingtalk_sns_app_secret=params.get_param('dingtalk_sns_app_secret')
        )
        return res

    def callback_api_register(self):
        """
        注册钉钉业务回调接口
        """
        config = self.env['ir.config_parameter'].sudo()
        # 回调Tag
        call_back_tag = ['user_add_org']
        # 生成Token
        token = self.generate_random_str(16)
        # 生成AESKey并进行Base64编码
        aes_key = base64.b64encode(self.generate_random_str(32).encode()).decode().rstrip('=')
        # 保存Token和AESKey
        config.set_param('dingtalk_call_back_api_token', token)
        config.set_param('dingtalk_call_back_api_aes_key', aes_key)
        # 回调Url
        call_back_url = request.httprequest.host_url + 'dingtalk/call_back'
        try:
            # 向钉钉接口发起回调接口注册请求
            dingtalk = DingTalk(config.get_param('dingtalk_app_key'), config.get_param('dingtalk_app_secret'))
            dingtalk.callback_api_register(call_back_tag, config.get_param('dingtalk_call_back_api_token'),
                                           config.get_param('dingtalk_call_back_api_aes_key'), call_back_url)
        except Exception as e:
            raise UserError(
                _('回调接口注册失败！\n\n错误原因：\n' + str(
                    e) + '\n\n请检查：\n（1）基本参数是否正确。\n（2）回调地址是否已注册。\n（3）Odoo服务器是否可以被外网访问。\n（4）钉钉后台权限设置是否正确。'))

    def generate_random_str(self, size,
                            chars=string.ascii_letters + string.ascii_lowercase + string.ascii_uppercase + string.digits):
        """
        生成随机字符串
        """
        return ''.join(choice(chars) for i in range(size))

    def update_users_and_departments(self):
        """
        手动同步成员与部门
        """
        try:
            self.env['res.users'].sudo().create_users_from_dingtalk()
        except Exception as e:
            raise UserError(_('同步失败！\n\n错误原因：\n' + str(e)))
