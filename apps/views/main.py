#-*- coding: utf-8 -*-

import copy
import md5
import time
import urllib2

from django.http import HttpResponse
from django.conf import settings

from apps.common.decorators import maintenance_auth
from apps.common.decorators import platform_auth
from apps.common.decorators import platform_bind
from apps.common.decorators import server_close_auth
from apps.common.decorators import session_auth
from apps.common.decorators import set_user
from apps.common.decorators import signature_auth
from apps.config.config_version import get_config_version
from apps.config.game_config import game_config
from apps.common.utils import create_sig
from apps.common.utils import get_msg
from apps.common.utils import get_uuid
from apps.logics import process_api
from apps.models import data_log_mod
from apps.models.session import Session
from apps.oclib.utils import rkjson as json


def subareas_conf(request):
    return HttpResponse(
        json.dumps(game_config.subareas_conf(),
                   indent=1),
        content_type='application/x-javascript',
    )


@signature_auth
@maintenance_auth
@session_auth
@set_user
@server_close_auth
def api(request):
    data = {}
    
    now = int(time.time())
    data['data'] = {
                    'server_now':now,
                    'cag':create_sig(str(now)),
                    'cog':md5.new(str(now) + 'random_kk').hexdigest()
                    }
    rc,func_data = process_api(request)

    data['data'].update(func_data)
    data['rc'] = rc
    print "~" *10 + "use_time", request.REQUEST.get("method", None), time.time() - now
    return HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )


@signature_auth
@maintenance_auth
@platform_auth
@server_close_auth
def index(request):
    """ 应用首页,输出top page"""
    
    data = {
        'rc':0,
        'data':{
         'server_now':int(time.time()),
         'pid':request.rk_user.pid,
         'uid':request.rk_user.uid,
         # 'newbie': False,
         # 'newbie_step': 10,
         'username':request.rk_user.username,
        }
    }
    if request.rk_user.is_new:
#        invite_code = request.REQUEST.get('invite_code')
#        _record_invite_code(request.rk_user,invite_code)
        if request.rk_user.platform == 'oc':
            data['data']['oc_openid'] = request.rk_user.account.openid
            data['data']['oc_access_token'] = request.rk_user.account.access_token
#    #设备唯一标识
#    mac_addr = request.REQUEST.get("uuid", "")
#    if mac_addr and mac_addr not in request.rk_user.client_macaddr:
#        request.rk_user.add_client_macaddr(mac_addr)
#    #下载渠道标识
#    mktid = request.REQUEST.get("mktid", "")
#    if mktid and mktid not in request.rk_user.mktids:
#        request.rk_user.add_mktid(mktid)
    data_log_mod.set_log('LoginRecord', request.rk_user, **{'version': request.REQUEST.get('version', '')})
    return HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )


@signature_auth
@maintenance_auth
@platform_bind
def account_bind(request):
    """

    # TODO(GuoChen) 未知的功能，前端有此接口的代码，待确认
    """
    
    data = {
        'rc': 0,
        'data': {
            'server_now': int(time.time()),
            'pid': request.rk_user.pid,
            'msg': '',
        }
    }
    # 是否有绑定帐号奖励
    request.rk_user.user_property.get_bind_weibo_award()
    return HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )

    
