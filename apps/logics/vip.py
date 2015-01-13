#-*- coding: utf-8 -*-
""" vip.py
主要包括 获取vip的配置信息 VIP的配置信息  get_vip_config
检查各种需求的回复次数  以及 vip 礼包的内容
"""
import copy
from apps.config.game_config import game_config
from apps.common import utils
from apps.common import tools
from apps.common.exceptions import GameLogicError



def get_vip_config(rk_user,params):
    data = {}
    data['vip_config'] = game_config.user_vip_config
    return data


def check_limit_recover(rk_user, where, dtype='', floor_id=''):
    """根据用户的vip等级判断用户当天是否达到回复次数"""
    user_property_obj = rk_user.user_property
    vip_lv = str(user_property_obj.vip_cur_level)
    today_str = utils.get_today_str()
    now_recover_times = 0
    if today_str == user_property_obj.property_info['recover_times']['today_str']:
        if where in ['recover_stamina', 'recover_mystery_store']:
            # 回复体力的处理
            max_recover_times = game_config.user_vip_config[vip_lv].get('can_'+where+'_cnt', 0)
            now_recover_times = user_property_obj.property_info['recover_times'][where]
            if max_recover_times <= now_recover_times:
                raise GameLogicError('user','max_times')
        elif where == 'recover_copy':
            # 重置战场的处理
            if dtype == 'normal':
                max_recover_times = game_config.user_vip_config[vip_lv]['can_recover_copy_cnt']['normal']
                now_recover_times = user_property_obj.property_info['recover_times']['recover_copy']['normal']
            elif dtype == 'daily':
                max_recover_times = game_config.user_vip_config[vip_lv]['can_recover_copy_cnt']['daily'][floor_id]
                now_recover_times = user_property_obj.property_info['recover_times']['recover_copy']['daily'].get(floor_id, 0)
            if max_recover_times <= now_recover_times:
                raise GameLogicError('user','max_times')
    else:
        # 重置时间和副本次数
        user_property_obj.reset_recover_times()
    return now_recover_times


def vip_gift_sale_list(rk_user):
    """vip用户礼包列表"""
    data = {}
    user_property_obj = rk_user.user_property
    # 已购买的vip礼包id list
    has_bought_ids = user_property_obj.property_info['has_bought_vip_package']
    # 读取商店vip礼包配置
    vip_gift_sale_config = game_config.vip_store_config.get('vip_sale',{})
    data = _pack_store_info(vip_gift_sale_config, has_bought_ids)
    return data


def buy_vip_gift(rk_user, params):
    "购买vip礼品包"
    vip_gift_id = params.get('vip_gift_id', '')
    vip_gift_sale_config = game_config.vip_store_config.get('vip_sale',{})

    user_property_obj = rk_user.user_property
    vip_cur_level = user_property_obj.vip_cur_level

    # 已购买的vip礼包id list
    has_bought_ids = user_property_obj.property_info['has_bought_vip_package']

    # 判断vip礼包id是否有效
    if not vip_gift_id:
        raise GameLogicError('gift', 'gift_code_error')
    # 判断是否存在该vip礼包
    if vip_gift_id not in vip_gift_sale_config:
        raise GameLogicError('gift','gift_code_not_exist')
    # 判断玩家的vip等级是否达到
    if int(vip_gift_id) > int(vip_cur_level):
        raise GameLogicError('gift','level_not_enough')
    # 判断玩家是否已经购买相应的vip礼包
    if vip_gift_id in has_bought_ids:
        raise GameLogicError('gift','gift_already_buy')

    need_coin = vip_gift_sale_config[vip_gift_id]['coin']
    # 判断玩家的元宝是否达到
    if not user_property_obj.is_coin_enough(need_coin):
        raise GameLogicError('user', 'not_enough_coin')

    goods_list = vip_gift_sale_config[vip_gift_id]['goods_list']
    all_get_goods = tools.add_things(rk_user, [{"_id": good_id, "num": num} 
        for good_id, num in goods_list.items()], where='buy_vip_gift')
    # 扣除元宝
    user_property_obj.minus_coin(need_coin, where="buy_vip_gift")

    user_property_obj.add_bought_vip_package(vip_gift_id)
    return {'get_info': all_get_goods}
    
    
def _pack_store_info(store_info, has_bought_ids):
    store_info = copy.deepcopy(store_info)
    for vip_level, good_info in store_info.items():
        good_info["has_bought"] = (vip_level in has_bought_ids)
        goods_list = []
        for good_id, num in good_info['goods_list'].items():
            goods_list.append(tools.pack_good(good_id, num))
        good_info['goods_list'] = goods_list
    return store_info


