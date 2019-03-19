# -*- coding: utf-8 -*-
{
    'name': "钉钉",
    'summary': """提供钉钉集成服务""",
    'description': """
        提供钉钉集成服务
	""",
    'author': "Li jinhui",
    'website': "https://ocubexo.github.io",
    'category': 'Connector',
    'version': '1.5',
    'depends': ['hr'],
    'external_dependencies': {
        'python': ['pycryptodome']
    },
    'data': [
        'views/dingtalk_connector_templates.xml',
        'views/res_config_settings_view.xml'
    ]
}
