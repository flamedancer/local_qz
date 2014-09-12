#-*- coding: utf-8 -*-
import datetime
import time
import copy
from apps.common import utils
from apps.config.game_config import game_config
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
    if not request.REQUEST.get('version') or (float(request.REQUEST['version']) \
    < float(game_config.system_config.get('version','1.00')) and method != 'dungeon.end'):
        return 13,{'msg':utils.get_msg('login','new_version')}    
    bl_model_str,bl_func_str = method.split('.')[0],method.split('.')[1]
    bl_obj = __import__(bl_model_str,globals(),locals())
    bl_func = getattr(bl_obj, bl_func_str)
    #重试时特殊处理
    retry = params.get('rty','')
    md_ls = [
             'gacha.charge','gacha.gold','gacha.charge_multi','gacha.gold_multi',
             'card.update','card.upgrade',
             'card.sell','card.extend_num','card.set_decks',
             'pvp.start','pvp.end','dungeon.revive','dungeon.end'

             ]
    ul = UserLogin.get_instance(rk_user.uid)
    api_retry = copy.deepcopy(ul.login_info.get('api_retry',{}))
    if api_retry and retry and method in md_ls:
        last_retry = api_retry.get('retry','')
        last_method = api_retry.get('method','')
        last_retry_cnt = api_retry.get('retry_cnt',0)
        last_data = api_retry.get('data',{})
        last_rc = api_retry.get('rc',0)
        if last_retry == retry and \
          last_method == method and \
          last_retry_cnt < 5:
            data.update(last_data)
            data['user_info'] = rk_user.wrapper_info()
            last_retry_cnt += 1
            api_retry['retry_cnt'] = last_retry_cnt
            ul.login_info['api_retry'] = api_retry
            ul.put()
            return last_rc,data
        else:
            ul.login_info['api_retry'] = {}
            ul.put()

    rc,func_data = bl_func(rk_user,params)
    if rc != 0:
        #rc异常时,清空storage
        app.pier.clear()
    data.update(func_data)

    if method in md_ls:
        ul = UserLogin.get_instance(rk_user.uid)
        ul.login_info['api_retry'] = {'retry':retry,'method':method,'data':func_data,'rc':rc,'retry_cnt':0}
        ul.put()

    # 更新玩家体力  每隔一段时间会恢复体力
    rk_user.user_property.update_stamina_from_time()
    #用户基本信息
    data['user_info'] = rk_user.wrapper_info()
    return rc,data
