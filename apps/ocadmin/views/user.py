#-*- coding:utf-8 -*-

import traceback
from apps.oclib.utils import rkjson as json
from apps.ocadmin.views import process_response
import copy
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from apps.ocadmin.decorators import require_permission
#from apps.models import pvp_redis
from apps.models.user_base import UserBase
from apps.models.user_property import UserProperty
from apps.models.user_cards import UserCards
from apps.models.user_dungeon import UserDungeon
from apps.models.virtual.card import Card
from apps.config.game_config import game_config
from apps.models.user_equips import UserEquips
from apps.models.user_pack import UserPack
from apps.models.user_pvp import UserPvp
from apps.models.user_login import UserLogin
from apps.common.utils import timestamp_toString
from apps.oclib import app as ocapp
from apps.models.user_souls import UserSouls
from apps.logics import soul
from apps.logics import mystery_store
from apps.models.account_mapping import AccountMapping
from django.http import HttpResponse

from apps.models import data_log_mod
ChargeRecord = data_log_mod.get_log_model("ChargeRecord")


def index(request):
    """
     用户管理导航页
    """
    status = request.GET.get("status")
    user_type = request.GET.get("user_type",'')
    return render_to_response('user/index.html',{"status":status,"user_type":user_type},RequestContext(request))

@require_permission
def edit_user(request):
    """
    编辑用户页
    """
    data = {
        'rc' : 0,
    }
    try:
        uid = request.REQUEST.get('uid','').strip()
        if not uid:
            pid = request.GET.get('pid','').strip()
            if not pid:
                username = request.GET.get('username','')
                if not username:
                    data['rc']  = 1
                    data['msg'] = u'不存在该用户'
                    return process_response(HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    ))
                try:
                    uid=ocapp.mongo_store.mongo.db['username'].find({'name':username})[0]['uid']
                except:
                    data['rc']  = 2
                    data['msg'] = u'异常'
                    return process_response(HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    ))
            else:
                account = AccountMapping.get(pid)
                if not account:
                    data['rc']  = 3
                    data['msg'] = u'不存在该账号'
                    return process_response(HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    ))
                uid = account.uid

        user = UserBase.get(uid)
        if not user or not user.account:
            data['rc']  = 4
            data['msg'] = u'不存在该账号'
            return process_response(HttpResponse(
                json.dumps(data, indent=1),
                content_type='application/x-javascript',
            ))

        user_equips_obj = UserEquips.get_instance(uid)
        user_pack_obj = UserPack.get_instance(uid)
        user_property_obj = UserProperty.get(uid)
        user_property_dict = {}
        if user_property_obj:
            user_property_dict['mobile_num'] = user_property_obj.mobile_num
            user_property_dict['lv'] = user_property_obj.lv
            user_property_dict['exp'] = user_property_obj.exp
            user_property_dict['gold'] = user_property_obj.gold
            user_property_dict['coin'] = user_property_obj.coin
            user_property_dict['stamina'] = user_property_obj.stamina
            user_property_dict['max_stamina'] = user_property_obj.max_stamina
            user_property_dict['newbie'] = user_property_obj.newbie

        user_dict = {}
        user_dict['uid'] = user.uid
        user_dict['username'] = user.username
        user_dict['baseinfo'] = user.baseinfo
        user_dict['platform'] = user.platform
        user_dict['in_frozen'] = user.in_frozen
        user_card_obj = UserCards.get(user.uid)

        data.update({
            'user_property_obj':user_property_dict,
            'user':user_dict,
            'deck_cards':[],
            'other_cards':[],
            'add_time':timestamp_toString(user.add_time),
            'last_login_time':timestamp_toString(user.user_property.login_time),
            'login_record':UserLogin.get(uid).login_info['login_record'],
        })
        if not user.client_type:
            data['client_type'] = 'appstore_ios'
        else:
            data['client_type'] = user.client_type
        all_cards = []

        all_cids = game_config.card_config.keys()

        all_cids_cp = copy.deepcopy(game_config.card_config)
        for k,v in all_cids_cp.iteritems():
            all_cids_cp[k]['no'] = int(k.split('_')[0])
     
        all_cids.sort(key = lambda x :(all_cids_cp[x]['no']))
        card_config = game_config.card_config
        for cid in all_cids:
            all_cards.append({
                'cid': cid,
                'name': card_config[cid]['name'],
            })
        data['all_cards'] = all_cards
        #用户当前战场信息
        user_dungeon_obj = UserDungeon.get_instance(user.uid)
        #pvp
        pvp_obj = UserPvp.getEx(user.uid)
        data['pvp'] = {}
        data['pvp']['pvp_info'] = pvp_obj.pvp_info
        data['pvp']['pvp_stamina'] = pvp_obj.pvp_stamina
        data['pvp']['max_pvp_stamina'] = pvp_obj.max_pvp_stamina
        data['max_card_num'] = game_config.system_config['max_card_num']
        data['now_card_num'] = user.user_property.max_card_num
