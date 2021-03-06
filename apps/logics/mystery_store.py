#-*- coding: utf-8 -*-
""" mystery_store.py
"""
import copy

from apps.models.user_mystery_store import UserMysteryStore
from apps.models.user_property import UserProperty
from apps.common import utils
from apps.common import tools
from apps.config.game_config import game_config
from apps.logics import vip
from apps.models import data_log_mod
from apps.models.user_cards import UserCards
from apps.models.user_equips import UserEquips
from apps.models.user_pack import UserPack
from apps.logics import card
from apps.logics import equip

from apps.common.exceptions import GameLogicError


def stove(rk_user,params):
    """
    熔炼炉
    类似一个回收系统，消耗武将，装备等，来得到相应的资源，资源包括战魂，铜钱，素材，道具等。
    返还的范围包括物品的初始花费和后续花费，比如升级某样物品所花费的铜钱也返还
    """
    #练化类型
    category = params.get('category','')
    data = {}
    rc = 0
    user_property_obj = UserProperty.get_instance(rk_user.uid)
    user_card_obj = UserCards.get_instance(rk_user.uid)
    user_equip_obj = UserEquips.get_instance(rk_user.uid)
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    user_property_obj = UserProperty.get_instance(rk_user.uid)
    #出售逻辑很炼丹炉一样，所以直接调用出售逻辑获得数据结构
    #武将
    if category == 'card':
        rc,msg = card.card_stove(rk_user,params)
        if rc:
            return rc,msg
        #获取武将计算系数                       card_update_config:武将强化
        card_stove_gold_coe = float(game_config.card_update_config['card_stove_gold_coe'])
        card_stove_props_coe = float(game_config.card_update_config['card_stove_props_coe'])
        #取得天赋进阶的配置信息                 talent_skill_config 武将天赋技能
        advanced_talent_config = game_config.talent_skill_config['advanced_talent_config']
        #总计获取的战魂
        fight_soul = 0
        #总计返回的进阶丹  
        return_props = 0
        #返回铜钱
        return_gold = 0
        for card_info in msg['cards_info']:
            cid = card_info['cid']
#           print '#### cid=', cid

            #获取武将的当前天赋等级
            cur_talent_lv = card_info['talent_lv']
#           print '#### cur_talent_lv=', cur_talent_lv

            #获取武将星级            card_config 武将设置
            star = str(game_config.card_config[cid].get('star',4))
#           print '#### card star=', star

            #读取计算战魂系统    card_update_config:武将强化
            stove_card_fight_soul = int(game_config.card_update_config['card_stove_fight_soul'].get(star,1))
            #获取当前经验
            cost_update_gold = card_info['exp']
            #武将炼化基础值
            base_gold = int(game_config.card_update_config['sell_base_gold'].get(star,3000))
            #获取当前进阶所需的配置(武将,铜钱,进阶丹)

            #铜钱计算公式 = 基础数值 + int(当前状态总共消耗铜钱 * 0.8)
            return_gold  += base_gold + int(cost_update_gold * card_stove_gold_coe)
            #战魂计算公式 =（1 + 进阶到当前状态总消耗武将个数）* 系数
            fight_soul  += stove_card_fight_soul

            for talent_lv in range(1, int(cur_talent_lv)+1):
                cur_talent = advanced_talent_config[star].get(str(talent_lv),{})
                cost_talent_gold  = int(cur_talent.get('cost_gold',0))
                cost_talent_card  = int(cur_talent.get('card',0))   #武将
                cost_talent_props = cur_talent.get('props',[]) #进阶丹

                #铜钱计算公式 = 基础数值 + int(当前状态总共消耗铜钱 * 0.8)
                return_gold  += int( cost_talent_gold * card_stove_gold_coe )
                #进阶丹 = int(当前状态总消耗 * 0.8)
                if cost_talent_props:
                    return_props += int(cost_talent_props[1] * card_stove_props_coe)
                #战魂计算公式 =（1 + 进阶到当前状态总消耗武将个数）* 系数
                fight_soul  += int(cost_talent_card * stove_card_fight_soul)

