#-*- coding: utf-8 -*-
'''
filename card.py
该文件的主要功能函数有
1 武将碎片的掉落信息
2 武将的升级  一次升一级和连续升级   升到他可达到的最大等级
3 武将的天赋进阶
4 武将的售出
5 武将的编队
'''

import copy
from apps.models.user_cards import UserCards
from apps.models.user_pack import UserPack
from apps.models.user_collection import UserCollection
from apps.common import utils
from apps.config.game_config import game_config
# from apps.models.virtual.card import Card
from apps.common.exceptions import GameLogicError


def check_card_in_deck(user_card_obj,card_list):
    """检查武将是否在队伍中
    miaoyichao
    """
    for ucid in card_list:
        for deck in user_card_obj.decks:
            ucid_ls = [card['ucid'] for card in deck if card.get('ucid','')]
            if ucid in ucid_ls:
                return 11,utils.get_msg('card','in_deck')
    return 0,''

def get_card_soul_drop_info():
    '''
    获取武将碎片掉落的关卡信息
    miaoyichao
    '''
    card_drop_info = {}
    #初始化所有的掉落
    all_cards = game_config.card_config.keys()
    #获取战场信息
    dungeon_config = game_config.normal_dungeon_config
    for floor_id in dungeon_config:
        #遍历所有的floor
        floor_info = dungeon_config[floor_id]
        for room_id in floor_info['rooms']:
            #遍历所有的room
            card_drop = floor_info['rooms'][room_id].get('drop_info',{}).get('soul',[])
            for card_id in card_drop:
                if 'card' in card_id:
                    if card_id in all_cards:
                        if card_id not in card_drop_info:
                            card_drop_info[card_id] = []
                        #遍历所有的武将碎片 然后将相关的floor和room添加进去
                        card_drop_info[card_id].append({'floor_id':floor_id,'room_id':room_id})
    #结果返回
    return card_drop_info

def card_update(rk_user, params):
    """
    通过玩家武将经验点升级武将等级 
    card_update_by_cardExpPoint
    """
    base_ucid = params['base_ucid']
    # 获取用户武将对象
    user_card_obj = UserCards.get(rk_user.uid)
    #检查武将是否存在
    if base_ucid and not user_card_obj.has_card(base_ucid):
        return 11, {'msg':utils.get_msg('card', 'no_card')}
    # 获取要强化升级的武将
    base_card = user_card_obj.get_card_info(base_ucid)
    cid = base_card['cid']
    exp_type = game_config.card_config[cid]['exp_type']
    # 武将等级不能大于用户的当前等级
    user_lv = rk_user.user_property.lv
    card_lv = base_card['lv']
    if not int(user_lv)  > int(card_lv):
        return 11, {'msg':utils.get_msg('card', 'cannot_update_now')}
    update_type = params['update_type']
    next_lv = int(card_lv) + 1
    #处理强化一次的逻辑
    need_exp = int(game_config.card_level_config['exp_type'][exp_type][str(next_lv)]) - int(base_card['exp'])
    # 判断用户升级武将的经验点是否足够
    if not rk_user.user_property.is_card_exp_point_enough(need_exp):
        return 11,{'msg':utils.get_msg('user', 'not_enough_exp_point')}
    need_gold = need_exp
    # 判断用户升级的金币是否足够
    if not rk_user.user_property.is_gold_enough(need_gold):
        return 11,{'msg':utils.get_msg('user', 'not_enough_gold')}
    if update_type == 'update':
        pass
    elif update_type == 'auto':
        #处理自动强化的逻辑
        for lv in xrange(next_lv,user_lv+1):
            #处理强化一次的逻辑
            tmp_need_exp = int(game_config.card_level_config['exp_type'][exp_type][str(lv)]) - int(base_card['exp'])
            # 判断用户升级武将的经验点是否足够
            if not rk_user.user_property.is_card_exp_point_enough(tmp_need_exp):
                break
            tmp_need_gold = tmp_need_exp
            # 判断用户升级的金币是否足够
            if not rk_user.user_property.is_gold_enough(tmp_need_gold):
                break

            need_gold = tmp_need_gold
            need_exp = tmp_need_exp
            next_lv = lv
    else:
        return 11,{'msg':utils.get_msg('card', 'params_wrong')}
    # base卡加经验
    user_card_obj.add_card_exp(base_ucid, need_exp, 'card_update')
    # 扣除经验点
    rk_user.user_property.minus_card_exp_point(need_exp, "card_update")
    #扣用户金钱
    rk_user.user_property.minus_gold(need_gold, 'card_update')
    data = {'new_card_info':{}}
    data['new_card_info']['ucid'] = base_ucid
    data['new_card_info'].update(user_card_obj.cards[base_ucid])
    data['up_lv'] = next_lv - card_lv #  升过几级 做任务用
    #判断新手引导
    newbie_step = int(params.get('newbie_step',0))
    if newbie_step:
        rk_user.user_property.set_newbie_steps(newbie_step, "card_update")

    return 0,data