#        #充值信息
        data['charge_sum_money'] = user.user_property.charge_sum_money
        data['last_charge_record'] = {}
        ChargeRecord_obj = ChargeRecord.find({'uid':uid})[-1] if ChargeRecord.find({'uid':uid}) else {}
        if ChargeRecord_obj:
            data['last_charge_record']['price'] = ChargeRecord_obj.price
            data['last_charge_record']['createtime']  = ChargeRecord_obj.createtime

######神秘商店#       代码往前方 因为此操作会改变玩家武将，物品等信息##############
        #   刷新  物品列表
        if request.POST.get('refresh_store_by_self',''):
            store_type = request.POST.get('store_type')
            params = {
                'store_type': store_type,
            }
            mystery_store.refresh_store_by_self(user, params)
        #   购买  物品
        if request.POST.get('buy_store_goods',''):
            store_type = request.POST.get('store_type')
            goods_index = int(request.POST.get('goods_index'))
            params = {
                'store_type': store_type,
                'goods_index': goods_index,
            }
            mystery_store.buy_store_goods(user, params)
        data.update({'mystery_store': mystery_store.get_store_info(user, {})[1]})
        #提交状态
        if request.method == "POST":
            state = int(request.POST.get("state","0"))
            state = bool(state)
            #冻结
            if state != user.in_frozen:
                if state:
                    user.froze()
                #解冻
                else:
                    user.unfroze()

            #删除账号
            if request.POST.get('del_user',''):
                if not user.account:
                    data['rc']  = 5
                    data['msg'] = u'不存在该用户'
                    return process_response(HttpResponse(
                        json.dumps(data, indent=1),
                        content_type='application/x-javascript',
                    ))
                user.account.delete()
            if request.POST.get('add_gold',''):
                add_gold = int(request.POST.get('add_gold'))
                if add_gold>0:
                    user.user_property.add_gold(add_gold,where='qa_add')
                else:
                    user.user_property.minus_gold(add_gold)
            #增加元宝
            if request.POST.get('add_coin',''):
                add_coin = int(request.POST.get('add_coin'))
                if add_coin>0:
                    user.user_property.add_coin(add_coin,where='qa_add')
                else:
                    user.user_property.minus_coin(add_coin)
            #增加经验
            if request.POST.get('add_exp',''):
                add_exp = int(request.POST.get('add_exp'))
                user.user_property.add_exp(add_exp,where='qa_add')

            #补武将
            if request.POST.get("add_card_ex", ""):
                user_card_obj = UserCards.get(user.uid)
                strCardInfo = request.POST.get("add_card_ex")
                lstCardInfo = strCardInfo.strip().split(",")
                for strAddCard in lstCardInfo:
                    cid = strAddCard.split(":")[0]
                    cid = cid.strip() + '_card'
                    num = int(strAddCard.split(":")[1])
                    for i in range(num):
                        clv = min(6,Card.get(cid).max_lv)
                        user_card_obj.add_card(cid,clv,where='qa_add')
            #增加武将
            if request.POST.getlist('add_card'):
                add_cids = request.POST.get('add_card')
                user_card_obj = UserCards.get(user.uid)
                add_cids_list = add_cids.split(',')
                for add_cid in add_cids_list:
                    if add_cid in game_config.card_config:
                        clv = min(6,Card.get(add_cid).max_lv)
                        user_card_obj.add_card(add_cid,clv,where='qa_add')
            #增加武将经验
            if request.POST.get('add_card_exp',''):
                add_exp = int(request.POST.get('add_card_exp'))
                ucid = request.POST.get('ucid')
                user_card_obj.add_card_exp(ucid,add_exp)
                if ucid == user_card_obj.deck[0]:
                    user.user_property.set_leader_card(ucid,user_card_obj.cards[ucid])
            #卖掉卡片
            if request.POST.get('sell_card',''):
                ucid = request.POST.get('ucid')
                this_card = Card.get(user_card_obj.cards[ucid]['cid'],user_card_obj.cards[ucid]['lv'])
                user_card_obj.del_card_info([ucid])
                user.user_property.add_gold(this_card.sell_gold,where='sell_card')
            #踢出队伍
            if request.POST.get('kick_deck',''):
                kick_index = int(request.POST.get('deck_index'))
                if user_card_obj.deck[kick_index].get('ucid','') != user_card_obj.get_leader(user_card_obj.cur_deck_index):
                    user_card_obj.deck[kick_index] = {}
                    user_card_obj.put()
            #设置主将
            if request.POST.get('set_deck_main',''):
                ucid = request.POST.get('ucid')
                find_fg = False
                if ucid:
                    for card in user_card_obj.deck:
                        if card.get('leader',0):
                            card['ucid'] = ucid
                            user_card_obj.put()
                            find_fg = True
                            break
                    if not find_fg:
                        user_card_obj.deck[0] = {'ucid':ucid,'leader':1}
                        user_card_obj.put()
                    user.user_property.set_leader_card(ucid,user_card_obj.cards[ucid])

            #设置副将
            if request.POST.get('set_deck_sub',''):
                ucid = request.POST.get('ucid')
                if ucid:
                    for card in user_card_obj.deck:
                        if not card:
                            card['ucid'] = ucid
                            user_card_obj.put()
                            break
            #一键送所有武将
            if request.POST.get('give_all_card',''):
                user_card_obj.cards = {}
                user_card_obj.cards_info = {
                                "decks":[[{},{},{},{},{}],[{},{},{},{},{}],
                                    [{},{},{},{},{}],[{},{},{},{},{}],[{},{},{},{},{}]],
                                "cur_deck_index":0,
                            }
                for eid in user_equips_obj.equips:
                    if user_equips_obj.equips[eid].get("used_by"):
                        user_equips_obj.equips[eid]['used_by'] = ''
                user_equips_obj.put()     
                card_index = 0
                for cid in all_cids:
                    clv = min(6,Card.get(cid).max_lv)
                    ucid = user_card_obj.add_card(cid,clv,where='qa_add')[2]
                    if card_index < 5:
                        user_card_obj.deck[card_index]['ucid'] = ucid
                        if card_index == 0:
                            user_card_obj.deck[card_index]['leader'] = 1
                            user.user_property.set_leader_card(ucid,user_card_obj.cards[ucid])
                    card_index += 1

            #一键删除军队外的所有武将
            if request.POST.get('del_other_card',''):
                decks = []
                for deck in user_card_obj.decks:
                    decks.extend([card['ucid'] for card in deck if card.get('ucid','')])
                del_cids = filter(lambda x:x not in decks,user_card_obj.cards.keys())
                user_card_obj.del_card_info(del_cids)
                for eid in user_equips_obj.equips:
                    if user_equips_obj.equips[eid].get("used_by"):
                        user_equips_obj.equips[eid]['used_by'] = ''
                user_equips_obj.put()
            #开放战场
            if request.POST.get('open_dungeon',''):
                open_dungeon = request.POST.get('open_dungeon')
                floor_id = open_dungeon.split('-')[0]
                room_id = open_dungeon.split('-')[1]
                user_dungeon_obj.dungeon_info['normal_current']['floor_id'] = floor_id
                user_dungeon_obj.dungeon_info['normal_current']['room_id'] = room_id
                user_dungeon_obj.dungeon_info['normal_current']['status'] = 0
                user_dungeon_obj.put()

            if request.POST.get('add_pvp_exp',0):
                pvp_pt = int(request.POST.get('add_pvp_exp'))
                if pvp_pt>100000000:
                    pvp_pt = 100000000
                pvp_obj.add_pt(pvp_pt)

            #equip
            if request.POST.get("add_equips", ""):
                user_equips_obj = UserEquips.get(uid)
                strEquipsInfo = request.POST.get("add_equips")
                lstEquipsInfo = strEquipsInfo.strip().split(",")
                for strAddEquip in lstEquipsInfo:
                    eid = strAddEquip.split(":")[0]
                    eid = eid.strip() + '_equip'
                    num = int(strAddEquip.split(":")[1])
                    for i in range(num):
                        user_equips_obj.add_equip(eid,where='qa_add')