#               print '#### return_gold, return_props, fight_soul=', \
#                       return_gold, return_props, fight_soul

        #添加战魂
        user_property_obj.add_fight_soul(fight_soul, 'stove')
        #返还进阶丹
        user_pack_obj.add_props('8_props',return_props, 'stove')
        #用户删卡
        user_card_obj.del_card_info(msg['cards_ucids'], where='stove')
        #返还铜钱
        user_property_obj.add_gold(return_gold, 'stove')
        data = {'gold':return_gold,'fight_soul':fight_soul,'props':{'8_props':return_props}}

    #普通装备(1:武器(攻击),2:护甲（防御）,3:头盔（血量）,4:饰品（回复)
    elif category == 'common_equip':
        rc,msg = equip.equip_stove(rk_user,params)
        if rc:
            return rc,msg
        # category check,防止category和装备eid不匹配
        for equip_info in msg['equips_info']:
            eid = equip_info['eid']
            eqtype = game_config.equip_config[eid]['eqtype']
            if eqtype not in [1, 2, 3, 4]:
                return 11,{'msg':utils.get_msg('mystery_store','category_not_match')}
        #获取普通装备计算系数                      equip_exp_conf:装备等级配置
        common_stove_gold_coe = float(game_config.equip_exp_config['common_stove_gold_coe'])
        #返回铜钱
        return_gold = 0
        for equip_info in msg['equips_info']:
            # equip_info 是 UserEquips实例的equips[ueid]字段
            eid = equip_info['eid'] 
            uetype = int(game_config.equip_config[eid]['eqtype'])
            #获取当前等级
            cur_equip_lv = equip_info['cur_lv']
            #获取当前经验(升级到该经验所需铜钱)
            cost_update_gold = equip_info['cur_experience']

            #获取装备的星级
            star = str(game_config.equip_config[eid].get('star',1))
            #普通装备炼化基础值            equip_exp_config:装备等级配置

            base_gold = int(game_config.equip_exp_config['common_base_gold'].get(star,500))
            return_gold += int((base_gold + cost_update_gold) * common_stove_gold_coe)


        #用户删除装备
        user_equip_obj.delete_equip(msg['equips_ueids'], where='stove')
        #返还铜钱
        user_property_obj.add_gold(return_gold, 'stove')

        data = {'gold':return_gold}

    #宝物(5:兵法,6:坐骑)
    elif category == 'treasure_equip':
        rc,msg = equip.equip_stove(rk_user,params)
        if rc:
            return rc,msg
        # category check,防止category和装备eid不匹配
        for equip_info in msg['equips_info']:
            eid = equip_info['eid']
            eqtype = game_config.equip_config[eid]['eqtype']
            if eqtype not in [5, 6]:
                return 11,{'msg':utils.get_msg('mystery_store','category_not_match')}

        #获取宝物计算系数                             装备等级配置
        treasure_stove_gold_coe = float(game_config.equip_exp_config['treasure_stove_gold_coe'])
        #返回铜钱
        return_gold = 0
        #返回道具
        return_props = {}
        #返还的 不同等级的经验马/经验书数量
        num_book4=num_book3=num_book2=num_book1=num_horse4=num_horse3=num_horse2=num_horse1 = 0
        # 不同等级的经验马/经验书提供的经验
        props_conf = game_config.props_config
        equip5_prop_list = []
        equip6_prop_list = []
        for prop_id in props_conf:
            if props_conf[prop_id].get('used_by') == 'equip5':
                equip5_prop_list.append((prop_id, props_conf[prop_id]['exp']))
            elif props_conf[prop_id].get('used_by') == 'equip6':
                equip6_prop_list.append((prop_id, props_conf[prop_id]['exp']))
        equip5_prop_list.sort(reverse=True)
        equip6_prop_list.sort(reverse=True)

        def calculate_rebate(prop_exp_list, all_exp):
            rebate_props = {}
            left_exp = all_exp
            for prop, exp in prop_exp_list:
                rebate_props[prop] = left_exp // exp
                left_exp = left_exp % exp
                if not left_exp:
                    break
            return rebate_props

        for equip_info in msg['equips_info']:
            eid = equip_info['eid']
            #宝物装备升级所消耗铜钱
            cost_update_gold = equip_info['cur_experience'] * treasure_stove_gold_coe
            #获取装备的星级
            star = str(game_config.equip_config[eid].get('star',1))
            #宝物装备炼化基础值
            base_gold = game_config.equip_exp_config['treasure_sell_gold'].get(star,500)
            eqtype = game_config.equip_config[eid]['eqtype']
            #计算返还经验书的数量。经验书有不同等级，分别计算个数。5000 3000 1000 500为相应等级的经验书所提供的经验
            if eqtype == 5:
                return_props.update(calculate_rebate(equip5_prop_list, cost_update_gold))
            #计算返还经验马  逻辑同经验书
            elif eqtype == 6:
                return_props.update(calculate_rebate(equip6_prop_list, cost_update_gold))
            return_gold += int(base_gold + (cost_update_gold * treasure_stove_gold_coe))
        #返还道具
        for props_id in return_props:
            user_pack_obj.add_props(props_id,return_props[props_id], 'stove')
        #用户删除装备
        user_equip_obj.delete_equip(msg['equips_ueids'], where='stove')
        #返还铜钱
        user_property_obj.add_gold(return_gold, where='stove')
        data = {'gold':return_gold,'props':return_props}
    else:
        return 11,{'msg':utils.get_msg('mystery_store','no_stove_category')}