def advanced_talent(rk_user,params):
    '''
    miaoyichao
    *天赋进阶
    *params : ucid = ucid
    * cost_cards = ucid,ucid,ucid.ucid
    '''
    ucid = params['ucid']
    #获取用户武将对象
    user_card_obj = UserCards.get_instance(rk_user.uid)
    #检查要天赋进阶的武将是否存在
    if not user_card_obj.has_card(ucid):
        return 11,{'msg':utils.get_msg('card','no_card')}
    #获取武将的cid
    cid = user_card_obj.cards[ucid]['cid']
    #获取武将的star
    star = str(game_config.card_config[cid].get('star',4))
    #获取武将的当前天赋等级和最大等级
    cur_talent_lv = user_card_obj.cards[ucid].get('talent_lv',0)
    max_talent_lv = int(game_config.card_config[cid]['max_talent_lv'])
    #是否已经是最大进阶等级
    if cur_talent_lv>=max_talent_lv:
        return 11,{'msg':utils.get_msg('card','max_talent_lv')}
    #取得天赋进阶的配置信息
    advanced_talent_config = game_config.talent_skill_config['advanced_talent_config']
    #获取所需要的进阶丹和card数量
    need_things = advanced_talent_config.get(star,'4').get(str(cur_talent_lv+1))
    need_card_num = need_things.get('card',0)
    if need_card_num:
        #需要消耗其他的武将
        cost_ucids = params['cost_cards'].split(',')
        cost_ucids = utils.remove_null(cost_ucids)
        #检查武将是否存在
        for cost_ucid in cost_ucids:
            #判断是否存在该武将
            if not user_card_obj.has_card(cost_ucid):
                return 11,{'msg':utils.get_msg('card','no_card')}
            #判断是否是同名卡牌
            if cid != user_card_obj.cards[cost_ucid]['cid']:
                return 11,{'msg':utils.get_msg('card','params_wrong')}
        #带装备武将不允许用于进阶
        if user_card_obj.is_equip_used(cost_ucids):
            return 11,{'msg':utils.get_msg('equip','is_used')}
        #被锁定武将不能卖出
        if user_card_obj.is_locked(cost_ucids):
            return 11,{'msg':utils.get_msg('card','locked')}
        #有天赋技能的不能用于天赋进阶
        if user_card_obj.has_talent(cost_ucids):
            return 11,{'msg':utils.get_msg('card','has_talent_card')}
        #检查武将是否在deck中
        rc,msg = check_card_in_deck(user_card_obj,cost_ucids)
        if rc:
            return rc,{'msg':msg}
        #判断消耗的武将数量是否足够
        if len(cost_ucids) < need_card_num:
            return 11,{'msg':utils.get_msg('card','not_enough_card')}
    #这里开始处理道具的逻辑
    props_config = game_config.props_config
    #判断道具是否足够
    user_pack_obj = UserPack.get_instance(rk_user.uid)
    need_props = need_things.get('props',['8_props',100])
    props_id = need_props[0]
    #检查道具的类型是否正确
    if props_config.get(props_id,{}).get('used_by','') != 'talent':
        return 11,{'msg':utils.get_msg('pack','wrong_used')}
    #检查道具是否足够
    num =  int(need_props[1])
    if not user_pack_obj.is_props_enough(props_id,num):
        return 11,{'msg':utils.get_msg('pack','not_enough_item')}
    #检查天赋进阶的金币是否足够
    cost_gold = int(need_things.get('cost_gold',10000))
    if not rk_user.user_property.is_gold_enough(cost_gold):
        return 11,{'msg':utils.get_msg('user','not_enough_gold')}
    #扣用户金钱
    rk_user.user_property.minus_gold(cost_gold,'advanced_talent')
    #删除道具
    user_pack_obj.minus_props(props_id,num,where='advanced_talent')
    #天赋进阶
    user_card_obj.advanced_talent(ucid)
    if need_card_num:
        #删除武将
        user_card_obj.del_card_info(cost_ucids,where='advanced_talent')
    data = {'new_card_info':{}}
    data['new_card_info']['ucid'] = ucid
    data['new_card_info'].update(user_card_obj.cards[ucid])
    return 0,data