#            #item
            if request.POST.get("add_items", ""):
                strItemsInfo = request.POST.get("add_items")
                lstItemsInfo = strItemsInfo.strip().split(",")
                for strAddItem in lstItemsInfo:
                    iid = strAddItem.split(":")[0]
                    iid = iid.strip() + '_item'
                    num = int(strAddItem.split(":")[1])
                    user_pack_obj.add_item(iid,num,where='qa_add')
            #材料
            if request.POST.get("add_mats", ""):
                strItemsInfo = request.POST.get("add_mats")
                lstItemsInfo = strItemsInfo.strip().split(",")
                for strAddItem in lstItemsInfo:
                    mid = strAddItem.split(":")[0]
                    mid = mid.strip() + '_mat'
                    num = int(strAddItem.split(":")[1])
                    user_pack_obj.add_material(mid,num,where='qa_add')

            if request.POST.get("add_materials_sum", 0):
                mid = request.POST.get("mid")
                user_pack_obj.add_material(mid,int(request.POST.get("add_materials_sum", 0)),where='qa_add')

            if  request.POST.get("add_item_num", 0):
                iid = request.POST.get("iid")
                user_pack_obj.add_item(iid,int(request.POST.get("add_item_num", 0)),where='qa_add')

            if request.POST.get('give_all_items'):
                num = request.POST.get('all_item_num', 99)
                if not num:
                    num = 99
                num = int(num)
                for iid in game_config.item_config:
                    user_pack_obj.add_item(iid,num,where='qa_add')
            if request.POST.get('del_all_items'):
                user_pack_obj.items = {}
                user_pack_obj.put()
            if request.POST.get('give_all_equips'):
                user_equips = UserEquips.get(uid)
                for eid in game_config.equip_config:
                    user_equips.add_equip(eid,where='qa_add')
            if request.POST.get('del_other_equips'):
                user_equips = UserEquips.get(uid)
                ueids = [ ueid for ueid in user_equips.equips if not user_equips.is_used(ueid)]
                user_equips.delete_equip(ueids)
            if request.POST.get('give_all_materials'):
                num = request.POST.get('all_materials_num', 99)
                if not num:
                    num = 99
                num = int(num)
                user_pack_obj = UserPack.get_instance(uid)
                for mid in game_config.material_config:
                    user_pack_obj.add_material(mid,num,where='qa_add')
            if request.POST.get('del_all_materials'):
                user_pack_obj = UserPack.get_instance(uid)
                user_pack_obj.materials = {}
                user_pack_obj.put()
