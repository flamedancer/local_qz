#-*- coding: utf-8 -*-
""" filename:pack.py
    该文件的主要功能函数有
    1  获取背包的所有的信息
    2  药品的合成
    3  背包内容的掉落信息
    4  获取和设置药品编队
    5  背包内容的售出
    6  使用道具进行添加体力
    7  使用道具进行重命名
    8  使用道具添加经验点
    9  在商城中购买道具

"""

from apps.models.user_property import UserProperty
from apps.models.user_pack import UserPack
from apps.models.user_collection import UserCollection
from apps.common import utils
from apps.config.game_config import game_config
from apps.common.exceptions import GameLogicError
from apps.logics import main


def get_store(rk_user, params):
    """取得用户背包信息
    """
    user_pack_obj = rk_user.user_pack
    data = {}
    data['materials'] = user_pack_obj.materials
    data['props'] = user_pack_obj.props
    drop_info = get_drop_info()
    data['drop_mat_info'] = drop_info['drop_mat_info']
    data['item_deck'] = [{},{},{},{},{}]
    data['items'] = {}
    #data['drop_props_info'] = drop_info['drop_props_info']
    return 0,data


def get_drop_info():
    '''
    获取素材掉落的那些关卡
    '''
    all_mat = {}
    #获取素材配置信息
    material_config = game_config.material_config
    #遍历获取所有素材和药品的信息
    all_material_config = material_config.keys()
    #获取普通战场配置信息
    dungeon_config = game_config.normal_dungeon_config
    for floor_id in dungeon_config:
        floor_info = dungeon_config[floor_id]
        for room_id in floor_info['rooms']:
            room_config = floor_info['rooms'][room_id]
            material_drop = room_config.get('drop_info', {}).get('mat', {})
            tmp = {'floor_id': floor_id, 'room_id': room_id}
            for mat_id in material_drop:
                if mat_id not in all_material_config:
                    pass
                else:
                    if mat_id not in all_mat:
                        all_mat[mat_id] = []
                    all_mat[mat_id].append(tmp)

    data = {}
    data['drop_mat_info'] = all_mat
    return data


def store_sell(rk_user, params):
    """背包卖出
    params:
        items:
            itemid:num,itemid:num,itemid:num
        materials:
            materialid:num,materialid:num
    """
    sell_materials = {}
    sell_props = {}
    user_pack_obj = rk_user.user_pack
    material_config = game_config.material_config
    props_config = game_config.props_config
    get_gold = 0

    for good_type in ['materials', 'props']:
        goods = params.get(good_type, None)
        if not goods:
            continue
        if good_type == 'materials':
            material_ls = goods.split(',')
            material_ls = utils.remove_null(material_ls)
            for m in material_ls:
                m_id, m_num = m.split(':')
                m_num = abs(int(m_num))
                if not user_pack_obj.is_material_enough(m_id, m_num):
                    return 11, {'msg':utils.get_msg('pack', 'not_enough_material')}
                sell_materials[m_id] = m_num
                get_gold += m_num * material_config[m_id].get('sell_gold', 0)
        else:
            props_ls = goods.split(',')
            props_ls = utils.remove_null(props_ls)
            for p in props_ls:
                p_id,p_num = p.split(':')
                p_num = abs(int(p_num))
                if not user_pack_obj.is_props_enough(p_id,p_num):
                    return 11, {'msg':utils.get_msg('pack', 'not_enough_props')}
                sell_props[p_id] = p_num
                get_gold += p_num * props_config[p_id].get('sell_gold', 0)
    #加铜钱
    if get_gold > 0:
        rk_user.user_property.add_gold(get_gold, 'pack_store_sell')
    #减物品
    for m_id in sell_materials:
        user_pack_obj.minus_material(m_id, sell_materials[m_id], 'pack_store_sell')
    for p_id in sell_props:
        user_pack_obj.minus_props(p_id, sell_props[p_id], 'pack_store_sell')
    return 0,{'get_gold': get_gold}


