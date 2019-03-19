# -*- coding: utf-8 -*-
import time, random
from odoo.addons.dingtalk_connector.dingtalk.main import DingTalk
from odoo.addons.dingtalk_connector.dingtalk.crypto import DingTalkCrypto
from odoo import http
from odoo.http import request


class IndexController(http.Controller):
    BASE_URL = '/dingtalk'

    def get_dingtalk(self):
        """
        获取钉钉API服务
        """
        # 获取配置信息
        config = request.env['ir.config_parameter'].sudo()
        # 返回钉钉API服务
        return DingTalk(config.get_param('dingtalk_app_key'), config.get_param('dingtalk_app_secret'),
                        config.get_param('dingtalk_sns_app_id'), config.get_param('dingtalk_sns_app_secret'))

    @http.route(BASE_URL + '/sign/in', type='http', auth='none')
    def sign_in(self, **kw):
        """
        钉钉免登入口
        """
        config = request.env['ir.config_parameter'].sudo()
        data = {
            'corp_id': config.get_param('dingtalk_corp_id')
        }
        return request.render('dingtalk_connector.sign_in', data)

    @http.route(BASE_URL + '/auth', type='http', auth='none')
    def auth(self, **kw):
        """
        钉钉免登认证
        """
        authCode = kw.get('authCode')
        code = kw.get('code')
        dingtalk = self.get_dingtalk()
        # 检测是通过扫码跳转还是免登跳转
        if authCode:
            # 免登跳转处理
            try:
                user_info = dingtalk.get_user_info_by_auth_code(authCode)
                user_id = user_info.get('userid')
            except:
                return http.local_redirect('/web/login')
        elif code:
            # 扫码跳转处理
            try:
                persistent_code_data = dingtalk.get_sns_persistent_code(code)
                unionid = persistent_code_data.get('unionid')
                user_id = dingtalk.get_user_id_by_unionid(unionid).get('userid')
            except:
                return http.local_redirect('/web/login')
        # 检查钉钉用户是否存在
        if user_id:
            # 根据钉钉Id判断Odoo用户是否存在，存在即登陆
            user = request.env['res.users'].sudo().search([('dingtalk_id', '=', user_id)])
            if user:
                # 添加登陆模式为钉钉免登模式
                request.session.dingtalk_auth = True
                # 生成登陆凭证
                request.session.authenticate(request.session.db, user.login, user_id)
                return http.local_redirect('/web')
            else:
                # 自动注册
                password = 'dingtalk_id:' + user_id + '|key:' + str(random.randint(100000, 999999))
                fail = request.env['res.users'].sudo().create_user_by_dingtalk_id(user_id, password)
                if not fail:
                    return http.local_redirect('/dingtalk/sign/in')
        return http.local_redirect('/web/login')

    @http.route(BASE_URL + '/call_back', type='json', auth='none', methods=['POST'], csrf=False)
    def delete_user(self, **kw):
        """
        钉钉业务回调 接收接口
        """

        # TODO 接收业务回调数据
        def result():
            # 获取Odoo配置
            config = request.env['ir.config_parameter'].sudo()
            dingtalkCrypto = DingTalkCrypto(config.get_param('dingtalk_call_back_api_aes_key'),
                                            config.get_param('dingtalk_corp_id'))
            # 加密数据
            encrypt = dingtalkCrypto.encrypt('success')
            # 获取当前时间戳
            timestamp = str(int(round(time.time() * 1000)))
            # 获取随机字符串
            nonce = dingtalkCrypto.generateRandomKey(8)
            # 生成签名
            signature = dingtalkCrypto.generateSignature(nonce, timestamp,
                                                         config.get_param('dingtalk_call_back_api_token'),
                                                         encrypt)
            data = {
                'msg_signature': signature,
                'timeStamp': timestamp,
                'nonce': nonce,
                'encrypt': encrypt
            }
            result = {
                'json': True,
                'data': data
            }
            return result

        return result()

    @http.route(BASE_URL + '/qrcode', type='http', auth='none')
    def qrcode(self, **kw):
        """
        钉钉扫码登陆页面
        """
        config = request.env['ir.config_parameter'].sudo()
        data = {
            'app_id': config.get_param('dingtalk_sns_app_id'),
            'redirect_url': request.httprequest.host_url + 'dingtalk/auth'
        }
        return request.render('dingtalk_connector.qrcode_login', data)