#            #一键过新手引导
#            if request.POST.get('newbie_pass','') and user.user_property.newbie:
#                if user.user_property.country:
#                    country = user.user_property.country
#                else:
#                    country = 1
#                user.user_property.set_country(str(country))
#                user_card_obj.init_cards(str(country))
#                user.user_property.update_tutorial_step(10)
#                #把主将设置为最高级
#                leader_card_info = user_card_obj.cards[user_card_obj.leader_ucid]
#                leader_card_info['lv'] = Card.get(leader_card_info['cid']).max_lv
#                user_card_obj.put()
#            data['status'] = 1

        data['current_dungeon'] = user_dungeon_obj.dungeon_info['normal_current']
        #配置中的所有战场
        data['all_dungeon'] = []
        floor_ids = sorted(map(lambda x:int(x),game_config.dungeon_config.keys()))
        for floor_id in floor_ids:
            for room_id in sorted(game_config.dungeon_config[str(floor_id)]['rooms'].keys()):
                data['all_dungeon'].append('%d-%s' % (floor_id,room_id))
#        #用户已经达到最深层时
        if '%s-%s' % (data['current_dungeon']['floor_id'],data['current_dungeon']['room_id']) == data['all_dungeon'][-1]:
            data['max_dungeon'] = True
        else:
            data['max_dungeon'] = False
            now_index = data['all_dungeon'].index('%s-%s' % (data['current_dungeon']['floor_id'],data['current_dungeon']['room_id']))
            data['all_dungeon'] = data['all_dungeon'][now_index + 1:]

