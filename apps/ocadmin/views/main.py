# -*- encoding: utf-8 -*-  

import os
import json
import datetime
import traceback
from django.http import HttpResponse
from apps.ocadmin.menu_config import get_name_perm_dict_by_permissions_list
from apps.ocadmin.menu_config import getmenu_by_moderator
from apps.ocadmin.views import process_response
from django.conf import settings
from apps.models.config import Config
from apps.config import config_update
from apps.config.game_config import game_config
from apps.ocadmin import auth
from apps.ocadmin.models.moderator import OcModerator
import copy
import md5
from apps.ocadmin.decorators import require_permission
from apps.ocadmin.models.role import Role
from apps.ocadmin.models import role
from apps.ocadmin.models.updateconf_record import UpdateConfRecord
from apps.config import config_list

def game_settings_menu(request):
    #获得ocadmin的菜单
    moderator = auth.get_moderator_by_request(request)  
    data = {
        'rc': 0,
    }
    if moderator:
        data['menu'] = getmenu_by_moderator(moderator)
        data['subareas'] = _extra_subareas_config()
    else:
        data['rc'] = 1
        data['msg'] = u'不存在该用户'
    data['head_title'] = settings.APP_NAME
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def add_moderator(request):
    """
     新建管理员
    """
    data = {
        'rc': 0,
        'msg': u'添加成功',
    }
    if request.method == "POST":
        username = str(request.POST.get('username', ''))
        moderator = OcModerator.get(username)
        role = request.POST.get('role', '')
        password = str(request.POST.get('password', ''))
        if moderator:
            data['rc'] = 1
            data['msg'] = u'该帐号已经存在'
        elif not role:
            data['rc'] = 2
            data['msg'] = u'请选择角色'
        elif not password:
            data['rc'] = 3
            data['msg'] = u'请输入密码'
        else:
            moderator = OcModerator.get_instance(username)
            moderator.email = str(request.POST.get('email', ''))
            moderator.last_login = datetime.datetime.now()
            moderator.set_password(password)
            moderator.set_role(role)
            moderator.put()
    else:
        data['rc'] = 1 
        data['msg'] = u'Need POST'
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

def _extra_subareas_config():
    """额外添加一个新区"""
    subareas_conf = copy.deepcopy(game_config.subareas_conf())
    extra_s = str(max([int(s) for s in subareas_conf]) + 1)
    subareas_conf[extra_s] = u'未开放的分区'
    return subareas_conf

def _config_skill_params_by_ruby(config_value, request):
    # 调用ruby的脚本处理ruby_skill_params_config，将得到的最终配置存入skill_params_config

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ruby_script = cur_dir + "/ruby_files/gen_skill.rb"

    in_file_path = "/tmp/qz_admin_in.txt"
    out_file_path = "/tmp/qz_admin_out.txt"

    with open(in_file_path, 'w') as in_file:
        in_file.write(config_value)
        in_file.close()

    ruby_r = os.system("/usr/local/ruby212/bin/ruby {} {} {}".format(ruby_script, in_file_path, out_file_path))
    with open(out_file_path, 'r') as out_file:
        skill_params = out_file.read()
    # ruby脚本成功执行
    if ruby_r or not skill_params:
        return 'ruby-error: skill_params is none'
    request_info = dict(request.REQUEST)
    request_info['config_name'] = "skill_params_config"
    request_info['config_value'] = skill_params.decode('utf-8')
    m = json.loads(save_game_settings(request, request_info).content)
    if m['rc']:
        return 'ruby-error: {}'.format(m['msg'])

    os.remove(in_file_path)
    os.remove(out_file_path)
    return ''

