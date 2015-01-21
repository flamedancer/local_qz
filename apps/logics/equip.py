#-*- coding: utf-8 -*-
""" filename:equip.py
    该文件里面的主要功能有
    1  获取装备碎片掉落的关卡信息
    2  装备的升级
    3  装备的售出
    4  装备的绑定和卸载
"""
import copy
from apps.models.user_equips import UserEquips
from apps.models.user_cards import UserCards
from apps.models.user_property import UserProperty
from apps.models.user_pack import UserPack
from apps.common import utils
from apps.common import tools
from apps.config.game_config import game_config

from apps.common.exceptions import GameLogicError
from apps.common.exceptions import ParamsError

def get_equip_drop_info():
    '''
    * 获取装备碎片掉落的关卡信息
    * miaoyichao
    '''
    equip_drop_info = {}
    equip_soul_drop_info = {}
    #初始化所有的掉落
    #获取战场信息
    dungeon_config = game_config.normal_dungeon_config
    for floor_id in dungeon_config:
        #遍历所有的floor
        floor_info = dungeon_config[floor_id]
        for room_id in floor_info['rooms']:
            #遍历所有的room
            equip_soul_drop = floor_info['rooms'][room_id].get('drop_info',{}).get('soul',[])
            equip_drop = floor_info['rooms'][room_id].get('drop_info',{}).get('equip',[])
            for equip_id in equip_soul_drop:
                if 'equip' in equip_id:
                    if equip_id not in equip_soul_drop_info:
                        equip_soul_drop_info[equip_id] = []
                    #遍历所有的装备碎片 然后将相关的floor和room添加进去
                    equip_soul_drop_info[equip_id].append({'floor_id':floor_id,'room_id':room_id})
            for equip_id in equip_drop:
                if equip_id not in equip_drop_info:
                    equip_drop_info[equip_id] = []
                #遍历所有的装备 然后将相关的floor和room添加进去
                equip_drop_info[equip_id].append({'floor_id':floor_id,'room_id':room_id})
    #结果返回
    return {'equip_drop_info':equip_drop_info,'equip_soul_drop_info':equip_soul_drop_info}

def __check_can_update(base_equip,user_lv):
    """
    * 检查是否可以强化
    * 装备强化上限等级是玩家当前等级的2倍 或者是装备预设的最大等级
    """
    update_flag = 1
    #判断最大等级
    if base_equip['cur_lv']>= game_config.equip_config[base_equip['eid']].get('equipMaxLv',0):
        update_flag = 0
    else:
        #判断当前等级是否是用户等级的2倍
        if base_equip['cur_lv'] >= 2*user_lv:
            #判断上限等级是玩家当前等级的2倍 
            update_flag = 0
    return update_flag

def get_user_lv(uid):
    '''
    * 获取用户的等级
    '''
    up = UserProperty.get(uid)
    return up.property_info.get('lv',1)

def __check_same_type(user_equips_lists,uetype,cost_list):
    '''
    * 检查消耗的素材的类型是否和要升级的装备的类型是一致的
    * miaoyichao
    '''

    #对要消耗的装备遍历
    for cost in cost_list:
        #获取装备的eid
        cost_eid = user_equips_lists[cost]['eid']
        #获取装备的类型
        cost_type = game_config.equip_config[cost_eid]['eqtype']
        #如果类型不一致 直接返回false
        if not cost_type == uetype:
            return False
    #装备类型一致返回true
    return True

