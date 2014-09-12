# -*- coding: utf-8 -*-
import re
import admin_config


class AdminConfiguration(object):
    """
    管理端配置类
    """
    def __init__(self):
        super(AdminConfiguration,self).__init__()
        self.all_permissions = {}
        self.view_perm_mappings=ViewPermMappings()
        self.configure()

    def configure(self):
        # permissions
        for perm in admin_config.permissions:
            self.all_permissions[perm["code"]] = perm
        # viewpermmappings
        self.view_perm_mappings.configure(admin_config.views_perms_mappings)

        # admin secret key
        self.ADMIN_SECRET_KEY = admin_config.ADMIN_SECRET_KEY


class RegexUrlPermissionPattern(object):
    """
        view路径和Permissions的设置
    """
    def __init__(self, regex, permissions = None):
        self.regex = re.compile(regex,re.UNICODE)
        self.permissions = permissions

    def is_allow(self,path,moderator):
        "是否允许指定管理员访问"

        # 检查是否路径匹配
        match = self.regex.search(path)
        if not match:
            return False

        if isinstance(self.permissions,basestring):
            if self.permissions=="all":
                return True

        if moderator.has_permissions(self.permissions):
            return True

        return False


class IndexPathPermissionPattern(object):
    def __init__(self,path,name,order = 0,permissions=None):
        self.path = path # 路径
        self.name = name # 名称
        self.order = order # 排序规则
        self.permissions = permissions # 权限限制

    def is_allow(self,moderator):

        #任意管理员皆可访问
        if isinstance(self.permissions,basestring):
            if self.permissions=="all":
                return True

        if moderator.has_permissions(self.permissions):
            return True
        return False


class ViewPermMappings(object):
    """
    View Path Permissions映射关系
    """
    def __init__(self):
        self.mapping_list = []
        self.index_list=[]

    def configure(self,mappings_data):
        "配置"
        for index in mappings_data["index"]:
            path = index.get("path")
            name = index.get("name")
            order = index.get("order",0)
            perms = index.get("permissions")
            self.index_list.append(IndexPathPermissionPattern(path,name,order,perms))

        for map in mappings_data["mappings"]:
            regex = map.get("path",None)
            permissions = map.get("permissions",None)
            self.mapping_list.append(RegexUrlPermissionPattern(regex,permissions=permissions))

    def is_view_allow(self,view_path,moderator):
        "检查指定的view url是否允许"

        for map in self.mapping_list:
            if map.is_allow(view_path,moderator):
                return True

        return False

    def get_allow_index_paths(self,moderator):
        "获取给定的用户允许的view url列表"
        paths = []
        for index in self.index_list:
            if index.is_allow(moderator):
                paths.append(index)

        sorted(paths,key=lambda path:path.order,reverse=True)
        return paths

admin_configuration = AdminConfiguration()


def get_all_permissions():
    """
    获取全部权限列表
    """
    return admin_configuration.all_permissions

def get_permissions_by_codes(codes):
    """
    基于code列表返回对应的权限列表
    """
    perms = []
    for code in codes:
        perms.append(admin_configuration.all_permissions[code])
    return perms

def get_permission(code):
    "返回权限,注意，perm是个字典"
    return admin_configuration.all_permissions[code]
