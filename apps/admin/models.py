#-*- coding: utf-8 -*-
import datetime
import math

from hashlib import sha1 as sha_constructor
from hashlib import md5 as md5_constructor
from django.utils.encoding import smart_str

from apps.oclib.model import MongoModel
from apps.common.utils import create_gen_id


def get_hexdigest(algorithm, salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or 'crypt').
    """
    raw_password, salt = smart_str(raw_password), smart_str(salt)
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)

    if algorithm == 'md5':
        return md5_constructor(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return sha_constructor(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")

def check_password(raw_password, enc_password):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    algo, salt, hsh = enc_password.split('$')
    return hsh == get_hexdigest(algo, salt, raw_password)


class Moderator(MongoModel):
    """
    管理员
    """
    pk = 'username'
    fields = ['mid','username','password','realname','email','last_ip','last_login','is_staff','permissions', 'in_review']
    ex = 3600 * 24
    def __init__(self):
        self.mid = 0 # 管理员标志
        self.username = "" # 管理员账号
        self.realname = '' # 管理员真实姓名
        self.password = "" # 管理员密码
        self.email = "" # 邮件
        self.last_ip = "0.0.0.0"
        self.last_login = datetime.datetime.now()
        self.is_staff = True #是否是雇员
        self.permissions = "" # 管理员可用权限
        self.in_review = False#帐号注册true为等待审核通过，false为通过审核

    @classmethod
    def get_instance(cls, username):
        obj = super(Moderator,cls).get(username)
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
        M = Moderator()
        M.mid = 0
        M.username = username
        M.password = ''
        M.realname = ''
        M.email = "" # 邮件
        M.last_ip = "0.0.0.0"
        M.last_login = datetime.datetime.now()
        M.is_staff = True #是否是雇员
        M.permissions = "" # 管理员可用权限
        M.in_review = False#帐号注册true为等待审核通过，false为通过审核
        return M

    def set_password(self, raw_password):
        "设置密码"
        self.password = raw_password
        self.put()

    def check_password(self, raw_password):
        "检查密码"
        return self.password == raw_password

    def clear_permissions(self):
        self.permissions = ""
        self.put()

    def set_permissions(self, perms):
        for perm in perms:
            if perm in self.permissions.split(','):
                continue
            else:
                raw = self.get_permissions()
                raw.append(perm)
                self.permissions = ",".join(raw)
                self.put()

    def get_permissions(self):
        "获取全部权限列表"
        if self.permissions.strip() == "":
            return []
        else:
            return self.permissions.lstrip(',').rstrip(',').split(',')

    def has_permission(self, permission):
        "检查是否具备指定权限"
        permissions = self.get_permissions()
        if permission in permissions:
            return True
        else:
            return False

    def has_permissions(self, *perms):
        if self.has_permission("super"):
            return True

        # 检查是否有权限列表中的权限
        for permission in perms:
            if not self.has_permission(permission):
                return False
        return True

    def set_last_login(self, time, ip):
        self.last_login = time
        self.last_ip = ip
        self.put()

    def in_review(self):
        """帐号注册true为等待审核通过，false为通过审核"""
        if not hasattr(self, 'in_review'):
            self.in_review = False
            self.put()
        return self.in_review


class UpdateConfRecord(MongoModel):
    pk = 'rid'
    fields = ['rid','username', 'date','subarea', 'configname', 'REMOTE_ADDR']
    def __init__(self):
        pass

    @classmethod
    def record(cls, username, date, subarea, configname, REMOTE_ADDR):
        obj = cls()
        obj.rid = create_gen_id()
        obj.username = username
        obj.date = str(date)
        obj.subarea = str(subarea)
        obj.configname = configname
        obj.REMOTE_ADDR = REMOTE_ADDR
        obj.put()
        return obj

    @classmethod
    def infos(cls, page=1):
        data = {}
        infos_list = []
        infos = cls.orderby({},[('date', -1)])
        clear_date = str(datetime.datetime.now() - datetime.timedelta(days=30))

        for info in infos[(page - 1) * 10:page * 10]:
            idict = {}
            idict['username']    = info.username
            idict['date']        = str(info.date)[:19]
            idict['subarea']     = info.subarea
            idict['configname']  = info.configname
            idict['REMOTE_ADDR'] = info.REMOTE_ADDR
            if clear_date > info.date:
                info.delete()
            else:
                infos_list.append(idict)
        data['infos_list'] = infos_list
        pages = int(math.ceil(len(infos) / 10.0))
        data['pages'] = range(1, pages + 1)
        return data