def binding_or_not(rk_user,params):
    """装备 武将
    
    ucid = ucid1|ucid2|ucid3
    ueid = ueid,ueid,ueid|ueid,ueid,ueid|ueid,ueid,ueid
    """
    params_ucid = params['ucid']
    params_ueids = params['ueid']

    ucids = params_ucid.split("|")
    ueids_group = params_ueids.split("|")

    user_equip_obj = rk_user.user_equips
    user_card_obj = rk_user.user_cards
    user_equips = user_equip_obj.equips
    all_cards = user_card_obj.cards

    equip_config = game_config.equip_config

    # 如果武将为空
    if not ucids or (len(ucids) != len(ueids_group)):
        raise ParamsError()
    ucid_ueids = dict(zip(ucids, ueids_group))
    for ucid, ueids in ucid_ueids.items():
        ueids = utils.remove_null(ueids.split(','))
        #获取用户的所有的武将和装备的 id
        if ucid not in all_cards:
            print ucid, ueids 
            print all_cards
            raise GameLogicError('card', 'no_card')
        all_eqtype = []
        # 判断装备是否存在
        for ueid in ueids:
            if ueid not in user_equips:
                raise GameLogicError('equip', 'no_equip')
            eid = user_equips[ueid]['eid']
            eqtype = equip_config[eid].get('eqtype', 1)
            if eqtype in all_eqtype:
                raise GameLogicError('equip', 'invalid_deck')
            else:
                all_eqtype.append(eqtype)
        #开始绑定信息
        user_equip_obj.bind_equip(ucid, ueids)

    #判断新手引导
    newbie_step = int(params.get('newbie_step',0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "binding_equip")
    return {}

def update(rk_user,params):
    """
    * 装备的升级
    * miaoyichao
    """
    #获取要升级的装备和升级所需要的参数  要升多少级 或者是升级的经验
    base_ueid = params['base_ueid']
    #获取前台传递过来的装备类型

    base_type = int(params['base_type'])

    #获取装备配置信息
    user_equips_obj = UserEquips.get_instance(rk_user.uid)
    #获取该用户的装备信息
    user_equips_lists = user_equips_obj.equips
    #武器、护甲、头盔、饰品4类通过游戏中的铜钱来升级强化  兵法及坐骑，升级方式通过消耗特定素材进行强化
    #获取装备的类型 1:武器(攻击),2:护甲（防御）,3:头盔（血量）,4:饰品（回复）,5:兵法,6:坐骑
    base_eid = user_equips_lists[base_ueid]['eid']
    uetype = int(game_config.equip_config[base_eid]['eqtype'])
    #传递过来的参数类型和从配置数据库得到的不一致
    if not base_type == uetype:
        return 11,{'msg':utils.get_msg('equip','params_wrong')}
    #检查要强化的武器是不是在用户装备中
    if base_ueid not in user_equips_lists:
        return 11,{'msg':utils.get_msg('equip','no_equip')}
    #获取用户的该装备信息
    base_ueid_info = user_equips_obj.get_equip_dict(base_ueid)    
    #获取用户的等级
    user_lv = get_user_lv(rk_user.uid)
    #检查base卡是是否满级
    if not __check_can_update(base_ueid_info,user_lv):
        return 11,{'msg':utils.get_msg('equip','cannot_update')}

    # 暴击次数
    crit_time = 0
    #只需要金钱就可以强化的
    if uetype<=4:
        #获取vip等级
        vip_lv = rk_user.user_property.vip_cur_level
        #获取装备的当前等级
        cur_equip_lv = base_ueid_info['cur_lv']
        cur_cost_gold = game_config.equip_exp_config['common_gold'].get(str(cur_equip_lv),0)
        next_cost_gold = game_config.equip_exp_config['common_gold'].get(str(cur_equip_lv+1),100)
        #获取装备的星级
        star = game_config.equip_config[base_ueid_info['eid']].get('star',2)
        #获取系数
        coefficient =  game_config.equip_exp_config['common_gold_coe'][str(star)]
        update_gold = int((next_cost_gold - cur_cost_gold)*coefficient)
        # #判断用户金币是否足够
        if not rk_user.user_property.is_gold_enough(update_gold):
            return 11,{'msg':utils.get_msg('user','not_enough_gold')}
        try:
            auto_flag = params['auto_flag']
        except:
            auto_flag = ''
        if not auto_flag:
            #给装备增加经验和等级
            crit_time, new_equip_info = user_equips_obj.add_com_equip_exp(base_ueid,vip_lv,user_lv,where='equip_update')
            #扣除消费的金币
            rk_user.user_property.minus_gold(update_gold,'common_equip_update')
            #格式化返回的数据的内容
            data = {}
            # tmp = {}
            # tmp['ueid'] = base_ueid
            # user_equips_obj = UserEquips.get_instance(rk_user.uid)
            # user_equips_lists = user_equips_obj.equips
            # tmp.update(user_equips_lists[base_ueid])
            data['up_lv'] = [new_equip_info['cur_lv']]
            data['new_equip_info'] = new_equip_info
        else:
            #自动强化装备
            crit_time, data = user_equips_obj.auto_update_equip(rk_user,base_ueid,vip_lv,user_lv,where='common_equip_auto_update')
        data['crit_time'] = crit_time

        return 0, data
    elif 5<=uetype<=6:
        #该部分需要特定的道具进行升级
        #检查参数是否合法
        try:
            cost_props = params['cost_props']
        except:
            return 11,{'msg':utils.get_msg('equip','params_wrong')}
        cost_props_list = cost_props.split(',')
        cost_props_list = utils.remove_null(cost_props_list)
        #格式化消耗的道具
        all_cost_props = {}
        for cost_props_id in cost_props_list:
            if cost_props_id not in all_cost_props:
                all_cost_props[cost_props_id] = 0
            all_cost_props[cost_props_id] += 1
        #获取用户背包信息
        user_pack_obj = UserPack.get_instance(rk_user.uid)
        check_use_type = 'equip%s' %uetype
        all_exp = 0
        #检查用户背包是否有这么多的道具和道具的使用类型
        for props_id in all_cost_props:
            num = int(all_cost_props[props_id])
            #检查数量是否足够
            if not user_pack_obj.is_props_enough(props_id,num):
                return 11,{'msg':utils.get_msg('pack', 'not_enough_props')}
            if not check_use_type == game_config.props_config[props_id]['used_by']:
                return 11,{'msg':utils.get_msg('pack', 'wrong_used')}
            all_exp += int(game_config.props_config[props_id]['exp']) * num
        #计算升级所消耗的金钱 强制转化为int类型的
        update_gold = int(all_exp * game_config.equip_exp_config['gold_exp_transform_coe'].get('treasure_update_coe',1))
        #判断用户金币是否足够
        if not rk_user.user_property.is_gold_enough(update_gold):
            return 11,{'msg':utils.get_msg('user','not_enough_gold')}
        #所有条件都满足的情况下 开始扣除金币和道具 然后开始添加经验
        #扣除消费的金币
        rk_user.user_property.minus_gold(update_gold,'treasure_equip_update')
        #扣除道具
        user_pack_obj.minus_multi_props(all_cost_props,where='treasure_equip_update')
        #添加经验
        new_equip_info = user_equips_obj.add_treasure_equip_exp(base_ueid,all_exp,user_lv,where='treasure_equip_update')
        #格式化返回的数据的内容
        data = {}
        data['up_lv'] = [new_equip_info['cur_lv']]
        data['new_equip_info'] = new_equip_info

        return 0,data
    else:
        return 11,{'msg':utils.get_msg('equip','params_wrong')}


def upgrade(rk_user, params):
    """升品操作

    Args:
        ueid: 需要升品的装备 唯一标示号
        cost_ueid: 升品需要消耗的装备唯一标示号， 若为 '' 表示不需要消耗装备
                多个装备用 , 隔开

    """
    ueid = params['ueid']
    cost_ueids = params.get('cost_ueid', '').split(",")
    user_equips_obj = rk_user.user_equips
    # 检查是否存在
    if not user_equips_obj.has_ueid(ueid):
        return 11, {'msg': utils.get_msg('equip', 'no_equip')}

    ueid_info = user_equips_obj.equips[ueid]
    quality = ueid_info['quality']

    equip_upgrade_config = rk_user.game_config.equip_upgrade_config
    quality_order = equip_upgrade_config['quality_order']
    next_quality_index = quality_order.index(quality) + 1
    # 已达到最大品级
    if next_quality_index >= len(quality_order):
        return 11, {'msg': utils.get_msg('equip', 'already_max_quality')}

    equip_type = rk_user.game_config.equip_config[ueid_info['eid']]['eqtype']
    quality = ueid_info['quality']

    needs = copy.deepcopy(equip_upgrade_config[quality][equip_type])

    # 判断是否需要同名卡牌
    needs_equip_num = 0
    if "needs_equip_num" in equip_upgrade_config[quality][equip_type]:
        needs_equip_num = needs.pop("needs_equip_num")

    suited_cost_equip = []
    if needs_equip_num > 0:
        suited_cost_equip = []
        for equip_ueid in cost_ueids:

            if user_equips_obj.has_ueid(equip_ueid) and \
            user_equips_obj.equips[equip_ueid]['quality'] == quality.split("+")[0] + "+0":
                suited_cost_equip.append(equip_ueid)
        if len(suited_cost_equip) < needs_equip_num:
            return 11, {'msg': 'lack same color equip'}
    else:
        suited_cost_equip = []

    needs = utils.format_award(needs)
    if not tools.is_things_enough(rk_user, needs):
        return 11, {'msg': "not enough things"}


    user_equips_obj.delete_equip(suited_cost_equip, where="upgrade_equip")
    tools.del_things(rk_user, needs, where="upgrade_equip")

    next_quality = quality_order[next_quality_index]
    new_equip_info = rk_user.user_equips.upgrade_equip(ueid, next_quality)

    # 判断新手引导
    newbie_step = int(params.get('newbie_step', 0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "equip_upgrade")
    return 0, {"new_equip_info": new_equip_info}


def equip_stove(rk_user,params):
    """
    炼化
    """
    sell_ueids = params.get('sell_ueids')
    #卖出的装备为空的时候的处理
    if not sell_ueids:
        return 11,{'msg':utils.get_msg('equip','no_equip')}
    #获取装备的列表
    sell_ueids = sell_ueids.split(',')
    #装备列表去空
    sell_ueids = utils.remove_null(sell_ueids)
    #这里执行两次的原因是防止前台传递过来的是 ,,
    if not sell_ueids:
        return 11,{'msg':utils.get_msg('equip','no_equip')}
    #获取用户装备对象
    user_equip_obj = UserEquips.get_instance(rk_user.uid)
    user_equips = user_equip_obj.equips
    #循环要卖出的装备 判断是否可以卖出
    for sell_ueid in sell_ueids:
        #检查装备是否存在
        if sell_ueid not in user_equips:
            return 11,{'msg':utils.get_msg('equip','no_equip')}
        #检查装备是否装备武将
        try:
            sell_ueid_bind = user_equips[sell_ueid]['used_by']
        except:
            sell_ueid_bind = ''
        #判断装备是否已经装备在武将身上
        if sell_ueid_bind:
            return 11,{'msg':utils.get_msg('equip','is_used')}
    #计算卖出获得的铜钱数量
    #get_gold = 0
    #获取用户的装备的eid和等级
    sell_eids_info = [user_equip_obj.get_equip_dict(ueid) for ueid in sell_ueids]
    #treasure_sell_gold = game_config.equip_exp_config['treasure_sell_gold']
    #common_base_gold = game_config.equip_exp_config['common_base_gold']
    return 0,{'equips_info':sell_eids_info,'equips_ueids':sell_ueids}
    # for sell_eid_info in sell_eids_info:
    #     #获取装备的eid
    #     eid = sell_eid_info['eid']
    #     #获取装备的经验值
    #     sell_equip_exp = sell_eid_info['cur_experience']
    #     #获取装备的类型  不同类型的转换系数不一样 如果找不到就默认为1 武器
    #     sell_equip_config = game_config.equip_config.get(eid,{})
    #     sell_equip_type = sell_equip_config.get('eqtype',1)
    #     sell_equip_star = str(sell_equip_config.get('star',2))
    #     if sell_equip_type>=5:
    #         #5 6 是宝物类型
    #         sell_type = 'treasure_sell_coe'
    #         base_gold = treasure_sell_gold.get(sell_equip_star,1000)
    #     else:
    #         #1 2 3 4 是普通装备类型
    #         sell_type = 'common_exp_coe'
    #         base_gold = common_base_gold.get(sell_equip_star,1000)
    #     #卖出装备需要一个当前经验和一个转换系数  以及每个装备的卖出初始值  系数是在配置信息中查找
    #     get_gold += base_gold + int(sell_equip_exp*game_config.equip_exp_config['gold_exp_transform_coe'][sell_type])
    # #用户加钱
    # rk_user.user_property.add_gold(get_gold,where='sell_equip')
    # #用户删除装备
    # user_equip_obj.delete_equip(sell_ueids,where='sell_equip')
    # return 0,{'get_gold':get_gold}


