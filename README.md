# OdooDingtalkConnector
Odoo钉钉连接器

## 简介
Odoo连接器提供Odoo与钉钉的集成服务，基于Odoo12.0开发。

## [更新日志](./docs/CHANGELOG.md)
版本：12.0.1.1 (2019-01-18 更新)

## 说明
该项目仍在Build阶段，目前可以正常使用的功能：
- 免登
- 手动同步钉钉部门与员工
- 业务回调接口
> 其中`业务回调接口`功能业务上只完成了接口的注册部分，在基本功能上，消息体的加密解密已完成，如果急需使用的`业务回调接口`功能的话可以尝试自行编写数据接收业务。我也会加快开发进度，完成一些基本的回调同步业务。

## 额外使用的第三方Python库
- pycryptodome

## 安装步骤
1. 安装模块依赖的第三方Python库
2. 将`/docs/files/http.py`覆盖`odoo-root/odoo/http.py`，其中`odoo-root`表示odoo的根目录
3. 在odoo中安装模块

## 捐赠

如果你觉得这个项目很赞且对你有帮助的话，请我喝一杯咖啡呗:)
![捐赠二维码](./docs/img/donation.png)

## License

[GNU General Public License v3.0](./LICENSE)