@require_permission
def get_game_settings(request):
    #"""获得系统设置某一项的具体内容
    #"""
    data = {
        'rc': 0,
    }
    config_name = request.REQUEST.get('config_name', '')
    subarea = request.REQUEST.get('zone', '1')
    lExtraSubareas = _extra_subareas_config()

    if not config_name:
        data['rc']  = 1
        data['msg'] = u'请选择要上传的配置' 
    elif not subarea in lExtraSubareas:
        data['rc']  = 2
        data['msg'] = u'请选择正确的分区'
    else:
        sconfig_name = config_list.get_configname_by_subarea(config_name,subarea)
        if not sconfig_name:
            data['rc'] = 3
            data['msg'] = u'不存在该配置'
            return process_response(HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            ))

        config = Config.get(sconfig_name)
        if not config:
            config = Config.create(config_name)
        config_value = config.data
        data['config_value'] = config_value

        uConfigTitle = config_list.get_description(config_name)
        uConfigTitle += '__%s' % config_name + u'||所在分区：' + str(subarea)
        data['config_title'] = uConfigTitle

    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))
    
@require_permission
def save_game_settings(request, request_info=None):
    #"""保存系统设置某一项的具体内容
    #"""
    if not request_info:
        request_info = request.REQUEST
    data = {
        'rc': 0,
    }
    config_name = request_info.get('config_name', '')
    lExtraSubareas = _extra_subareas_config()
    zone = request_info.get('zone', '1')

    subarea_list = zone.split(',')
    u_config_description = config_list.get_description(config_name)
    data['config_title'] = u_config_description
    data['config_title'] += '__%s' % config_name
    if not config_name:
        data['rc']  = 1
        data['msg'] = u'请选择要上传的配置'
    elif not set(subarea_list) | set(lExtraSubareas) == set(lExtraSubareas): 
        data['rc']  = 2
        data['msg'] = u'请选择正确的分区'
    else:
        for subarea in subarea_list:
            sconfig_name = config_list.get_configname_by_subarea(config_name,subarea)
            if not sconfig_name:
                data['rc'] = 3
                data['msg'] = u'不存在该配置'
                return process_response(HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                ))

            config = Config.get(sconfig_name)
            if not config:
                config = Config.create(sconfig_name)
            config_value = request_info['config_value'].encode('utf-8').replace('\r','').strip()
            config.data = config_value
            try:
                if config_name != 'ruby_skill_params_config':
                    verify_info = verify_game_config(config_name, eval(config_value))
                # 通过ruby的配置  简化技能的配置
                else:
                    verify_info = _config_skill_params_by_ruby(config_value, request)
                if verify_info != '':
                    verify_info += ' KeyError'
                    data['rc'] = 3
                    data['msg'] = verify_info
                    return process_response(HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    ))

            except Exception, e:
                print e
                data['rc'] = 4
                data['msg'] = traceback.format_exc()
                return process_response(HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                ))
            config.put()
            config_update(subarea, config_name)

            moderator = auth.get_moderator_by_request(request)
            username,date,subarea,configname,REMOTE_ADDR = moderator.username,datetime.datetime.now(),subarea, data['config_title'], request.META["REMOTE_ADDR"]
            UpdateConfRecord.record(username, date, subarea, configname, REMOTE_ADDR)

        data['config_value'] = config_value        
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

def verify_game_config(config_name, value):
    """
    用于验证配置是否正确
    """
    verify_dict = {
        'system_config': ['maintenance', 'version'],#key为配置名称，value为该配置名称必须存在的key
        'loginbonus_config': ['bonus'],
        'shop_config': ['sale'],
        'user_level_config': ['1'],
        'gacha_config': ['gold_rate', 'charge_rate',],
        'card_config': ['1_card', ],
        'card_level_config': ['exp_type', ],
        'card_update_config': ['cost_gold', ],
        'monster_config': [],
        'dungeon_config': ['1', ],
        'normal_dungeon_effect_config': ['rule', ],
    }

    verify_info = ''
    if config_name in verify_dict:
        for verify_value in verify_dict[config_name]:
            if not verify_value in value:
                verify_info = config_name + " miss '" + verify_value + "'"

    #战场掉落敌将，而在敌将配置中未配置的验证
    #dcverify = verify_dungeon_config(config_name, value)
    #if dcverify:
    #    return dcverify
    return verify_info

