#-*- coding: utf-8 -*-
""" 
filename:activity.py
miaoyichao
该文件主要有的函数功能
1  美味大餐
2  探索活动的内容
"""

import datetime
from apps.models.user_pack import UserPack
from apps.models.user_cards import UserCards
from apps.models.user_equips import UserEquips
from apps.models.user_souls import UserSouls
from apps.common import utils
from apps.common import tools
from apps.config.game_config import game_config
from apps.models import data_log_mod
from apps.common.utils import datetime_toString


def banquet_info(rk_user, params):
    '''
    * 获取美味大餐的相关内容
    * 获取探索的相关内容
    '''
    ua = rk_user.user_activity
    user_banquet_info = ua.banquet_info
    now = datetime.datetime.now()
    now_date_day = now.strftime('%Y-%m-%d')
    now_hour_min = now.strftime('%H:%M')
    banquet_info = {'banquet_msgs': [], 'can_get': False,'desc':{}}
    banquet_info['banquet_interval'] = []
    open_time_gaps = game_config.operat_config.get('open_stamina_banquet_gaps', [])
    #获取开放的时间   设置标志位
    for gap in open_time_gaps:
        time_msg = gap[0] + ' -- ' + gap[1] + ':'
        if user_banquet_info.get(gap):
            open_msg = utils.get_msg('active', 'already_banquet')
        elif gap[0] <= now_hour_min <= gap[1]:
            open_msg = utils.get_msg('active', 'in_time')
            banquet_info['can_get'] = True
        else:
            open_msg = utils.get_msg('active', 'not_in_time')
        banquet_info['banquet_msgs'].append(time_msg + open_msg)
        banquet_info['desc'][time_msg[:-1]] = open_msg
        time_start = '%s %s:00'%(now_date_day,str(gap[0]))
        time_end = '%s %s:00'%(now_date_day,str(gap[1]))
        start_time = utils.string_toTimestamp(time_start)
        end_time = utils.string_toTimestamp(time_end)
        banquet_info['banquet_interval'].append(start_time)
        banquet_info['banquet_interval'].append(end_time)
    time_lists = sorted([str(time_list) for time_list in banquet_info['banquet_interval']])
    banquet_info['am_start'] = time_lists[0]
    banquet_info['am_end'] = time_lists[1]
    banquet_info['pm_start'] = time_lists[2]
    banquet_info['pm_end'] = time_lists[3]
    banquet_info.pop('banquet_interval')
    banquet_info['am_flag'] = user_banquet_info.get(banquet_info['am_start'],False)
    banquet_info['pm_flag'] = user_banquet_info.get(banquet_info['pm_start'],False)
    #获取探索的相关内容
    explore_info = get_explore_info(rk_user)

    # 判断新手引导
    newbie_step = int(params.get('newbie_step', 0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "banquet_info")
    return 0, {'banquet_info': banquet_info,'explore_info':explore_info}

def get_banquet_stamina(rk_user, params):
    """
    开始宴席
    """
    open_time_gaps = game_config.operat_config.get('open_stamina_banquet_gaps', [])
    now = datetime.datetime.now()
    now_date_day = now.strftime('%Y-%m-%d')
    now_hour_min = now.strftime('%H:%M')
    this_time_gap = utils.between_gap(now_hour_min, open_time_gaps)
    if not this_time_gap:
        return 11,{'msg':utils.get_msg('active', 'not_in_time')}
    # 获取时间区间的最小值
    time_start = '%s %s:00'%(now_date_day,str(this_time_gap[0]))
    start_time = utils.string_toTimestamp(time_start)
    #查询是否已经领取体力
    ua = rk_user.user_activity
    banquet_info = ua.banquet_info
    if banquet_info.get(str(start_time), False):
        return 11, {'msg':utils.get_msg('active', 'already_banquet')}
    # 获取可以领取多少体力
    get_stamina = game_config.operat_config.get('banquet_click_get_stamina', 50)
    #  运营活动  特定时间内收益翻倍
    multiply_income_conf = rk_user.game_config.operat_config.get("multiply_income", {}).get("banquet", {})
    get_stamina = get_stamina * multiply_income(multiply_income_conf)
    ua.banquet_info[str(start_time)] = True
    ua.put()
    rk_user.user_property.add_stamina(get_stamina)
    return 0, {'add_stamina': get_stamina}


def get_explore_info(rk_user):
    '''
    获取探索的信息
    uid
    '''
    data = {}
    for explore_type in ['gold','silver','copper']:
        data['cost_'+explore_type] = game_config.explore_config.get('cost_'+explore_type+'_shovel')
        data['explore_'+explore_type+'_cost'] = game_config.explore_config.get('explore_cost_config',{}).get(explore_type,10)
    #获取背包中的道具信息
    user_pack_obj = rk_user.user_pack
    #获取所有的道具
    all_props = user_pack_obj.get_props()
    props_config = game_config.props_config
    user_explore_props = {}
    #获取用户的道具配置
    for props_id in props_config:
        user_by = props_config.get(props_id,{}).get('used_by','')
        if user_by == 'explore' and props_id in all_props:
            props_type = props_config.get(props_id,{}).get('type','')
            #获取可以探索的id 
            user_explore_props[props_type] = all_props[props_id]
    #获取探索信息 用户的道具的数量
    user_activity_obj = rk_user.user_activity
    explore_times = user_activity_obj.get_explore_times()
    for explore_type in explore_times:
        #data[explore_type] = explore_times[explore_type]
        data['user_'+explore_type] = user_explore_props.get(explore_type,0)
    #结果返回
    return data


def explore(rk_user,params):
    '''
    *宝藏探索 
    *输入 要探索的宝藏类型  探索次数
    返回 探索获取的
    '''
    shovel = params.get('shovel')
    if shovel not in ['gold','silver','copper']:
        return 11,{'msg':utils.get_msg('pack', 'no_materials')}
    #获取探索的次数
    times = int(params.get('times',1))
    #获取是否是消耗元宝进行的探索
    use_coin = params.get('use_coin',False)
    #获取当前探索类型的每一次所消耗的道具数量
    once_cost_num = int(game_config.explore_config.get('cost_'+shovel+'_shovel'))
    all_cost_num = times * once_cost_num
    #user_activity_obj = UserActivity.get_instance(rk_user.uid)
    # #获取可探索的次数
    # left_explore_times = user_activity_obj.get_explore_times()
    # #判断可探索次数是为空
    # if not left_explore_times[shovel]:
    #     return 11,{'msg':utils.get_msg('pack', 'not_enough_times')}
    # #判断可探索次数和要探索次数是否符合逻辑
    # if times>left_explore_times[shovel]:
    #     return 11,{'msg':utils.get_msg('pack', 'not_enough_material')}
    if use_coin:
        #用户使用元宝进行探索
        explore_cost_config = game_config.explore_config.get('explore_cost_config',{})
        cost_coin = int(explore_cost_config.get(shovel,10))
        all_cost_coin = cost_coin * times
        if rk_user.user_property.coin < all_cost_coin:
            return 11,{'msg':utils.get_msg('user','not_enough_coin')}
        #减元宝
        rk_user.user_property.minus_coin(all_cost_coin, where="explore")
        cost_what = "coin"
        cost_num = all_cost_coin
    else:
        #将类型转化为可识别的道具
        props_config = game_config.props_config
        #根据探索的类型获取探索所需要的道具
        for props_id in props_config:
            if props_config[props_id].get('used_by','')=='explore' and props_config[props_id].get('type','')== shovel:
                p_id = props_id
                break
            else:
                pass
        #使用道具进行探索
        user_pack_obj = UserPack.get_instance(rk_user.uid)
        #判断道具是否足够
        if not user_pack_obj.is_props_enough(p_id,all_cost_num):
            return 11,{'msg':utils.get_msg('pack', 'not_enough_props')}
        #减素材
        user_pack_obj.minus_props(p_id, all_cost_num, where="explore")
        cost_what = props_id
        cost_num = all_cost_num
    #减可探索的次数
    # user_activity_obj.min_explore_times(shovel,all_cost_num)
    log_data = {"type": shovel, "cost": cost_what, "cost_num": cost_num, "num": times}
    data_log_mod.set_log('Explore', rk_user, **log_data)
    explore_info = add_explore_info(shovel, rk_user, times)


    return 0,{'explore_info':explore_info}


def add_explore_info(explore_type, rk_user, times):
    '''
    根据探索类型获取探索的内容 并且添加
    '''
    explore_config = game_config.explore_config.get('get_explore_info',{}).get(explore_type,{})


    get_things = []
    show_things = []
    #格式化探索获得的内容
    for i in xrange(times):
        get_explore_type = utils.get_item_by_random_simple(explore_config)
        explore_info = game_config.explore_config.get(get_explore_type, {})
        #格式化要获取的 id 和权重
        wlst = []
        for index, explore_dict in explore_info.items():
            weight = int(explore_dict['weight'])
            thing_id = explore_dict['id']
            thing_num = explore_dict['num']
            wlst.append([(thing_id, thing_num), weight])
        #获取探索得到的 id  #[[value,weight],[value,weight],[value,weight],[value,weight]]
        get_id, get_num = utils.windex(wlst)
        # #获取探索得到的数量
        # get_num = int(explore_info[get_id]['num'])
        #获取探索得到的种类
        get_things.append({"_id": get_id, "num": get_num})
        show_things.append(tools.pack_good(get_id, get_num))

    all_get_goods = tools.add_things(rk_user, get_things)
    return {"get_info": all_get_goods, "show_things": show_things}

        
def multiply_income(multiply_income_conf):
    """特定时间内功能 收益翻倍
    banquet 美味大餐体力收益翻倍；
    daily_dungeon  试炼副本掉落物品道具，铜钱，经验值等数量翻倍；
    pk  实时pvp胜利pt点收益翻倍；
    start_time"， "end_time"  翻倍开始和结束时间，  "multiply" 翻的倍数


    Returns:
        multiply     收益翻倍翻的倍数
    """
    if not multiply_income_conf:
        return 1
    now_str = datetime_toString(datetime.datetime.now())
    # 未开放
    start_time = multiply_income_conf.get("start_time", 0)
    end_time = multiply_income_conf.get("end_time", 0)
    if now_str > end_time or now_str < start_time:
        return 1
    return multiply_income_conf.get("multiply", 1)