#   print '#### stove_info:', data

    return rc,{'stove_info':data}


def get_store_info(rk_user, params):
    """
    得到当前玩家的神秘商店信息
    前段点击 和 前段倒计时结束时调用此接口 神秘商店时调用此接口
     此接口会先判断是否要自动刷新商品
     Returns:
        fight_soul: 玩家战魂数
        next_auto_refresh_time 下次刷新时间datetimestr
        free_refresh_cnt 可免费刷新次数 
        store  商店物品信息
    """
    user_mystery_store_obj = rk_user.user_mystery_store
    return _pack_store_info(user_mystery_store_obj.incre_free_refresh_cnt())


def refresh_store_by_self(rk_user,params):
    """
    玩家主动刷新时  调用此接口
    1. 若有免费刷新次数, 消耗刷新次数
    2. 若有刷新令, 消耗刷新令28_props
    3. 以上都没有, 用元宝刷新

    """
    user_property_obj = rk_user.user_property

    user_mystery_store_obj = rk_user.user_mystery_store
    user_pack_obj = rk_user.user_pack
    needed_cost = int(game_config.mystery_store_config["store_refresh_cost"])

    props_config = game_config.props_config
    refresh_mystery_props_id = ''
    #获取用户的道具配置
    for props_id in props_config:
        if props_config[props_id].get('used_by','') == 'refresh_mystery':
            refresh_mystery_props_id = props_id

    if user_mystery_store_obj.free_refresh_cnt:
        user_mystery_store_obj.free_refresh_cnt -= 1
        user_mystery_store_obj.put()
    elif user_pack_obj.has_props(refresh_mystery_props_id):
        user_pack_obj.minus_props(refresh_mystery_props_id, 1, 'refresh_mystery_store')
    # 根据vip用元宝可刷新次数判断是否可以刷新
    elif vip.check_limit_recover(rk_user, 'recover_mystery_store') >= 0 and \
         user_property_obj.minus_coin(needed_cost, 'refresh_mystery_store'):
        # 已刷新次数+1
        user_property_obj.add_recover_times('recover_mystery_store')        
    else:
        raise GameLogicError('user', 'not_enough_coin')
    
    user_mystery_store_obj.refresh_store()
    return _pack_store_info(user_mystery_store_obj.store_info())


def buy_store_goods(rk_user, params):
    """
    玩家购买指定商品时逻辑
    params  参数需包含 store_type： 可选  "packages"   "gold_store"  or  "coin_store" 
                     goods_index:  int  为所买商品在所属类型的index   
    """
    #store_type = params['store_type']
    goods_index = int(params['goods_index'])

    buy_goods_info = {}
    goods_list = []
    user_mystery_store_obj = rk_user.user_mystery_store

    buy_goods_info = user_mystery_store_obj.store_info()['store'][goods_index]
    goods_list.append(buy_goods_info['goods'])
    need = "need_coin" if buy_goods_info.get("need_coin", 0) else "need_fight_soul"
    needed_cost = buy_goods_info.get(need, 0)
    fight_or_coin = need.replace("need_", "")
   

    #  根据store_type  决定是 消耗元宝还是战魂
    minus_func = getattr(rk_user.user_property, "minus_" + fight_or_coin)

    if not minus_func(needed_cost, 'buy_mystery_store_goods'):
        raise GameLogicError('user', 'not_enough_' + fight_or_coin)

    # 发商品    
    # 前端通过rc 是否等于 0 判断是否购买成功
    if not user_mystery_store_obj.update_goods_info_by_index(goods_index):
        raise GameLogicError('has bought this item')
    all_get_goods = tools.add_things(rk_user, goods_list, where=u"buy_from_mystery_store")

    # 记录log
    log_data = {"cost": fight_or_coin, "cost_num": needed_cost, "goods": goods_list}
    data_log_mod.set_log("MysteryStore", rk_user, **log_data)

    return {'get_info': all_get_goods}


def _pack_store_info(store_info):
    store_info = copy.deepcopy(store_info)
    for each_good_info in store_info["store"]:
        good_id = each_good_info["goods"]["_id"]
        num = each_good_info["goods"]["num"]
        pack = tools.pack_good(good_id, num)
        each_good_info["goods"] = pack
    return store_info