@signature_auth
@session_auth
@set_user
def get_access_token(request):
    #用于刷新access_token用的refresh token
    data = {
            'rc':0,
            'data':{}
            }
    para_pid = request.REQUEST.get('pid',None)
    para_platform = request.REQUEST.get('platform',None)
    session_dic = Session.new_get(para_platform+':'+para_pid)
    pid = session_dic['pid']
    access_token = session_dic['access_token']
    refresh_token = session_dic['refresh_token']
    expires_time = session_dic['expires_time']
    if not pid and not access_token and not refresh_token and not expires_time:
        data = {
                'rc':8,
                'data':{
                      'msg':get_msg('login','server_exception'),
                      'server_now':int(time.time()),
                      }
                }
        return HttpResponse(
            json.dumps(data, indent=1),
            content_type='application/x-javascript',
        )

    else:
        if expires_time > time.time():
            data['data']['access_token'] = access_token
            data['data']['pid'] = request.rk_user.account.openid
            data['data']['uid'] = request.rk_user.uid
            data['data']['nickname'] = request.rk_user.baseinfo['username']
        else:
            client_id = settings.APP_KEY_360
            client_secret = settings.APP_SECRET_KEY_360
            oauth2_url = "https://openapi.360.cn/oauth2/access_token?grant_type=refresh_token&refresh_token=%s&client_id=%s&client_secret=%s&scope=basic" %(refresh_token, client_id, client_secret)
            url_request = urllib2.urlopen(oauth2_url, timeout=12)
            code, res = url_request.code, url_request.read()
            if code == 200:
                res_dict = json.loads(res)
                data['data']['access_token'] = str(res_dict['access_token'])
                data['data']['pid'] = request.rk_user.account.openid
                data['data']['uid'] = request.rk_user.uid
                data['data']['nickname'] = request.rk_user.baseinfo['username']
                expires_time = time.time() + float(res_dict['expires_in'])
                Session.set(para_platform, pid, str(res_dict['access_token']), str(res_dict['refresh_token']), expires_time)
            else:
                data = {
                        'rc':8,
                        'data':{
                              'msg':get_msg('login','server_exception'),
                              'server_now':int(time.time()),
                              }
                        }
    data['data']['server_now'] = int(time.time())
    return HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    )

    
def setConfigUpdateTime(subarea):
    #"""设置配置的时间
    #"""
    #武将配置
    #get_config_version
    need_record_configs = [
        "config",

        "card_config",
        "monster_config",
        # "city_config",
        "equip_config",
        "skill_params_config",      # 技能的配置
        "material_config",
        "system_config",

        "card_desc_config",
        "skill_desc_config",
        "equip_desc_config",
        # "dungeon_desc_config",
        "material_desc_config",
        "props_desc_config",


        "language_config",

    ]

    update_time_records = {}
    for config_name in need_record_configs:
        update_time_records[config_name] = get_config_version(subarea, config_name)
    return update_time_records


def info(request):
    """获取一些不重要的系统信息，和配置版本号

    获取当前游戏版本号、一些是否可以通过平台登入的开关、
    一些常用配置和各语言包的最后更新时间，前端可以比较这些
    时间判断是否需要发请求更新本地的一些配置
    
    """
    
    params = request.REQUEST
    subarea = params.get("subarea", "1") or '1'
    game_config.set_subarea(subarea)
    # config_update_time = get_config_version(subarea, 'config')
    # if not config_update_time:
    #     up_value = int(time.time())
    # else:
    #     up_value = int(config_update_time)
    update_time_records = setConfigUpdateTime(subarea)

    data = {
        'openid': get_uuid(),
        'version':game_config.system_config['version'],
        'app_url':game_config.system_config['app_url'],
        'server_now':int(time.time()),

        #False for now -- 2014/10/22 Xu Changsen
        'qq_account':game_config.system_config.get('qq_account',False),
        'sina_account':game_config.system_config.get('sina_account',False),

        'fb_account':game_config.system_config.get('fb_account',False),
        'oc_account':game_config.system_config.get('account_assign_switch',False),
        #added 2014/10/22 Xu Changsen
        'qihoo360_account':game_config.system_config.get('qihoo360_account',False),
        'baidu91_account':game_config.system_config.get('baidu91_account',False),


        'christmas':game_config.system_config.get('christmas',False),
        'open_invite':game_config.invite_config.get('open_invite',False),
        'skin_type': game_config.system_config.get('skin_type', ''),#皮肤的样子

        "up_value": update_time_records["config"],
        
        "cup_value": update_time_records["card_config"],
        "mup_value": update_time_records["monster_config"],
        "sup_value": update_time_records["system_config"],
        # "cityup_value": update_time_records["city_config"],
        "equp_value": update_time_records["equip_config"],
        "skill_params_value": update_time_records["skill_params_config"],
        "materialup_value": update_time_records["material_config"],

        'card_desc_version': str(update_time_records["card_desc_config"]),
        'skill_desc_version': str(update_time_records["skill_desc_config"]),
        'equip_desc_version': str(update_time_records["equip_desc_config"]),
        # 'dungeon_desc_version': str(update_time_records["dungeon_desc_config"]),
        'mat_item_desc_version': str(update_time_records["material_desc_config"]),
        "props_desc_config": str(update_time_records["props_desc_config"]),

        'language_version': str(update_time_records["language_config"]),


        'share_image_version':game_config.system_config.get('share_image_version', '100'),
    }
    res_version = params.get('ver', '')
    if res_version:
        res_url, res_ver = get_res_url(res_version, game_config)
        data["res_url"] = res_url
        data["res_ver"] = res_ver
        # 安卓的fb登录标识
        if 'fb_account' in game_config.android_config:
            data['fb_account'] = game_config.android_config['fb_account']
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )


