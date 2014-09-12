# -*- encoding: utf-8 -*-  

import copy
from apps.config import config_list

g_l_commongameconfig_menu = []
g_l_gameconfig_menu       = []
g_d_gameconfig_submenu    = {
    'system_config_type': {
        'name': u'系统配置',
        'sub_menu': [],
    },
    'general_type':{
        'name': u'武将类',
        'sub_menu': [],
    },
    'battleground_type':{
        'name': u'战场类',
        'sub_menu': [],
    },
    'operate_type':{
        'name': u'运营活动类',
        'sub_menu': [],
    },
    'equip_type':{
        'name': u'装备素材类',
        'sub_menu': [],
    },
}


for d_configinfo in config_list.g_lConfig:
    use_subarea = d_configinfo['use_subarea']
    if use_subarea:
        str_belongsmenu = d_configinfo.get('belongs_menu', 'system_config_type')
        if not str_belongsmenu in g_d_gameconfig_submenu:
            g_d_gameconfig_submenu[str_belongsmenu] = {'sub_menu': []}
        g_d_gameconfig_submenu[str_belongsmenu]['sub_menu'].append({
            'name_en': d_configinfo['name'],
            'name'   : d_configinfo['description']
        })
    else:
        g_l_commongameconfig_menu.append({
            'name_en': d_configinfo['name'],
            'name'   : d_configinfo['description'],
        })
for str_configtype in g_d_gameconfig_submenu:
    g_d_gameconfig_submenu[str_configtype]['name_en'] = str_configtype
    g_l_gameconfig_menu.append(
        g_d_gameconfig_submenu[str_configtype]
    )

g_d_menu = {
    'admin_manage': {
        "name":"管理员管理",
        'permissions': 'super',
    },
    'password_change': {
        "name":"修改帐号密码",
        'permissions': 'all',
    },
    'common_game_config': {
        "name": '通用游戏配置',
        'permissions': 'submit_setting',
        "sub_menu": g_l_commongameconfig_menu,
    },
    'view_game_user':{
        "name": '查看玩家信息',
        'permissions': 'view_users',
    },
    'game_user_edit':{
        "name": '修改玩家信息',
        'permissions': 'edit_users',
    },
    'game_config':{
        "name": '游戏设置',
        'permissions': 'submit_setting',
        "sub_menu": g_l_gameconfig_menu,
    },
}

permissions_path_map = {
    'submit_setting': [
        '/ocadmin/game_setting/', 
        '/ocadmin/save_game_settings/', 
        '/ocadmin/get_game_settings/', 
        '/ocadmin/file/upload_config/', 
        '/ocadmin/config/record/'
    ],
    'view_users': [
        '/ocadmin/user/view/'
    ],
    'edit_users': [
        '/ocadmin/user/edit/',
    ],
    'all':[
        '/ocadmin/change_password/',
    ],
}

def getmenu_by_moderator(moderator):
    d_menu = {}
    dpmconfig = copy.deepcopy(g_d_menu)
    mpermissions = moderator.permissions()
    for m in dpmconfig:
        menu_permissions = dpmconfig[m]['permissions']
        if menu_permissions in mpermissions or menu_permissions == 'all' or 'super' in mpermissions:
            d_menu[m] = {}
            d_menu[m]['name'] = dpmconfig[m]['name']
            d_menu[m]['permissions'] = dpmconfig[m]['permissions']
            d_menu[m]['name_en'] = m
            if menu_permissions in ['submit_setting', 'common_game_config']:
                d_menu[m]['sub_menu'] = dpmconfig[m]['sub_menu']
    return d_menu

def getname_by_permissions(permissions_list):
    pname = ''
    dpmconfig = copy.deepcopy(g_d_menu)
    for m in dpmconfig:
        menu_permissions = dpmconfig[m]['permissions']
        if menu_permissions in permissions_list:
            pname += dpmconfig[m]['name'] + ','
    return pname

def get_name_perm_dict_by_permissions_list(permissions_list):
    name_perm_data = {}
    dpmconfig = copy.deepcopy(g_d_menu)
    for m in dpmconfig:
        menu_permissions = dpmconfig[m]['permissions']
        if menu_permissions in permissions_list:
            name_perm_data[menu_permissions] = dpmconfig[m]['name']
    return name_perm_data

def get_path_by_permission(permission_list):
    path_list = []
    for permission in permissions_path_map:
        if permission in permission_list:
            path_list += permissions_path_map[permission]
    return path_list
