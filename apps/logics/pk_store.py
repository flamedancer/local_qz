# encoding: utf-8
""" 
pk_store.py
"""
import copy
from apps.common import utils
from apps.common import tools
from apps.config.game_config import game_config
from apps.models import data_log_mod
from apps.common.exceptions import GameLogicError


def get_store_info(rk_user, params):
    '''
    获取玩家 pk 商店信息
    '''
    #判断新手引导
    newbie_step = int(params.get('newbie_step', 0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "pk_store")
    return _pack_store_info(rk_user.user_pk_store.auto_refresh_store())


def refresh_store_by_self(rk_user, params):
    '''
    手动刷新 pk 商店
    '''
    user_pk_store = rk_user.user_pk_store
    user_real_pvp = rk_user.user_real_pvp
    # 今日手动刷新次数用完, 无法刷新,提示充值来提升 vip 等级
    if not user_pk_store.can_manual_refresh():
        return 11, {'msg': utils.get_msg('pk_store', 'can_not_refresh')}
    # 玩家所拥有的功勋点不够一次刷新
    refresh_times = str(user_pk_store.manual_refresh_times + 1) # 指第几次刷新，第一次刷新时manual_refresh_times 是 0
    refresh_need_honor = game_config.pk_store_config['refresh_need_honor'].get(refresh_times, 1)
    if not user_real_pvp.is_honor_enough(refresh_need_honor):
        return 11, {'msg': utils.get_msg('pk_store', 'not_enough_honor')}

    user_real_pvp.minus_honor(refresh_need_honor)
    user_pk_store.add_refresh_time()
    user_pk_store.refresh_store_goods()
    return 0, _pack_store_info(user_pk_store.store_info())


def buy_store_goods(rk_user, params):
    """
    用功勋兑换 Pk 商店物品
    params  参数需包含 
        goods_index:   所兑换的物品index
    返回 data 包括所兑换物品和商店信息
    """

    goods_index = int(params['goods_index'])
    user_pk_store = rk_user.user_pk_store
    user_pk_goods = user_pk_store.goods
    
    
    # pk商店无此物品
    if not (0 <= goods_index < len(user_pk_goods)):
        return 11, {'msg': utils.get_msg('pk_store', 'no_this_goods')}
    
    goods_info = user_pk_goods[goods_index]
    
    # 已兑换过
    if not user_pk_store.can_buy_this_goods(goods_index):
        raise GameLogicError('pk_store', 'can_not_buy_again')
    need_honor = goods_info['need_honor']
    # 兑换所需功勋点不够
    user_real_pvp = rk_user.user_real_pvp
    if not user_real_pvp.is_honor_enough(need_honor):
        raise GameLogicError('pk_store', 'not_enough_honor')
    # 扣除功勋
    user_real_pvp.minus_honor(need_honor)
    # 兑换物品
    user_pk_store.goods_has_bought(goods_index)

    # 发放兑换物品
    all_get_goods = tools.add_things(rk_user,
                             [goods_info['goods']],
                             where="buy_mystery_store_goods")


    # 记录log
    log_data = {"cost_honor": need_honor, "goods": all_get_goods}
    data_log_mod.set_log("PkStore", rk_user, **log_data)

    data = {'get_info': all_get_goods}
    data.update(_pack_store_info(user_pk_store.store_info()))
    return data


def _pack_store_info(store_info):
    store_info = copy.deepcopy(store_info)
    for each_good_info in store_info["pk_store"]:
        if not isinstance(each_good_info, dict):
            continue
        print each_good_info
        good_id = each_good_info["goods"]["_id"]
        num = each_good_info["goods"]["num"]
        pack = tools.pack_good(good_id, num)
        each_good_info["goods"] = pack
    return store_info
