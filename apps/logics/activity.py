#-*- coding: utf-8 -*-
""" 
filename:activity.py
该文件主要有的函数功能
1  美味大餐
2  探索活动的内容
"""

import datetime
from apps.models.user_pack import UserPack
from apps.common import utils
from apps.common import tools
from apps.config.game_config import game_config
from apps.models import data_log_mod
from apps.common.utils import datetime_toString
from apps.common.exceptions import GameLogicError


def get_growup_info(rk_user, params):
    """ 获得成长礼包的信息 

    Returns:
        has_bought  玩家是否购买过成长计划
        need_coin   购买成长计划需要元宝数
        growup_award   各成长礼包信息以及玩家领取情况
    """
    operat_config = game_config.operat_config
    need_coin = operat_config.get('growup_award_need_coin', 0)
    need_vip_lv = operat_config.get('growup_award_need_vip_lv', 0)
    growup_award = operat_config.get('growup_award', {}).copy()
    # 已领取的等级奖励
    ua_growup_info = rk_user.user_activity.growup_info
    has_got_award_lvs = ua_growup_info.get('has_got_lvs', [])
    has_bought = ua_growup_info.get('has_bought', False)
    for lv in growup_award:
        growup_award[lv]['has_got'] = (lv in has_got_award_lvs)
    return {'need_coin': need_coin,
            'growup_award': growup_award,
            'has_bought': has_bought,
            'need_vip_lv': need_vip_lv,
    }


