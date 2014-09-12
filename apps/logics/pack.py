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
import copy
from apps.models.user_property import UserProperty
from apps.models.user_base import UserBase
from apps.models.user_pack import UserPack
from apps.models.user_collection import UserCollection
from apps.common import utils
from apps.config.game_config import game_config


def produce_item(rk_user,params):
    """
    生产药水
    params:
        item: 药水id:num,药水id:num
    """
    #仓库是否满
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    item = params['item']
    item_ls = item.split(',')
    items = {}
    for it in item_ls:
        if it:
            item_id,num = it.split(':')
            items[item_id] = int(num)
    #合成所需的材料和药水
    total_need_material = {}
    total_need_item = {}
    for item_id in items:
        item_num = items[item_id]
        if item_id not in game_config.item_config:
            return 6,{'msg':utils.get_msg('pack', 'no_item')}
        #检查材料
        item_conf = game_config.item_config[item_id]
        need_material = item_conf['need_material']
        for material_id in need_material:
            if 'mat' in material_id:#材料类型
                num = int(need_material[material_id])*item_num
                if material_id in total_need_material:
                    total_need_material[material_id] += num
                else:
                    total_need_material[material_id] = num
            elif 'item' in material_id:#道具类型
                num = int(need_material[material_id])*item_num
                if material_id in total_need_item:
                    total_need_item[material_id] += num
                else:
                    total_need_item[material_id] = num
            else:
                return 11,{'msg':utils.get_msg('pack','not_enough_material')}
    #检查材料是否足够
    for material_id in total_need_material:
        if not user_pack_obj.is_material_enough(material_id,total_need_material[material_id]):
            return 11,{'msg':utils.get_msg('pack','not_enough_material')}
    #检查药品道具是否足够
    total_need_item_copy = copy.deepcopy(total_need_item)
    for material_id in total_need_item_copy:
        can_use_cnt = user_pack_obj.get_item_can_use_cnt(material_id)
        produce_item_cnt = items.get(material_id,0)
        if produce_item_cnt>0:
            if total_need_item[material_id] >= produce_item_cnt:
                total_need_item[material_id] -= produce_item_cnt
                items.pop(material_id)
                if total_need_item[material_id] <= 0:
                    total_need_item.pop(material_id)
            else:
                items[material_id] -= total_need_item[material_id]
                total_need_item.pop(material_id)
        if total_need_item.get(material_id,0) > can_use_cnt:
            return 11,{'msg':utils.get_msg('pack','not_enough_material')}
    #扣材料
    user_pack_obj.minus_materials(total_need_material,'pack_produce_item')
    #扣药品道具
    user_pack_obj.minus_items(total_need_item,'pack_produce_item')
    #加药水
    for item_id in items:
        item_num = items[item_id]
        user_pack_obj.add_item(item_id,item_num,'pack_product_item')
    return 0,{}

def get_store(rk_user,params):
    """取得用户背包信息
    """
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    data = {}
    data['items'] = user_pack_obj.items
    data['materials'] = user_pack_obj.materials
    data['props'] = user_pack_obj.props
    data['item_deck'] = user_pack_obj.item_deck
    drop_info = get_drop_info()
    data['drop_mat_info'] = drop_info['drop_mat_info']
    data['drop_item_info'] = drop_info['drop_item_info']
    #data['drop_props_info'] = drop_info['drop_props_info']
    return 0,data