def verify_dungeon_config(config_name, value):
    #"""战场掉落敌将，而在敌将配置中未配置的验证
    #"""
    if config_name == 'dungeon_config':
        for dungeon_floor in value:
            mdset = set(value[dungeon_floor]['monster_drop'].keys())
            mset = set(game_config.monster_config.keys())
            if mdset & mset != mdset:
                vdresult = mdset - (mdset & mset)
                if vdresult:
                    for mid in vdresult:
                        return "敌将配置__monster_config 缺少配置ID：" + str(mid)
    return ''

def login(request):
    """
        首页，登录用
    """
    appname = settings.APP_NAME
    data = {
        'rc': 0,
    }
    if request.method == "POST":
        username = str(request.POST.get("username"))
        password = str(md5.md5(str(request.POST.get("password"))).hexdigest())
        if not username or not password:
            data['rc'] = 1
            data['msg'] = '帐号或密码错误'
        else:
            moderator = auth.get_moderator_by_username(username)
            if moderator is None:
                data['rc'] = 3
                data['msg'] = u'帐号错误'
            else:
                if not moderator.check_password(password):
                    data['rc'] = 4
                    data['msg'] = u'密码错误'
    else:
        data['rc'] = 2
        data['msg'] = 'Need POST'

    if data['rc'] == 0:
        cv = auth.cv(request, moderator)
        data['moderator'] = cv
    response = HttpResponse(json.dumps(data, indent=1),content_type='application/x-javascript',)
    return process_response(response)