#        #装备
        equips = user_equips_obj.equips
        eqids_dict = [user_equips_obj.get_equip_dict(ueid) for ueid in equips ]
        data['user_equips'] = [game_config.equip_config.get(eid_dict['eid'])  for eid_dict in eqids_dict]
        all_equips_tag = sorted([int(i.split('_')[0]) for i in game_config.equip_config.keys()])
        data['all_equips'] = [(i,game_config.equip_config.get(str(i)+'_equip')) for i in all_equips_tag]
        #item
        data['user_items'] = { iid:{'name':game_config.item_config.get(iid)['name'],'num':user_pack_obj.items[iid] } for iid in user_pack_obj.items }
        all_item_tag = sorted([int(i.split('_')[0]) for i in game_config.item_config.keys()])
        data['all_items'] = [(i,game_config.item_config.get(str(i)+'_item')) for i in all_item_tag]
        #mat
        data['user_materials'] = {mid :{'name':game_config.material_config.get(mid)['name'],'num':user_pack_obj.materials[mid]} for mid in user_pack_obj.materials }
        all_materials_tag = sorted([int(i.split('_')[0]) for i in game_config.material_config.keys()])
        data['all_materials'] = [(i,game_config.material_config.get(str(i)+'_mat')) for i in all_materials_tag]

# #####将魂系统#       代码要在其他逻辑偏后 以保证是最新的信息##############
#         user_souls_obj = UserSouls.get_instance(uid)
#         #   添加  普通将魂
#         if request.POST.get('add_normal_soul',''):
#             add_normal_soul_num = int(request.POST.get('add_normal_soul'))
#             sid = request.POST.get('sid')
#             user_souls_obj.add_normal_soul(sid, add_normal_soul_num, where='qa_add')
#         #   批量添加  普通将魂
#         if request.POST.get('dump_normal_soul'):
#             dump_normal_soul_str = request.POST.get('dump_normal_soul').strip()
#             for item in dump_normal_soul_str.split(','):
#                 sid, num = item.split(':')
#                 user_souls_obj.add_normal_soul(sid + '_card', int(num), where='qa_add')