def add_stamina(rk_user,params):
    '''
    * 使用体力丹回复体力
    miaoyichao
    '''
    cost_props_param = params.get('cost_props')
    cost_props = cost_props_param.split(',')
    cost_props = utils.remove_null(cost_props)
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    cost_props_copy = {}
    get_stamina = 0
    for cost in cost_props:
        props_id = cost.split(':')[0]
        num = int(cost.split(':')[1])
        #判断props的用途是否是增加体力的
        if not game_config.props_config[props_id].get('used_by','') == 'stamina':
            return 11,{'msg':utils.get_msg('pack', 'wrong_used')}
        #判断道具数量是否足够
        if not user_pack_obj.is_props_enough(props_id,num):
            return 11,{'msg':utils.get_msg('pack', 'not_enough_props')}
        #道具数量足够的话就开始整理道具
        cost_props_copy[props_id] = num
        #默认没取到的时候 增加的体力值是0
        get_stamina += int(game_config.props_config[props_id].get('stamina_num',0))*num
    #扣除道具
    user_pack_obj.minus_multi_props(cost_props_copy,where='pack.add_stamina')
    #增加体力
    rk_user.user_property.add_stamina(get_stamina)
    #结果返回
    return 0,{'get_stamina':get_stamina}


def rename(rk_user, params):
    """ 使用更名令进行重命名"""
    cost_props = params.get('cost_props')
    new_name = params.get('new_name','')
    #判断是否是更命令道具
    if not game_config.props_config.get(cost_props,{}).get('used_by','') == 'rename':
        raise GameLogicError('pack', 'wrong_used')
    #判断用户是否有该道具
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    if not user_pack_obj.is_props_enough(cost_props,1):
        raise GameLogicError('pack', 'not_enough_props')
    #有道具的情况进行重命名
    main.set_name(rk_user, {"name": new_name})
    #减道具
    user_pack_obj.minus_props(cost_props, 1, where='pack.rename')
    return {'new_name': new_name}


def add_exp_point(rk_user,params):
    '''
    添加经验点接口
    根据用户提交的道具 id 给用户添加经验点
    '''
    props_id = params['props_id']
    num = int(params['num'])
    #根据 id 获取道具的使用途径
    props_id_config = game_config.props_config.get(props_id,{})
    used_by = props_id_config.get('used_by','')
    #判断使用的用途
    if used_by != 'card':
        return 11,{'msg':utils.get_msg('pack', 'wrong_used')}
    #判断用户道具是否足够
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    if not user_pack_obj.is_props_enough(props_id,num):
        return 11,{'msg':utils.get_msg('pack', 'not_enough_props')}
    #计算经验点数
    add_exp_point = int(num*props_id_config.get('exp',0))
    #所有条件都满足的话  删除道具 添加经验点
    user_pack_obj.minus_props(props_id,num,where='add_exp_point')
    user_property_obj = UserProperty.get(rk_user.uid)
    user_property_obj.add_card_exp_point(add_exp_point, "by_props")
    print user_property_obj.property_info['vip_charge_info']
    #结果返回
    return 0,{'add_exp_point':add_exp_point}


def buy_props(rk_user, params):
    """购买道具的接口"""
    #获取道具 id 和购买的组数
    props_index = params['props_indexs']
    #获取商店配置
    this_props_shop_config = game_config.props_store_config['props_sale'].get(props_index, {})
    # 获取道具id
    props_id = this_props_shop_config['id']
    # 获取单价
    price = this_props_shop_config.get('need_coin', 0)
    # 获取道具数量
    num = this_props_shop_config.get('num', 1)

    user_pack_obj = rk_user.user_pack
    # vip等级购买次数 是否足够
    user_pack_obj.add_store_has_bought_cnt(props_index)

    print price, num, props_index

    # 判断元宝是否足够
    if not rk_user.user_property.minus_coin(price, 'buy_props'):
        raise GameLogicError('user','not_enough_coin')
    # 添加道具
    user_pack_obj.add_props(props_id, num, where='buy_props')
    return {}


def get_collection(rk_user,params):
    """取得装备，材料的图鉴信息
    """
    user_collect_obj = UserCollection.get_instance(rk_user.uid)
    return 0,{
              'collection':{
                  'equips':user_collect_obj.get_collected_cards('equips'),
                  'materials':user_collect_obj.get_collected_cards('materials'),
                  'props':user_collect_obj.get_collected_cards('props'),
                }
              }