@require_permission
def moderator_list(request):
    """
    管理员列表
    """
    mod_list = OcModerator.find({})
    data = {
        'rc': 0,
    }
    data['moderator_list'] = []
    for mobj in mod_list:
        data['moderator_list'].append({
            'username': mobj.username,
            'email': mobj.email,
            'role': mobj.role[-1],
            'last_ip': mobj.last_ip,
            'last_login_date': mobj.last_login.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return process_response(
        HttpResponse(
            json.dumps(data, indent=1),
            content_type='application/x-javascript',
        )
    )

@require_permission
def get_roles_list(request):
    data = {
        'rc': 0,
    }
    data['roles_list'] = role.get_roles_rname()
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def add_roles(request):
    data = {
        'rc': 0,
        'msg': u'添加成功',
    }
    roleName = request.REQUEST.get('roleName', '')
    permissions = str(request.REQUEST.get('permissions', ''))
    if permissions and roleName:
        r_obj = Role.get(roleName)
        if r_obj:
            data['rc'] = 3
            data['msg'] = u'已经存在该角色名称'
        else:
            r_obj = Role.getbyrname_instance(roleName)
            permissions_list = permissions.split(',')
            r_obj.permissions_list = permissions_list
            r_obj.put()
    elif not permissions:
        data['rc'] = 1
        data['msg'] = u'请选择功能'
    elif not roleName:
        data['rc'] = 2
        data['msg'] = u'请输入角色名称'
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def del_moderator(request):
    data = {
        'rc': 0,
        'msg': u'成功删除该帐号',
    }
    accountName = request.REQUEST.get('accountName', '')
    moderator = OcModerator.get(accountName)
    if moderator:
        moderator.delete()
    else:
        data['rc'] = 1
        data['msg'] = u'不存在该帐号'

    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def del_role(request):
    data = {
        'rc': 0,
        'msg': u'成功删除该角色',
    }
    rname = request.REQUEST.get('roleName', '')
    r_obj = Role.get(rname)
    if r_obj:
        r_obj.delete()
    else:
        data['rc'] = 1
        data['msg'] = u'不存在该角色'
    
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def manage_role(request):
    data = {
        'rc': 0,
    }
    roleName = request.REQUEST.get('roleName', '')
    r_obj = Role.get(roleName)
    if not r_obj:
        data['rc'] = 1
        data['msg'] = u'不存在该角色'
    else:
        data['info'] = get_name_perm_dict_by_permissions_list(r_obj.permissions_list)
    data['roleName'] = roleName
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def edit_role(request):
    data = {
        'rc': 0,
        'msg': u'修改成功',
    }
    roleName = request.REQUEST.get('roleName', '')
    r_obj = Role.get(roleName)
    permissions = str(request.REQUEST.get('editPermissions', ''))
    if permissions and r_obj:
        r_obj = Role.getbyrname_instance(roleName)
        permissions_list = permissions.split(',')
        r_obj.permissions_list = permissions_list
        r_obj.put()
    elif not permissions:
        data['rc'] = 1
        data['msg'] = u'请选择权限'
    elif not r_obj:
        data['rc'] = 2
        data['msg'] = u'不存在该角色'
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def add_roles(request):
    data = {
        'rc': 0,
        'msg': u'添加成功',
    }
    roleName = request.REQUEST.get('roleName', '')
    permissions = str(request.REQUEST.get('permissions', ''))
    if permissions and roleName:
        r_obj = Role.get(roleName)
        if r_obj:
            data['rc'] = 3
            data['msg'] = u'已经存在该角色名称'
        else:
            r_obj = Role.getbyrname_instance(roleName)
            permissions_list = permissions.split(',')
            r_obj.permissions_list = permissions_list
            r_obj.put()
    elif not permissions:
        data['rc'] = 1
        data['msg'] = u'请选择功能'
    elif not roleName:
        data['rc'] = 2
        data['msg'] = u'请输入角色名称'
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def manage_moderator(request):
    data = {
        'rc': 0,
        'info': {}
    }
    accountName = request.REQUEST.get('accountName', '')
    moderator = OcModerator.get(accountName)
    if not moderator:
        data['rc'] = 1
        data['msg'] = u'不存在该帐号'
    else:
        data['info']['accountName'] = accountName
        if moderator.role:
            data['info']['role'] = moderator.role[-1]
        else:
            data['info']['role'] = ''
        data['info']['email'] = moderator.email

    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def edit_moderator(request):
    data = {
        'rc': 0,
        'msg': u'修改成功'
    }
    accountName = request.REQUEST.get('accountName', '')
    moderator = OcModerator.get(accountName)
    roleName = request.REQUEST.get('roleName', '')
    if not roleName:
        data['rc'] = 1
        data['msg'] = u'请选择有效的角色'
    elif not moderator:
        data['rc'] = 2
        data['msg'] = u'不存在该帐号'
    else:
        password = request.REQUEST.get('password', '')
        email    = request.REQUEST.get('email', '')
        if password:
            moderator.set_password(password)
        if email:
            moderator.set_email(email)
        moderator.set_role(roleName)
        
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def updateconfig_record(request):
    page = int(request.POST.get('page', '1'))
    data = {
        'rc': 0,
    }
    uinfos = UpdateConfRecord.infos(page)
    data['infos'] = uinfos['infos_list']
    data['pages'] = uinfos['pages']
    if data['pages']:
        data['max_page'] = uinfos['pages'][-1]
    else:
        data['max_page'] = 0
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def change_password(request):
    data = {
        'rc': 0,
        'msg': u'修改成功',
    }
    newPassword = str(request.POST.get('newPassword', ''))
    if not newPassword:
        data['rc'] = 1
        data['msg'] = u'请输入密码'
    else:
        moderator = auth.get_moderator_by_request(request)
        moderator.set_password(newPassword)
        
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )) 

def head_title(request):
    data = {
        'rc': 0,
        'msg': u'修改成功',
    }
    data['head_title'] = settings.APP_NAME
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))