def card_stove(rk_user,params):
    """
    炼化
    """
    sell_ucids = params.get('sell_ucids')
    if not sell_ucids:
        return 11,{'msg':utils.get_msg('card','no_cost_card')}
    sell_ucids = sell_ucids.split(',')
    sell_ucids = utils.remove_null(sell_ucids)
    user_card_obj = UserCards.get(rk_user.uid)
    #检查武将是否存在
    for ucid in sell_ucids:
        if ucid and not user_card_obj.has_card(ucid):
            return 11,{'msg':utils.get_msg('card','no_card')}
    #带装备武将不允许卖出
    if user_card_obj.is_equip_used(sell_ucids):
        return 11,{'msg':utils.get_msg('equip','is_used')}
    #被锁定武将不能卖出
    if user_card_obj.is_locked(sell_ucids):
        return 11,{'msg':utils.get_msg('card','locked')}
    #检查武将是否在deck中
    rc,msg = check_card_in_deck(user_card_obj,sell_ucids)
    if rc:
        return rc,{'msg':msg}
    sell_cards = [user_card_obj.get_card_info(ucid) for ucid in sell_ucids]
    return 0,{'cards_info':sell_cards,'cards_ucids':sell_ucids}
    #计算得到的铜钱,每个+增加10000铜钱
    # get_gold = 0
    # for sell_card in sell_cards:
    #     sell_card_config = game_config.card_config.get(sell_card['cid'])
    #     star = sell_card_config['star']
    #     #基础售价+总经验值*0.2 基础售价和star有关
    #     base_gold = int(game_config.card_update_config.get('sell_base_gold',{}).get(str(star),3000))
    #     exp_ratio = game_config.card_update_config.get('exp_gold_rate',0.2)
    #     #计算经验增加值和总获得的金币
    #     exp = sell_card['exp']
    #     exp_gold = int(exp*exp_ratio)
    #     get_gold += base_gold+exp_gold
    # #用户加钱
    # rk_user.user_property.add_gold(get_gold,where='sell_card')
    # #用户删卡
    # user_card_obj.del_card_info(sell_ucids,where='sell_card')
    # return 0,{'get_gold':get_gold}


def get_collection(rk_user,params):
    """取得用户的图鉴信息
    """
    return 0,{'collection':UserCollection.get_instance(rk_user.uid).get_collected_cards()}

def get_all(rk_user,params):
    """
    * 取得用户的全部武将
    * miaoyichao
    """
    data = {}
    data['user_cards'] = UserCards.get_instance(rk_user.uid).cards
    return 0,data