#         #   添加  英雄将魂
#         if request.POST.get('add_super_soul',''):
#             add_super_soul_num = int(request.POST.get('add_super_soul'))
#             if add_super_soul_num >= 0:
#                 user_souls_obj.add_super_soul(add_super_soul_num, where='qa_add')
#             else:
#                 user_souls_obj.minus_card_soul('super_soul', add_super_soul_num, where='qa_add')
#         # 将魂兑换武将
#         if request.POST.get('prior_type'):
#             sid = request.POST.get('sid')
#             prior_type = request.POST.get('prior_type')
#             params = {
#                 'cid': sid,
#                 'prior_type': prior_type,
#             }
#             soul.exchange_card(user, params)
#         # 释放将魂
#         if request.POST.get('tranform_normal_to_super'):
#             sid = request.POST.get('sid')
#             num = request.POST.get('num')
#             params = {
#                 'cid': sid,
#                 'num': num,
#             }
#             soul.tranform_normal_to_super(user, params)
#         data.update(soul.get_all(user, None)[1])
#         for sid, soul_conf in data['normal_souls'].items():
#             soul_conf['name'] = game_config.card_config[sid].get('star','') + u'星 ' + game_config.card_config[sid].get('name','') + u' 将魂'

#         data['super_souls_num'] = user_souls_obj.super_souls_num

#      获取玩家武将信息  代码往后放 以保证是最新的信息
        deck_num = 0
        for card in user_card_obj.deck:
            if card:
                this_card_dict = {}
                ucid = card['ucid']
                card_info = user_card_obj.cards[ucid]
                this_card = Card.get_from_dict(card_info)
                this_card.ucid = ucid
                this_card.is_leader = card.get('leader',0)
                eid = user_card_obj.get_eid(ucid)
                if eid:
                    this_card.equip = game_config.equip_config[eid]['name']
                else:
                    this_card.equip = ''
                this_card.now_exp = card_info['exp']
                this_card_dict['is_leader'] = this_card.is_leader
                this_card_dict['skid'] = this_card.skid
                this_card_dict['sk_lv'] = this_card.sk_lv
                this_card_dict['max_sk_lv'] = this_card.max_sk_lv
                this_card_dict['ucid'] = this_card.ucid
                this_card_dict['attack'] = this_card.attack
                this_card_dict['recover'] = this_card.recover
                this_card_dict['hp'] = this_card.hp
                this_card_dict['defense'] = this_card.defense
                this_card_dict['equip'] = this_card.equip

                this_card_dict['name'] = this_card.name
                this_card_dict['star'] = this_card.star
                this_card_dict['now_exp'] = this_card.now_exp
                this_card_dict['lv'] = this_card.lv
                this_card_dict['max_lv'] = this_card.max_lv
                data['deck_cards'].append(this_card_dict)
                deck_num += 1
            else:
                data['deck_cards'].append(None)
        data['deck_num'] = deck_num
        other_ucids = user_card_obj.cards.keys()
        for card in user_card_obj.deck:
            ucid = card.get('ucid')
            if ucid:
                other_ucids.remove(ucid)

        for ucid in other_ucids:
            card_info = user_card_obj.cards[ucid]
            this_card_dict = {}
            this_card = Card.get_from_dict(card_info)
            this_card.ucid = ucid
            this_card.now_exp = card_info['exp']
            eid = user_card_obj.get_eid(ucid)
            if eid:
                this_card.equip = game_config.equip_config[eid]['name']
            else:
                this_card.equip = ''
            this_card_dict['ucid'] = this_card.ucid
            this_card_dict['name'] = this_card.name
            this_card_dict['star'] = this_card.star
            this_card_dict['lv'] = this_card.lv
            this_card_dict['now_exp'] = this_card.now_exp
            this_card_dict['max_lv'] = this_card.max_lv
            this_card_dict['skid'] = this_card.skid
            this_card_dict['sk_lv'] = this_card.sk_lv
            this_card_dict['max_sk_lv'] = this_card.max_sk_lv
            this_card_dict['attack'] = this_card.attack
            this_card_dict['recover'] = this_card.recover
            this_card_dict['defense'] = this_card.defense
            this_card_dict['hp'] = this_card.hp
            this_card_dict['equip'] = this_card.equip

            data['other_cards'].append(this_card_dict)
        #重新整理 下编队
        user_card_obj.decks

    except:
        data['rc'] = 1
        data['msg'] = traceback.format_exc()
        print traceback.format_exc()

    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))