def banquet_info(rk_user, params):
    """
    * 获取美味大餐的相关内容
    * 获取探索的相关内容
    * 获得成长礼包的信息
    """

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
    # 获取探索的相关内容
    explore_info = get_explore_info(rk_user)
    # 获取成长礼包相关内容
    growup_info = get_growup_info(rk_user, params)
    # 判断新手引导
    newbie_step = int(params.get('newbie_step', 0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "banquet_info")
    return {
        'banquet_info': banquet_info, 
        'explore_info': explore_info,
        'growup_info': growup_info,
    }


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

    all_get_goods = tools.add_things(rk_user, get_things, where='explore')
    return {"get_info": all_get_goods, "show_things": show_things}

        
def buy_growup_plan(rk_user, params):
    """购买成长计划"""
    ua = rk_user.user_activity
    ua_growup_info = ua.growup_info
    has_bought = ua_growup_info.get('has_bought', False)

    # 是否已购买 成长计划
    if has_bought:
        raise GameLogicError('has bought')
    operat_config = game_config.operat_config
    need_coin = operat_config.get('growup_award_need_coin', 0)
    if not rk_user.user_property.is_coin_enough(need_coin):
        raise GameLogicError('user', 'not_enough_coin')
    # vip 等级限制
    user_property_obj = rk_user.user_property
    vip_cur_level = user_property_obj.vip_cur_level
    need_vip_lv = operat_config.get('growup_award_need_vip_lv', 0)
    if vip_cur_level < need_vip_lv:
        raise GameLogicError('vip lv not reached')

    ua_growup_info['has_bought'] = True
    # 扣元宝
    rk_user.user_property.minus_coin(need_coin, 'buy_growup_plan')
    ua.put()
    return {}


def get_growup_awards(rk_user, params):
    """ 领取等级成长奖励

    Args:
        award_lv:  领取是第几等级的奖励
    """
    award_lv = params.get('award_lv', '0')
    ua = rk_user.user_activity
    ua_growup_info = ua.growup_info
    all_growup_awards = game_config.operat_config.get('growup_award', {})

    # 没有购买成长计划
    if not ua_growup_info.get('has_bought', False):
        raise GameLogicError('has not bought')
    # 不存在该等级奖励
    if award_lv not in all_growup_awards:
        raise GameLogicError('lv award no exist')
    # 等级未到达
    user_property_obj = rk_user.user_property
    if int(user_property_obj.lv) < int(award_lv):
        raise GameLogicError('lv not reached')
    # 已领取的等级奖励 不能再领
    has_got_award_lvs = ua_growup_info.get('has_got_lvs', [])
    if award_lv in has_got_award_lvs:
        raise GameLogicError('has got this award')
    has_got_award_lvs.append(award_lv)
    ua_growup_info['has_got_lvs'] = has_got_award_lvs
    ua.put()
    # 加物品
    get_things = [{'_id': thing_id, 'num': num}  for thing_id, num in 
            all_growup_awards[award_lv].get('awards', {}).items()]
    all_get_goods = tools.add_things(rk_user, get_things, where='get_growup_awards_%s' %award_lv)
    return {"get_info": all_get_goods}

        
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


def more_dungeon_drop(dungeon_type, floor_id, room_id, times=1):
    """  运营活动 特定时间   指定战场 额外掉落物品

    Args:
        dungeon_type   战场类型 
        floor_id
        room_id
        times          需要随机掉落几次

    Retruns:
        {
            'card':{
                '1_card': 4,
                '2_card': 5,
            },
            'soul':{
                '1_card': 10,
                '2_equip_1': 1,
            },
            'gold':{
                'gold': 50,
            }
            .....

        }
    """
    more_drop_conf = game_config.operat_config.get('more_drop_conf')
    if not more_drop_conf:
        return {}
    drop_info = {}
    for each_conf in more_drop_conf.values():
        now_str = datetime_toString(datetime.datetime.now())
        start_time = each_conf.get("start_time", 0)
        end_time = each_conf.get("end_time", 0)
        # 开发时间
        if now_str > end_time or now_str < start_time:
            continue
        # 指定战场类型开放
        if not dungeon_type in each_conf.get('dungeon', {}):
            continue
        # 指定战场开放
        if each_conf['dungeon'][dungeon_type] != 'all' and '-'.join([floor_id, room_id]) not in each_conf['dungeon'][dungeon_type]:
            continue
        for thing_id, thing_drop_conf in each_conf.get('drop_things', {}).items():
            num = 0
            for cnt in range(times):
                if not utils.is_happen(thing_drop_conf.get('drop_rate', 0)):
                    continue
                num += utils.get_item_by_random_simple(thing_drop_conf['num'])
            if num > 0:
                thing_type = thing_drop_conf['type']
                drop_info.setdefault(thing_type, {})
                thing_id = thing_id.replace('Soul', '')
                drop_info[thing_type][thing_id] = drop_info[thing_type].get(thing_id, 0) + num
    return drop_info


def get_fudai_things(rk_user, params):
    """开启福袋获得物品

    Args:
        fudai_id   开启的福袋id 
        times      开启次数
    """
    fudai_id = params.get('fudai_id', '')
    open_times = int(params.get('times', 0))
    # 判断是否是福袋
    if not game_config.props_config.get(fudai_id, {}).get('used_by','') == 'fudai':
        raise GameLogicError('pack', 'wrong_used')
        # 判断用户是否有该道具
    user_pack_obj = rk_user.user_pack
    if not user_pack_obj.is_props_enough(fudai_id, open_times):
        raise GameLogicError('pack', 'not_enough_props')
    fudai_conf = game_config.operat_config.get('fudai_conf', {}).get(fudai_id, {})
    get_things_conf = fudai_conf.get('get_things', {})
    get_things_list = []
    for cnt in range(open_times):
        get_things_dict = utils.get_items_by_weight_dict(get_things_conf, 1)[0]
        things_id = get_things_dict['id']
        things_num = get_things_dict['num']
        get_things_list.append({'_id': things_id, 'num': things_num})
    all_get_things = tools.add_things(rk_user, get_things_list, where=u"open_fudai_%s" %fudai_id)
    # 减素材
    user_pack_obj.minus_props(fudai_id, open_times, where="open_fudai")
    return {'get_info': all_get_things}