def set_yuanjun_decks(rk_user,params):
    """设置援军编队
    params:
        yuanjun_deck:  'ucid,ucid,ucid_ucid,,ucid'
    """
    new_deck = params['yuanjun_deck']
    # 没有援军槽时前端传的是 '____'
    if new_deck == '____':
        return 0, {}
    new_decks = new_deck.split('_')
    new_decks_lst = []
    uc = rk_user.user_cards
    if len(new_decks) != 5:
        raise GameLogicError('card','invalid_deck')
    for i, deck in enumerate(new_decks):

        ucids = deck.split(',')#[:uc.slot_num]
        if len(ucids) != uc.slot_num:
            raise GameLogicError('card','invalid_deck')
        ucid_repeat_check = []
        cid_repeat_check = []
        for ucid in ucids:
            # check :  ucid是否存在，ucid是否重复，cid是否重复
            #if ucid and ucid not in rk_user.user_cards.cards:
            #    raise GameLogicError('card', 'no_card')
            if ucid:
                if ucid not in rk_user.user_cards.cards:
                    raise GameLogicError('card', 'no_card')
                ucid_repeat_check.append(ucid)
                cid_repeat_check.append(uc.cards[ucid]['cid'])

        for item in uc.decks[i]:
            if item.get('ucid'):
                ucid_repeat_check.append(item['ucid'])
                cid_repeat_check.append(uc.cards[item['ucid']]['cid'])
        if len(ucid_repeat_check) != len(set(ucid_repeat_check)):
            raise GameLogicError('card', 'repeated_ucid')
        if len(cid_repeat_check ) != len(set(cid_repeat_check)):
            raise GameLogicError('card', 'repeated_cid')

        new_decks_lst.append(ucids)
    #print new_decks_lst, 'new_decks_lst ---------*************------------'

    uc.set_yuanjun_decks(new_decks_lst)
    
    return 0, {}

def set_decks(rk_user,params):
    """设置编队
    params:
        deck_index:当前编队编号0-9
        new_deck:  武将id:是否是主将 1是 0 否
            ucid:0,ucid:1,ucid:0,,ucid:0_ucid:0,ucid:1,ucid:0,,ucid:0
    """
    #获取参数
    #new_decks = params['new_deck']
    new_deck = params.get('new_deck')
    cur_deck_index = int(params["deck_index"])
    #判断编队是否符合要求
    if cur_deck_index < 0 or cur_deck_index > 4:
        raise GameLogicError('card','invalid_deck')
    if new_deck:
        new_decks = new_deck.split('_')
        user_card_obj = UserCards.get_instance(rk_user.uid)
    
        decks = user_card_obj.decks
        if len(decks)==5:
            new_decks_lst = [[{}] * 5] * 5
        else:
            raise GameLogicError('card','invalid_deck')
        for i, new_deck in enumerate(new_decks):
            new_new_deck = new_deck.split(',')
            #检查队伍长度是否合法
            if len(new_new_deck) == 0:
                continue
            if len(new_new_deck) < game_config.system_config['deck_length']:
                new_new_deck.extend([':0']*(game_config.system_config['deck_length'] - len(new_new_deck)))
                # return 11,{'msg':utils.get_msg('card','invalid_deck')}
            #检查这些武将是否存在
            new_deck_copy = []
            for card_info in new_new_deck:
                card_info_ls = card_info.split(':')
                if card_info_ls:
                    ucid,is_leader = card_info_ls
                else:
                    ucid = ''
                    is_leader = 0
                if ucid and not user_card_obj.has_card(ucid):
                    raise GameLogicError('card', 'no_card')
                #判断升级和强化素材不能上阵
                if ucid:
                    tmp_dict = {'ucid':ucid}
                    if int(is_leader) == 1:
                        tmp_dict['leader'] = 1
                    new_deck_copy.append(tmp_dict)
                else:
                    new_deck_copy.append({})
            #队伍中不能出现重复的ucid和重复的ueid和多个leader
            no_repeat_deck = utils.remove_null(new_deck_copy)
            ucids = [card['ucid'] for card in no_repeat_deck if card.get('ucid','')]
            leader_cnt = len([card['leader'] for card in no_repeat_deck if card.get('leader',0)])
            if len(ucids) != len(set(ucids)) or leader_cnt != 1:
                raise GameLogicError('card', 'invalid_deck')
            new_decks_lst[i] = copy.deepcopy(new_deck_copy)

        #设置最新队伍
        user_card_obj.set_decks(new_decks_lst)
        #设置当前编队索引
        user_card_obj.set_cur_deck_index(cur_deck_index)
    
    if params.get('yuanjun_deck'):
        set_yuanjun_decks(rk_user,params)
    return {}

def lock(rk_user,params):
    """
    加锁
    ucids,锁对象id
    """
    ucids = params['ucids'].split(',')
    ucids = utils.remove_null(ucids)
    user_card_obj = UserCards.get(rk_user.uid)
    for ucid in ucids:
        if not user_card_obj.has_card(ucid):
            return 11,{'msg':utils.get_msg('card','no_card')}
    user_card_obj.lock(ucids)
    return 0,{}