@require_permission
def view_user(request):
    """
     更新用户信息
    """
    data = {
        'rc' : 0,
    }
   
    uid = request.REQUEST.get('uid','').strip()
    if not uid:
        pid = request.GET.get('pid','').strip()
        if not pid:
            username = request.GET.get('username','')
            if not username:
                data['rc']  = 1
                data['msg'] = u'不存在该用户'  
                return process_response(HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                ))
            try:
                uid=ocapp.mongo_store.mongo.db['username'].find({'name':username})[0]['uid']
            except:
                data['rc']  = 2
                data['msg'] = u'异常'
                return process_response(HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                ))
        else:
            account = AccountMapping.get(pid)
            if not account:
                data['rc']  = 3
                data['msg'] = u'不存在该账号'
                return process_response(HttpResponse(
                    json.dumps(data, indent=1),
                    content_type='application/x-javascript',
                ))
            uid = account.uid

    user = UserBase.get(uid)
    user_dict = {}
    user_dict['uid'] = user.uid
    user_dict['username'] = user.username
    user_dict['baseinfo'] = user.baseinfo
    user_dict['platform'] = user.platform
    user_dict['in_frozen'] = user.in_frozen
    user_dict['frozen'] = user.frozen


    if not user or not user.account:
        data['rc']  = 4
        data['msg'] = u'不存在该账号'
        return process_response(HttpResponse(
            json.dumps(data, indent=1),
            content_type='application/x-javascript',
        ))
    user_card_obj = UserCards.get(user.uid)
    user_equips_obj = UserEquips.get_instance(uid)
    user_pack_obj = user.user_pack
    user_property_obj = UserProperty.get(uid)

    data.update({
        'user_property_obj':user_property_obj.user_property,
        'user':user_dict,
        'deck_cards':[],
        'other_cards':[],
        'add_time':timestamp_toString(user.add_time),
        'last_login_time':timestamp_toString(user.user_property.login_time),
        'login_record':UserLogin.get(uid).login_info['login_record'],
    })
    if not user.client_type:
        data['client_type'] = 'appstore_ios'
    else:
        data['client_type'] = user.client_type
    #用户当前战场信息
    user_dungeon_obj = UserDungeon.get_Ex(user.uid)
    pvp_obj = UserPvp.getEx(user.uid)
#    #pvp 排名
    data['pvp'] = {}
    data['pvp']['pvp_info'] = pvp_obj.pvp_info
    data['pvp']['rank'] = pvp_obj.pvp_rank()
    data['pvp']['pvp_stamina'] = pvp_obj.pvp_stamina
    data['current_dungeon'] = user_dungeon_obj.dungeon_info['normal_current']
    #配置中的所有战场
    data['all_dungeon'] = []
    floor_ids = sorted(map(lambda x:int(x),game_config.dungeon_config.keys()))
    for floor_id in floor_ids:
        for room_id in sorted(game_config.dungeon_config[str(floor_id)]['rooms'].keys()):
            data['all_dungeon'].append('%d-%s' % (floor_id,room_id))