def get_drop_info():
    '''
    获取素材掉落的那些关卡
    '''
    all_mat = {}
    all_items = {}
    #获取素材配置信息
    material_config = game_config.material_config
    item_config = game_config.item_config
    #遍历获取所有素材和药品的信息
    all_material_config = material_config.keys()
    all_item_config = item_config.keys()
    #获取普通战场配置信息
    dungeon_config = game_config.normal_dungeon_config
    for floor_id in dungeon_config:
        floor_info = dungeon_config[floor_id]
        for room_id in floor_info['rooms']:
            room_config = floor_info['rooms'][room_id]
            material_drop = room_config.get('drop_info',{}).get('mat',{})
            item_drop = room_config.get('drop_info',{}).get('item',{})
            tmp = {'floor_id':floor_id,'room_id':room_id}
            for mat_id in material_drop:
                if mat_id not in all_material_config:
                    pass
                else:
                    if mat_id not in all_mat:
                        all_mat[mat_id] = []
                    all_mat[mat_id].append(tmp)
            for item_id in item_drop:
                if item_id not in all_item_config:
                    pass
                else:
                    if item_id not in all_items:
                        all_items[item_id] = []
                    all_items[item_id].append(tmp)
    data = {}
    data['drop_mat_info'] = all_mat
    data['drop_item_info'] = all_items
    return data

def get_item_deck(rk_user,params):
    """获取item_deck
    """
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    return 0,{'item_deck':user_pack_obj.item_deck}

def set_item_deck(rk_user,params):
    """设置药品deck
      params:
        item_deck:药品id:数量,,药品id:数量,药品id:数量,
    """
    param_item_deck = params['item_deck']
    new_deck = param_item_deck.split(',')
    no_repeat_deck = utils.remove_null(new_deck)
    #检查是否有重复的item
    if len(no_repeat_deck) != len(list(set(no_repeat_deck))):
        return 11,{'msg':utils.get_msg('pack','invalid_item_deck')}
    if not len(new_deck) == game_config.pack_config['item_deck_length']:
        return 11,{'msg':utils.get_msg('pack','invalid_item_deck')}
    #检查携带数是否超过上限
    item_config = game_config.item_config
    item_new_deck = []
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    for item in new_deck:
        if item:
            item_id,num = item.split(':')
            #判断药片是否在配置中
            if item_id not in item_config:
                return 11,{'msg':utils.get_msg('pack', 'no_item')}
            max_num = item_config[item_id]['max_num']
            user_num = user_pack_obj.get_item_num(item_id)
            #获取最最大容量和用户背包中药品数量的最小值
            set_num = min(max_num,user_num)
            #判断数量不为空
            if set_num:
                item_new_deck.append({item_id:set_num})
            else:
                #用户没有这个药品
                item_new_deck.append({})
        else:
            item_new_deck.append({})
    item_ls = [item.keys()[0] for item in item_new_deck if item.keys()]
    if len(item_ls) != len(set(item_ls)):
        return 11,{'msg':utils.get_msg('pack','invalid_item_deck')}
    if item_new_deck:
        user_pack_obj.set_item_deck(item_new_deck)
    # if item_ls:
    #     rk_user.user_property.has_set_item_deck()
    return 0,{}

