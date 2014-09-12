#-*- coding: utf-8 -*-
import datetime
import time
import copy
from apps.common import utils
from apps.config import game_config
from apps.common import AESM2Encrypt
from apps.models.user_login import UserLogin
from apps.oclib import app
from django.conf import settings

def process_api(request):
    """ 
    功能描述:分发处理请求
    参数说明:HttpRequest
    返回说明:dict
    """
    #读取模板文件
    data = {}
    rk_user = request.rk_user
    params = request.REQUEST
    method = params.get('method','')
    if not method:
        return 6,{'msg':''}
    sig = params.get('sig','')
    if not sig:
        return 6, {'msg':utils.get_msg('login','refresh')}
    print '%s %s active uid:' % (str(datetime.datetime.now()),method),rk_user.uid
    #自动检测外挂功能
#    auto_scan_fg = game_config.system_config.get('auto_scan',False)
#    now_version = request.REQUEST.get('version','')
#    review_version = game_config.system_config.get('review_version','')
#    is_review = review_version and float(now_version) == float(review_version)
#    if auto_scan_fg and (not is_review ):
#        strMD5 = str(params.get("org", "none"))
#        strDecryptMD5 = ""
#        if strMD5 != "none":
#            #客户端传来的+变空格了
#            strMD5 = strMD5.replace(" ", "+")
#            decrypt_res = AESM2Encrypt.decryptEx(strMD5 + "==")
#            msg = utils.get_msg('login', 'illegal_md5')
#            if not decrypt_res:
#                return 1, {'msg':msg}
#            strDecryptMD5 = decrypt_res[0:9]
#            decrypt_timestamp = decrypt_res[9:15]
#            if abs(int(decrypt_timestamp) - int(str(int(time.time()))[-6:]))\
#            > settings.AUTH_AGE:
#                return 1, {'msg':utils.get_msg('login','refresh')}
#            print 'org_new %s %s' % (str(rk_user.uid),strDecryptMD5)
#            if strDecryptMD5 != "":
#                scan_type = game_config.system_config.get('scan_type','white')
#                if scan_type == 'white':
#                    scan_white_list = game_config.system_config.get('scan_white_list',[])
#                    if scan_white_list and strDecryptMD5 not in scan_white_list:
#                        return 1, {'msg':msg}
#                else:
#                    scan_black_list = game_config.system_config.get('scan_black_list',[])
#                    if strDecryptMD5 in scan_black_list:
#                        return 1, {'msg':msg}
#            else:
#                return 1, {'msg':msg}
#        else:
#            msg = utils.get_msg('login', 'new_version')
#            return 1, {'msg':msg}
    #版本是否已更新
    if not request.REQUEST.get('version') or (float(request.REQUEST['version']) \
    < float(game_config.system_config.get('version','1.00')) ):
        return 13,{'msg':utils.get_msg('login','new_version')}    
#    white_list = ['main.get_config','friend.add_request',
#                  "main.get_card_config", "main.get_monster_config",'main.get_equip_config',
#                  'main.get_item_config','main.get_material_config','main.index']
    #如果用户没有合法进行新手引导，返回
#    black_list = ['dungeon.start','dungeon.end']
#    if rk_user.user_property.newbie and method in black_list:
#        return 4,{'msg':utils.get_msg('login', 'server_exception')}
    #旧版本客户端不提供服务
#    if not request.REQUEST.get('version') or (float(request.REQUEST['version']) \
#    < float(game_config.system_config.get('version','1.00')) and method != 'dungeon.end' and method != 'pvp.end'):
#        return 13,{'msg':utils.get_msg('login','new_version')}

    bl_model_str, bl_func_str = method.split('.')[0],method.split('.')[1]
    bl_obj = __import__(bl_model_str,globals(),locals())
    bl_func = getattr(bl_obj, bl_func_str)

#   #重试时特殊处理
#   retry = params.get('rty','')
#   md_ls = [
#            'gacha.charge','gacha.free','gacha.charge_multi','gacha.free_multi',
#            'card.update','card.upgrade',
#            'card.sell','card.extend_num','card.set_decks',
#            'city.upgrade','city.produce_item','city.produce_equip',
#            'city.extend_store_num','city.set_item_deck','city.receive',
#            'city.store_sell','pvp.start','pvp.end','dungeon.revive','dungeon.end'

#            ]
#   ul = UserLogin.get_instance(rk_user.uid)
#   api_retry = copy.deepcopy(ul.login_info.get('api_retry',{}))
#   if api_retry and retry and method in md_ls:
#       last_retry = api_retry.get('retry','')
#       last_method = api_retry.get('method','')
#       last_retry_cnt = api_retry.get('retry_cnt',0)
#       last_data = api_retry.get('data',{})
#       last_rc = api_retry.get('rc',0)
#       if last_retry == retry and \
#         last_method == method and \
#         last_retry_cnt < 5:
#           data.update(last_data)
#           data['user_info'] = rk_user.wrapper_info()
#           last_retry_cnt += 1
#           api_retry['retry_cnt'] = last_retry_cnt
#           ul.login_info['api_retry'] = api_retry
#           ul.put()
#           return last_rc,data
#       else:
#           ul.login_info['api_retry'] = {}
#           ul.put()

    rc, func_data = bl_func(rk_user, params)
    if rc == 0:
        data.update(func_data)

#   if rc != 0:
#       #rc异常时,清空storage
#       app.pier.clear()

#   if method in md_ls:
#       ul = UserLogin.get_instance(rk_user.uid)
#       ul.login_info['api_retry'] = {'retry':retry,'method':method,'data':func_data,'rc':rc,'retry_cnt':0}
#       ul.put()
#   #用户信息
#   data['user_info'] = rk_user.wrapper_info()

    return rc, data