#    #用户已经达到最深层时
    if '%s-%s' % (data['current_dungeon']['floor_id'],data['current_dungeon']['room_id']) == data['all_dungeon'][-1]:
        data['max_dungeon'] = True
    else:
        data['max_dungeon'] = False
        now_index = data['all_dungeon'].index('%s-%s' % (data['current_dungeon']['floor_id'],data['current_dungeon']['room_id']))
        data['all_dungeon'] = data['all_dungeon'][now_index + 1:]

    deck_num = 0
    for card in user_card_obj.deck:
        if card:
            ucid = card['ucid']
            card_info = user_card_obj.cards[ucid]
            this_card = Card.get_from_dict(card_info)
            this_card.ucid = ucid
            this_card.is_leader = card.get('leader',0)
            eid = user_card_obj.get_eid(ucid)
            if eid:
                this_card.equip = game_config.equip_config[eid]['name']
            else:
                this_card.equip = ''
            this_card.now_exp = card_info['exp']
            this_card_dict = {}
            this_card_dict['is_leader'] = this_card.is_leader
            this_card_dict['name'] = this_card.name
            this_card_dict['star'] = this_card.star
            this_card_dict['lv'] = this_card.lv
            this_card_dict['now_exp'] = this_card.now_exp
            this_card_dict['skid'] = this_card.skid
            this_card_dict['sk_lv'] = this_card.sk_lv
            this_card_dict['attack'] = this_card.attack
            this_card_dict['recover'] = this_card.recover
            this_card_dict['hp'] = this_card.hp
            this_card_dict['defense'] = this_card.defense
            this_card_dict['equip'] = this_card.equip
            data['deck_cards'].append(this_card_dict)
            deck_num += 1
        else:
            data['deck_cards'].append(None)
    data['now_card_num'] = user.user_property.max_card_num
    data['deck_num'] = deck_num
    other_ucids = user_card_obj.cards.keys()
    for card in user_card_obj.deck:
        ucid = card.get('ucid')
        if ucid:
            other_ucids.remove(ucid)
    for ucid in other_ucids:
        card_info = user_card_obj.cards[ucid]
        this_card = Card.get_from_dict(card_info)
        this_card.ucid = ucid
        this_card.now_exp = card_info['exp']
        eid = user_card_obj.get_eid(ucid)
        if eid:
            this_card.equip = game_config.equip_config[eid]['name']
        else:
            this_card.equip = ''
        this_card_dict = {}
        this_card_dict['name'] = this_card.name
        this_card_dict['star'] = this_card.star
        this_card_dict['lv'] = this_card.lv
        this_card_dict['now_exp'] = this_card.now_exp
        this_card_dict['skid'] = this_card.skid
        this_card_dict['sk_lv'] = this_card.sk_lv
        this_card_dict['attack'] = this_card.attack
        this_card_dict['recover'] = this_card.recover
        this_card_dict['defense'] = this_card.defense
        this_card_dict['hp'] = this_card.hp
        data['other_cards'].append(this_card_dict)

    #重新整理 下编队
    user_card_obj.decks

    #装备
    equips = user_equips_obj.equips
    eqids_dict = [user_equips_obj.get_equip_dict(ueid) for ueid in equips ]
    data['user_equips'] = [game_config.equip_config[eid_dict['eid']]  for eid_dict in eqids_dict]
    all_equips_tag = sorted([int(i.split('_')[0]) for i in game_config.equip_config.keys()])
    data['all_equips'] = [(i,game_config.equip_config[str(i)+'_equip']) for i in all_equips_tag]
    #item
    data['user_items'] = { iid:{'name':game_config.item_config[iid]['name'],'num':user_pack_obj.items[iid] } for iid in user_pack_obj.get_items() }
    all_item_tag = sorted([int(i.split('_')[0]) for i in game_config.item_config.keys()])
    data['all_items'] = [(i,game_config.item_config.get(str(i)+'_item')) for i in all_item_tag]
    #mat
    data['user_materials'] = {mid :{'name':game_config.material_config[mid]['name'],'num':user_pack_obj.materials[mid]} for mid in user_pack_obj.get_materials() }
    all_materials_tag = sorted([int(i.split('_')[0]) for i in game_config.material_config.keys()])
    data['all_materials'] = [(i,game_config.material_config[str(i)+'_mat']) for i in all_materials_tag]

    data['charge_sum_money'] = user.user_property.charge_sum_money
    data['last_charge_record'] = {}
    ChargeRecord_obj = ChargeRecord.find({'uid':uid})[-1] if ChargeRecord.find({'uid':uid}) else {}
    if ChargeRecord_obj:
        data['last_charge_record']['price'] = ChargeRecord_obj.price
        data['last_charge_record']['createtime']  = ChargeRecord_obj.createtime
    #将魂系统
    data.update(soul.get_all(user, None)[1])
    for sid, soul_conf in data['normal_souls'].items():
        soul_conf['name'] = game_config.card_config[sid].get('star','') + u'星 ' + game_config.card_config[sid].get('name','') + u' 将魂'
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))
