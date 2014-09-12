#-*- coding: utf-8 -*-

from apps.oclib.model import MongoModel
from apps.ocadmin.menu_config import getname_by_permissions

class Role(MongoModel):
    pk = 'rname'
    fields = ['rname','permissions_list', ]
    def __init__(self):
        self.rname = ''
        #if 'super' in self.permissions_list then can do everything
        self.permissions_list = []

    @classmethod
    def getbyrname_instance(cls, username):
        obj = super(Role,cls).get(username)
        if obj is None:
            obj = cls.create(username)
        return obj

    @classmethod
    def create(cls, username):
        M = Role()
        M.rname = username
        M.permissions_list = [] 
        M.put()
        return M

s = u'超级管理员'
r = Role.get(s)
if not r:
    r = Role.getbyrname_instance(s)
    r.permissions_list = ['super']
    r.put()
del r
del s

def get_roles_list():
    roles_find = Role.find({})
    roles_list = []
    for r_obj in roles_find:
        roles_list.append({
            'cnname': r_obj.rname,
            'permissions_list': r_obj.permissions_list
        })
    return roles_list

def get_roles_rname():
    roles_find = Role.find({})
    roles_list = []
    for r_obj in roles_find:
        permissions_list = r_obj.permissions_list
        roles_list.append({
            'cnname': r_obj.rname,
            'pname': getname_by_permissions(permissions_list),
        })
    return roles_list