# @signature_auth
# @maintenance_auth
# @session_auth
# @set_user
# def tutorial(request):
    
#     rk_user = request.rk_user
#     version = float(request.REQUEST.get('version','1.0'))
#     rc,res_dic = tutorial_logic_1_5(rk_user,request.REQUEST)
#     res_dic['version'] = game_config.system_config['version']
#     res_dic['server_now'] = int(time.time())
#     res_dic['user_info'] = rk_user.wrapper_info()
#     data = {
#             'rc':rc,
#             'data':res_dic,
#             }
#     return HttpResponse(
#             json.dumps(data, indent=1),
#             content_type='application/x-javascript',
#         )


def language_version(request):
    """
    返回当前语言包信息
    """
    
    data = {
        'rc':0,
        'data':game_config.language_config
        }
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )


def get_material_item_desc_config(request):
    #"""获得材料道具的描述配置
    #"""
    
    data = {
              'rc':0,
              'data':copy.deepcopy(game_config.material_desc_config),
           }
    # data['data'].update(game_config.item_desc_config)
    data['data'].update(game_config.props_desc_config)
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )


def get_card_desc_config(request):
    #"""获得武将的描述配置
    #"""
    
    data = {
               'rc':0,
               'data':game_config.card_desc_config,
          }
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )


def get_equip_desc_config(request):
    #"""获得装备的描述配置
    #"""
    
    data = {
            'rc':0,
            'data':game_config.equip_desc_config,
          }
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )


def get_skill_desc_config(request):
    #"""获得技能的描述配置
    #"""
    
    data = {
            'rc':0,
            'data':game_config.skill_desc_config,
          }
    return HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            )


# def get_dungeon_desc_config(request):
#     #"""获得战场的描述配置
#     #"""
    
#     data = {
#             'rc':0,
#             'data':game_config.dungeon_desc_config,
#           }
#     return HttpResponse(
#                 json.dumps(data, indent=1),
#                 content_type='application/x-javascript',
#             )


def get_res_url(res_version, game_config):
    #获得资源链接列表地址，及资源的版本号
    res_url_online = game_config.system_config.get("res_url_online", {})
    res_version = str(float(res_version))
    if res_url_online and res_version in res_url_online:
        res_url = res_url_online.get(res_version, {}).get('url', '')
        res_ver = res_url_online.get(res_version, {}).get('res_version', '')
    else:
        res_url = ''
        res_ver = ''
    return res_url, res_ver


def crossdomain(request):
    return HttpResponse("""
        <?xml version="1.0"?>
        <cross-domain-policy>
        <allow-access-from domain="*" />
        </cross-domain-policy>
    """)
