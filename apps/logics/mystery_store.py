#-*- coding: utf-8 -*-
""" mystery_store.py
"""
import copy

from apps.models.user_mystery_store import UserMysteryStore
from apps.common import utils
from apps.config.game_config import game_config
from apps.logics import vip
from apps.models import data_log_mod

def get_store_info(rk_user, params):
    """
    得到当前玩家的神秘商店信息
    前段点击 和 前段倒计时结束时调用此接口 神秘商店时调用此接口
     此接口会先判断是否要自动刷新商品
    """
    user_mystery_store_obj = UserMysteryStore.get_instance(rk_user.uid)
    return 0, _pack_store_info(user_mystery_store_obj.auto_refresh_store())


def refresh_store_by_self(rk_user, params):
    """
    玩家主动刷新时  调用此接口
    优先消耗  刷新令
    params  参数需包含 store_type ：  "gold_store"  or  "coin_store"
    刷新令  :  1001_mat
    """

    mat_id = '1001_mat'
    store_type = params['store_type']
    needed_cost = game_config.mystery_store[store_type + "_refresh_cost"]
    golf_or_coin = store_type.split('_')[0]

    #  根据store_type  决定是 消耗元宝还是铜钱
    minus_func = getattr(rk_user.user_property, "minus_" + golf_or_coin)

    user_pack_obj = rk_user.user_pack

    #miaoyichao start
    if not vip.check_limit_recover(rk_user,'recover_mystery_store'):
        return 11,{'msg':utils.get_msg('user','max_times')}
    #回复次数+1
    rk_user.user_property.add_recover_times('recover_mystery_store')
    #miaoyichao end
    # 先判断 是否有  刷新令
    if user_pack_obj.is_material_enough(mat_id, 1):
        user_pack_obj.minus_materials({mat_id: 1})
    # 再判断是否 coin or  gold  足够
    elif not minus_func(needed_cost, 'refresh_mystery_store'):
        return 11, {'msg': utils.get_msg('user', 'not_enough_' + golf_or_coin)}
    
    # 记录 消费元宝log
    if store_type == "coin_store":
        data_log_mod.set_log("ConsumeRecord", rk_user, 
                            lv=rk_user.user_property.lv,
                            num=needed_cost,
                            consume_type='refresh_coin_store',
                            before_coin=rk_user.user_property.coin + needed_cost,
                            after_coin=rk_user.user_property.coin
        )

    user_mystery_store_obj = UserMysteryStore.get_instance(rk_user.uid)
    user_mystery_store_obj.refresh_store(store_type)
    return 0, _pack_store_info(user_mystery_store_obj.store_info())


def buy_store_goods(rk_user, params):
    """
    玩家购买指定商品时逻辑
    params  参数需包含 store_type： 可选 "packages"   "gold_store"  or  "coin_store"
                     goods_index:  int  为所买商品在所属类型的index   
    """
    store_type = params['store_type']
    goods_index = int(params['goods_index'])

    buy_goods_info = {}
    goods_list = []
    user_mystery_store_obj = UserMysteryStore.get_instance(rk_user.uid)
    if store_type == "packages":
        buy_goods_info = game_config.mystery_store["packages"][goods_index]
        goods_list = buy_goods_info['goods']
    else:
        buy_goods_info = user_mystery_store_obj.store_info()[store_type][goods_index]
        goods_list.append(buy_goods_info['goods'])
    gold_or_coin = "coin" if buy_goods_info.get("coin", 0) else "gold"
    needed_cost = buy_goods_info.get(gold_or_coin, 0)

    #  根据store_type  决定是 消耗元宝还是铜钱
    minus_func = getattr(rk_user.user_property, "minus_" + gold_or_coin)

    if not minus_func(needed_cost, 'buy_mystery_store_goods'):
        return 11, {'msg': utils.get_msg('user', 'not_enough_' + gold_or_coin)}

    # 记录 消费元宝log
    if gold_or_coin == "coin":
        data_log_mod.set_log("ConsumeRecord", rk_user, 
                            lv=rk_user.user_property.lv,
                            num=needed_cost,
                            consume_type='buy_mystery_{}_item'.format(store_type),
                            before_coin=rk_user.user_property.coin + needed_cost,
                            after_coin=rk_user.user_property.coin
        )

    # 发商品    
    # 前端通过rc 是否等于 0 判断是否购买成功
    if not user_mystery_store_obj.update_goods_info_by_index(store_type, goods_index):
        return 11, {'msg': 'has bought this item'}
    all_get_goods = {}
    award_return = {'stamina':0,'gold':0,'coin':0,'gacha_pt':0,'stone':0,'item':{}, 'super_soul': 0, 'material':{},'card':{},'equip':{}, 'normal_soul': {},}

    for goods in goods_list:
        tmp = rk_user.user_property.give_award(_pack_goods(goods), where=u"buy_from_mystery_store")
        for _k in tmp:
            if _k in ['gold','coin','gacha_pt','stone', 'super_soul','stamina']:
                award_return[_k] = award_return.get(_k,0) + tmp.get(_k,0)
            elif _k in ['item','material', 'normal_soul']:
                for __kk in tmp[_k]:
                    award_return[_k][__kk] = award_return[_k].get(__kk,0) + tmp[_k][__kk]
            elif _k in ['card','equip']:
                award_return[_k].update(tmp[_k])
    all_get_goods = {i:award_return[i] for i in award_return if award_return[i]}

    return 0, {'get_info': all_get_goods}

def _pack_goods(award):
    k = award.keys()[0]
    out_key = ""
    if k in ['gold','gacha_pt','coin','stone', 'super_soul']:
        return award
    elif 'card' in k:
        if isinstance(award[k], dict):
            out_key = 'card'
        # 区别是武将还是将魂， 如果是将魂 {'160_card':num}
        elif isinstance(award[k], int):
            out_key = 'normal_soul'
    elif 'equip' in k:
        out_key = 'equip'
    elif 'item' in k:
        out_key = 'item'
    elif 'mat' in k:
        out_key = 'material'
    elif 'soul' in k:
        out_key = 'normal_soul'
        award = {k.replace("soul", "card"): award[k]}
    return {out_key: award}

def _pack_store_info(store_info):
    store_info = copy.deepcopy(store_info)
    for package in store_info["packages"]:
        new_goods = []
        for goods in package["goods"]:
            new_goods.append(_pack_goods(goods))
        package["goods"] = new_goods

    for goods_info in store_info["gold_store"]:
        goods_info["goods"] = _pack_goods(goods_info["goods"])
    for goods_info in store_info["coin_store"]:
        goods_info["goods"] = _pack_goods(goods_info["goods"])
    return store_info