def store_sell(rk_user,params):
    """背包卖出
    params:
        items:
            itemid:num,itemid:num,itemid:num
        materials:
            materialid:num,materialid:num
    """
    sell_items = {}
    sell_materials = {}
    sell_props = {}
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    equip_config = game_config.equip_config
    item_config = game_config.item_config
    material_config = game_config.material_config
    props_config = game_config.props_config
    get_gold = 0
    #因为只有三种类型   所以只需要遍历这三种即可
    for good_type in ['items','materials','props']:
        goods = params.get(good_type,None)
        if not goods:
            continue
        if good_type == 'items':
            items_ls = goods.split(',')
            items_ls = utils.remove_null(items_ls)
            for item in items_ls:
                item_id,item_num = item.split(':')
                item_num = abs(int(item_num))
                #卖出数量不能超过总数减队伍携带数
                if item_num > user_pack_obj.get_item_can_use_cnt(item_id):
                    return 11,{'msg':utils.get_msg('pack', 'not_enough_item')}
                sell_items[item_id] = item_num
                get_gold += item_num*item_config[item_id].get('sell_gold',0)
        elif good_type == 'materials':
            material_ls = goods.split(',')
            material_ls = utils.remove_null(material_ls)
            for m in material_ls:
                m_id,m_num = m.split(':')
                m_num = abs(int(m_num))
                if not user_pack_obj.is_material_enough(m_id,m_num):
                    return 11,{'msg':utils.get_msg('pack', 'not_enough_material')}
                sell_materials[m_id] = m_num
                get_gold += m_num*material_config[m_id].get('sell_gold',0)
        else:
            props_ls = goods.split(',')
            props_ls = utils.remove_null(props_ls)
            for p in props_ls:
                p_id,p_num = p.split(':')
                p_num = abs(int(p_num))
                if not user_pack_obj.is_props_enough(p_id,p_num):
                    return 11,{'msg':utils.get_msg('pack', 'not_enough_props')}
                sell_props[p_id] = p_num
                get_gold += p_num*props_config[p_id].get('sell_gold',0)
    #加铜钱
    if get_gold > 0:
        rk_user.user_property.add_gold(get_gold,'pack_store_sell')
    #减物品
    for item_id in sell_items:
        user_pack_obj.minus_item(item_id,sell_items[item_id],'pack_store_sell')
    for m_id in sell_materials:
        user_pack_obj.minus_material(m_id,sell_materials[m_id],'pack_store_sell')
    for p_id in sell_props:
        user_pack_obj.minus_props(p_id,sell_props[p_id],'pack_store_sell')
    return 0,{'get_gold':get_gold}

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

def rename(rk_user,params):
    '''
    使用更名令进行重命名
    '''
    cost_props = params.get('cost_props')
    new_name = params.get('new_name','')
    #判断是否是更命令道具
    if not game_config.props_config.get(cost_props,{}).get('used_by','') == 'rename':
        return 11,{'msg':utils.get_msg('pack', 'wrong_used')}
    #判断用户是否有该道具
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    if not user_pack_obj.is_props_enough(cost_props,1):
        return 11,{'msg':utils.get_msg('pack', 'not_enough_props')}
    #有道具的情况进行重命名
    #减道具
    user_pack_obj.minus_props(cost_props,1,where='pack.rename')
    #更名
    user_base_obj = UserBase.get(rk_user.uid)
    user_base_obj.rename(new_name)
    return 0,{'new_name':new_name}

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
    user_property_obj.add_card_exp_point(add_exp_point)
    print user_property_obj.property_info['vip_charge_info']
    #结果返回
    return 0,{'add_exp_point':add_exp_point}

def buy_props(rk_user,params):
    '''
    购买道具的接口
    miaoyichao
    '''
    #获取道具 id 和购买的组数
    props_id = params['props_id']
    num = int(params['num'])
    #获取商店配置
    this_props_shop_config = game_config.shop_config.get('props_sale', {}).get(props_id, {})
    #获取单价
    per_price = this_props_shop_config.get('coin',0)
    #获取单组的道具数量
    unit_num = this_props_shop_config.get('unit_num',1)
    #价格不对
    if not per_price:
        return 11,{'msg':utils.get_msg('pack', 'no_props')}
    #获取购买所消耗的元宝
    all_cost = per_price * num
    all_props_num = unit_num * num
    #判断元宝是否足够
    if rk_user.user_property.minus_coin(all_cost,'buy_props'):
        #添加道具
        user_pack_obj = UserPack.get_instance(rk_user.uid)
        user_pack_obj.add_props(props_id,all_props_num,where='buy_props')
        return 0,{}
    else:
        return 11,{'msg':utils.get_msg('user','not_enough_coin')}

def get_collection(rk_user,params):
    """取得装备，药水，材料的图鉴信息
    """
    user_collect_obj = UserCollection.get_instance(rk_user.uid)
    return 0,{
              'collection':{
                  'equips':user_collect_obj.get_collected_cards('equips'),
                  'items':user_collect_obj.get_collected_cards('items'),
                  'materials':user_collect_obj.get_collected_cards('materials'),
                  'props':user_collect_obj.get_collected_cards('props'),
                }
              }
