#-*- coding: utf-8 -*-

import datetime
import md5
from apps.oclib.model import MongoModel
from apps.ocadmin import admin_config
from apps.ocadmin.models import role
from apps.ocadmin import menu_config

class OcModerator(MongoModel):
    """
    管理员
    """
    pk = 'username'
    fields = ['username','mid', 'password','email','last_ip','last_login','role', 'in_review']
    def __init__(self):
        self.mid = 0 # 管理员标志
        self.username = "" # 管理员账号
        self.password = "" # 管理员密码
        self.email = "" # 邮件
        self.last_ip = "0.0.0.0"
        self.last_login = datetime.datetime.now()
        self.role = [] # 管理员可用权限
        self.in_review = False#帐号注册true为等待审核通过，false为通过审核

    @classmethod
    def get_instance(cls, username):
        obj = super(OcModerator,cls).get(username)
        if obj is None:
            obj = cls._install(username)
        return obj

    @classmethod
    def _install(cls, username):
        obj = cls.create(username)
        moderator_list = obj.find({})
        if moderator_list:
            obj.mid = max([i.mid for i in moderator_list])+1
        else:
            obj.mid = 1
        obj.put()
        return obj

    @classmethod
    def create(cls, username):
        M = OcModerator()
        M.mid = 0
        M.username = username
        M.password = ''
        M.email = "" # 邮件
        M.last_ip = "0.0.0.0"
        M.last_login = datetime.datetime.now()
        M.role = [] # 管理员可用权限
        M.in_review = False#帐号注册true为等待审核通过，false为通过审核
        return M

    def set_password(self, raw_password):
        "设置密码"
        self.password = md5.md5(raw_password).hexdigest()
        self.put()

    def check_password(self, raw_password):
        "检查密码"
        return str(self.password) == str(raw_password)

    def set_role(self, role):
        self.role = [role]
        self.put()

    def set_last_login(self, time, ip):
        self.last_login = time
        self.last_ip = ip
        self.put()

    def permissions(self):
        roles_list = role.get_roles_list()
        for rinfo in roles_list:
            rname = rinfo['cnname']
            if rname in self.role:
                return rinfo['permissions_list']
        return []

    def allow_paths(self, path):
        fg = False
        permission_list = self.permissions()
        if 'super' in permission_list:
            fg = True
        else:
            path_list = menu_config.get_path_by_permission(permission_list)
            if path in path_list:
                fg = True
        if not fg:
            print('path is :', path, ' permissions is :', permission_list, ' you can set "permissions_path_map" in apps/ocadmin/menu_config.py ')
        return fg

    def set_email(self, email):
        self.email = email
        self.put()
