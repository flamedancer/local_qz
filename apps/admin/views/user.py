#-*- coding:utf-8 -*-
import copy

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from apps.admin.decorators import require_permission
from apps.models import pvp_redis
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
    uid = request.GET.get('uid','').strip()
    if not uid:
        pid = request.GET.get('pid','').strip()
        if not pid:
            username = request.GET.get('username','')
            if not username:
                return HttpResponseRedirect('/admin/user/?status=1')
            try:
                uid=ocapp.mongo_store.mongo.db['username'].find({'name':username})[0]['uid']
            except:
                return HttpResponseRedirect('/admin/user/?status=1')
        else:
            account = AccountMapping.get(pid)
            if not account:
                return HttpResponseRedirect('/admin/user/?status=1')
            uid = account.uid


    user = UserBase.get(uid)
    if not user or not user.account:
        return HttpResponseRedirect('/admin/user/?status=1')

    user_equips_obj = UserEquips.get_instance(uid)
    user_pack_obj = UserPack.get_instance(uid)
    user_property_obj = UserProperty.get(uid)
    user_card_obj = UserCards.get(user.uid)
    game_config = game_config.set_subarea(user.subarea)

    data = {
        'user_property_obj':user_property_obj,
        'user':user,
        'deck_cards':[],
        'other_cards':[],
        'add_time':timestamp_toString(user.add_time),
        'last_login_time':timestamp_toString(user.user_property.login_time),
        'login_record':UserLogin.get(uid).login_info['login_record'],
    }
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
    for cid in all_cids:
        all_cards.append(Card.get(cid))
    data['all_cards'] = all_cards
    #用户当前战场信息
    user_dungeon_obj = UserDungeon.get_instance(user.uid)
    # #pvp
    # pvp_obj = UserPvp.getEx(user.uid)
    # top_model = pvp_redis.get_pvp_redis("1")
    # rank = top_model.rank(uid)
    # pvp_obj.rank = rank+1 if rank != None else 0
    # data['pvp'] = pvp_obj
    data['final_max_store_num'] = game_config.pack_config['max_store_num']
    data['max_card_num'] = game_config.system_config['max_card_num']
    data['now_card_num'] = user.user_property.max_card_num
    #充值信息
    data['charge_sum_money'] = user.user_property.charge_sum_money
    data['last_charge_record'] = ChargeRecord.find({'uid':uid})[-1] if ChargeRecord.find({'uid':uid}) else {}

######神秘商店   代码往前方 因为此操作会改变玩家武将，物品等信息##############
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
####################

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
                return HttpResponseRedirect('/admin/user/?status=1')
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
        #增加 经验点
        if request.POST.get('add_card_point',''):
            add_card_point = int(request.POST.get('add_card_point'))
            if add_card_point>0:
                user.user_property.add_card_exp_point(add_card_point)
            else:
                user.user_property.minus_card_exp_point(add_card_point)
        #增加经验
        if request.POST.get('add_exp',''):
            add_exp = int(request.POST.get('add_exp'))
            user.user_property.add_exp(add_exp,where='qa_add',version=float(game_config.system_config['version']))


        #发邮件
        if request.POST.get('mail_value','') or request.POST.get('mail_coin',0) or request.POST.get('mail_gold',0):
            from apps.models.user_mail import UserMail
            from apps.common import utils
            sid = 'system_%s' % (utils.create_gen_id())
            mail_value = request.POST.get('mail_value','')
            mail_coin = int(request.POST.get('mail_coin',0))
            mail_gold = int(request.POST.get('mail_gold',0))
            mailtype = 'system'
            user_mail_obj = UserMail.hget(uid, sid)
            user_mail_obj.set_mail(mailtype=mailtype,content=mail_value,award={'gold':mail_gold,'coin':mail_coin})

        #补武将
        if request.POST.get("add_card_ex", ""):
            user_card_obj = UserCards.get(user.uid)
            strCardInfo = request.POST.get("add_card_ex")
            lstCardInfo = strCardInfo.strip().split(";")
            for strAddCard in lstCardInfo:
                cid = strAddCard.split(":")[0]
                cid = cid.strip() + '_card'
                num = int(strAddCard.split(":")[1])
                for i in range(num):
                    clv = '1'
                    user_card_obj.add_card(cid,clv,where='qa_add')
        #增加武将
        if request.POST.getlist('add_card'):
            add_cids = request.POST.getlist('add_card')
            user_card_obj = UserCards.get(user.uid)
            for add_cid in add_cids:
                if add_cid in game_config.card_config:
                    clv = 1
                    user_card_obj.add_card(add_cid,clv,where='qa_add')
        #增加武将经验
        if request.POST.get('add_card_exp',''):
            add_exp = int(request.POST.get('add_card_exp'))
            ucid = request.POST.get('ucid')
            user_card_obj.add_card_exp(ucid,add_exp)
            if ucid == user_card_obj.deck[0]:
                user.user_property.set_leader_card(ucid,user_card_obj.cards[ucid])

        #增加武将技能级别
        if request.POST.get('add_card_sk_lv',''):
            ucid = request.POST.get('ucid')
            user_card_obj.add_card_sk_lv(ucid)
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
            for card in user_card_obj.deck:
                if not card:
                    card['ucid'] = ucid
                    user_card_obj.put()
                    break
        #一键扩格子
        if request.POST.get('extend_max_num',''):
            if user.user_property.max_card_num != game_config.system_config['max_card_num']:
                user.user_property.property_info['max_card_num'] = game_config.system_config['max_card_num']
                user.user_property.put()
        #一键扩仓库
        if request.POST.get('extend_store_num',''):
            user_pack_obj.max_store_num = game_config.pack_config['max_store_num']
            user_pack_obj.put()

        #一键送所有武将碎片
        if request.POST.get('give_all_card_soul',''):
            for cid in game_config.card_config:
                user_card_obj.add_card(cid,1,where='qa_add')
            user_card_obj.put()
            
        #一键送所有武将
        if request.POST.get('give_all_card',''):
            #一键送所有武将
            for cid in all_cids:
                ucid = user_card_obj.add_card(cid, 1, where='qa_add')[2]
        # if request.POST.get('give_all_card',''):
        #     user_card_obj.cards = {}
        #     user_card_obj.cards_info = {
        #                     "decks":[[{}] * 5] * 10,
        #                     "cur_deck_index":0,
        #                 }
        #     for eid in user_equips_obj.equips:
        #         if user_equips_obj.equips[eid].get("used_by"):
        #             user_equips_obj.equips[eid]['used_by'] = ''
        #     user_equips_obj.put()     
        #     card_index = 0
        #     for cid in all_cids:
        #         clv = 1
        #         ucid = user_card_obj.add_card(cid,clv,where='qa_add')[2]
        #         if card_index < 5:
        #             user_card_obj.deck[card_index]['ucid'] = ucid
        #             if card_index == 0:
        #                 user_card_obj.deck[card_index]['leader'] = 1
        #                 user.user_property.set_leader_card(ucid,user_card_obj.cards[ucid])
        #         card_index += 1

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
        #回复体力
        if request.POST.get('recover_stamina',''):
            user.user_property.recover_stamina()

        #回复pvp体力
        if request.POST.get('recover_pvp_stamina',''):
            pvp_obj.recover_pvp_stamina()

        if request.POST.get('add_pvp_exp',0):
            pvp_pt = int(request.POST.get('add_pvp_exp'))
            if pvp_pt>100000000:
                pvp_pt = 100000000
            pvp_obj.add_pt(pvp_pt)

        #equip
        if request.POST.get("add_equips", ""):
            user_equips_obj = UserEquips.get(uid)
            strEquipsInfo = request.POST.get("add_equips")
            lstEquipsInfo = strEquipsInfo.strip().split(";")
            for strAddEquip in lstEquipsInfo:
                eid = strAddEquip.split(":")[0]
                eid = eid.strip() + '_equip'
                num = int(strAddEquip.split(":")[1])
                for i in range(num):
                    user_equips_obj.add_equip(eid,where='qa_add')
        #item
        if request.POST.get("add_items", ""):
            strItemsInfo = request.POST.get("add_items")
            lstItemsInfo = strItemsInfo.strip().split(";")
            for strAddItem in lstItemsInfo:
                iid = strAddItem.split(":")[0]
                iid = iid.strip() + '_item'
                num = int(strAddItem.split(":")[1])
                user_pack_obj.add_item(iid,num,where='qa_add')
        #材料
        if request.POST.get("add_mats", ""):
            strItemsInfo = request.POST.get("add_mats")
            lstItemsInfo = strItemsInfo.strip().split(";")
            for strAddItem in lstItemsInfo:
                mid = strAddItem.split(":")[0]
                mid = mid.strip() + '_mat'
                num = int(strAddItem.split(":")[1])
                user_pack_obj.add_material(mid,num,where='qa_add')
                
        #道具
        if request.POST.get("add_props", ""):
            strPropsInfo = request.POST.get("add_props")
            lstPropsInfo = strPropsInfo.strip().split(";")
            for strAddProps in lstPropsInfo:
                pid = strAddProps.split(":")[0]
                pid = pid.strip() + '_props'
                num = int(strAddProps.split(":")[1])
                user_pack_obj.add_props(pid,num,where='qa_add')

        if request.POST.get("add_materials_sum", 0):
            mid = request.POST.get("mid")
            user_pack_obj.add_material(mid,int(request.POST.get("add_materials_sum", 0)),where='qa_add')

        if  request.POST.get("add_item_num", 0):
            iid = request.POST.get("iid")
            user_pack_obj.add_item(iid,int(request.POST.get("add_item_num", 0)),where='qa_add')

        if request.POST.get('give_all_items'):
            num = int(request.POST.get('all_item_num'))if request.POST.get('all_item_num') else 99
            for iid in game_config.item_config:
                user_pack_obj.add_item(iid,num,where='qa_add')
        if request.POST.get('del_all_items'):
            user_pack_obj.items = {}
            user_pack_obj.put()

        if  request.POST.get("add_props_num", 0):
            iid = request.POST.get("iid")
            user_pack_obj.add_props(iid,int(request.POST.get("add_props_num", 0)),where='qa_add')

        if request.POST.get('give_all_props'):
            num = int(request.POST.get('all_props_num'))if request.POST.get('all_props_num') else 99
            for iid in game_config.props_config:
                user_pack_obj.add_props(iid,num,where='qa_add')

        if request.POST.get('give_8_props'):
            num = int(request.POST.get('give_update_props'))if request.POST.get('give_update_props') else 99
            user_pack_obj.add_props('8_props',10000,where='qa_add')
        
        if request.POST.get('del_all_props'):
            user_pack_obj.props = {}
            user_pack_obj.put()


        if request.POST.get('give_all_equips'):
            user_equips = UserEquips.get(uid)
            for eid in game_config.equip_config:
                user_equips.add_equip(eid,where='qa_add')

        #一键送所有的装备碎片
        if request.POST.get('give_all_equip_soul'):
            user_souls_obj = UserSouls.get(uid)
            for eid in game_config.equip_config:
                if game_config.equip_config[eid].get('need_soul_types_num',0):
                    parts = game_config.equip_config[eid].get('need_soul_types_num',0)
                    for i in xrange(1,parts+1):
                        user_souls_obj.add_equip_soul(eid+'_'+str(i),100,where='qa_add')
                else:
                    user_souls_obj.add_equip_soul(eid,1,where='qa_add')

        #一键删除所有的装备碎片
        if request.POST.get('del_all_equip_soul'):
            user_souls_obj = UserSouls.get(uid)
            user_souls_obj.equip_souls_info = {}
            user_souls_obj.put()

        #添加单个装备碎片
        if request.POST.get('add_single_equip_soul'):
            sid = request.POST.get('sid')
            num = int(request.POST.get('add_single_equip_soul'))
            user_souls_obj = UserSouls.get_instance(uid)
            user_souls_obj.add_equip_soul(sid, num,where='qa_add')
            user_souls_obj.put()
        
        if request.POST.get('del_other_equips'):
            user_equips = UserEquips.get(uid)
            ueids = [ ueid for ueid in user_equips.equips if not user_equips.is_used(ueid)]
            user_equips.delete_equip(ueids)
        if request.POST.get('give_all_materials'):
            num = int(request.POST.get('all_materials_num'))if request.POST.get('all_materials_num') else 99
            user_pack_obj = UserPack.get_instance(uid)
            for mid in game_config.material_config:
                user_pack_obj.add_material(mid,num,where='qa_add')
        if request.POST.get('del_all_materials'):
            user_pack_obj = UserPack.get_instance(uid)
            user_pack_obj.materials = {}
            user_pack_obj.put()
        #一键过新手引导
        if request.POST.get('newbie_pass','') and user.user_property.newbie:
            newbie_steps_num = int(user.game_config.system_config.get('newbie_steps', 6))
            user.user_property.property_info['newbie_steps'] = (1 << newbie_steps_num) - 1
            user.user_property.do_put()
            user.user_property.set_newbie()

        data['status'] = 1

    data['current_dungeon'] = user_dungeon_obj.dungeon_info['normal_current']
    #配置中的所有战场
    data['all_dungeon'] = []
    floor_ids = sorted(map(lambda x:int(x),game_config.normal_dungeon_config.keys()))
    for floor_id in floor_ids:
        for room_id in sorted(game_config.normal_dungeon_config[str(floor_id)]['rooms'].keys()):
            data['all_dungeon'].append('%d-%s' % (floor_id,room_id))
    #用户已经达到最深层时
    if '%s-%s' % (data['current_dungeon']['floor_id'],data['current_dungeon']['room_id']) == data['all_dungeon'][-1]:
        data['max_dungeon'] = True
    else:
        data['max_dungeon'] = False
        now_index = data['all_dungeon'].index('%s-%s' % (data['current_dungeon']['floor_id'],data['current_dungeon']['room_id']))
        data['all_dungeon'] = data['all_dungeon'][now_index + 1:]

    #装备
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

    #props
    data['user_props'] = {pid :{'name':game_config.props_config.get(pid)['name'],'num':user_pack_obj.props[pid]} for pid in user_pack_obj.props }
    all_props_tag = sorted([int(i.split('_')[0]) for i in game_config.props_config.keys()])
    data['all_props'] = [(i,game_config.props_config.get(str(i)+'_props')) for i in all_props_tag]

######将魂系统   代码要在其他逻辑偏后 以保证是最新的信息##############
    user_souls_obj = UserSouls.get_instance(uid)
    #   添加  普通将魂
    if request.POST.get('add_normal_soul',''):
        add_normal_soul_num = int(request.POST.get('add_normal_soul'))
        sid = request.POST.get('sid')
        user_souls_obj.add_normal_soul(sid, add_normal_soul_num, where='qa_add')
    #   批量添加  普通将魂
    if request.POST.get('dump_normal_soul'):
        dump_normal_soul_str = request.POST.get('dump_normal_soul').strip()
        for item in dump_normal_soul_str.split(';'):
            sid, num = item.split(':')
            user_souls_obj.add_normal_soul(sid + '_card', int(num), where='qa_add')
    #   批量添加  装备碎片
    if request.POST.get('add_equip_soul'):
        add_equip_soul_str = request.POST.get('add_equip_soul').strip()
        for equip_info in add_equip_soul_str.split(';'):
            eid, num = equip_info.split(':')
            user_souls_obj.add_equip_soul(eid, int(num), where='qa_add')

    #   添加  英雄将魂
    if request.POST.get('add_super_soul',''):
        add_super_soul_num = int(request.POST.get('add_super_soul'))
        if add_super_soul_num >= 0:
            user_souls_obj.add_super_soul(add_super_soul_num, where='qa_add')
        else:
            user_souls_obj.minus_card_soul('super_soul', add_super_soul_num, where='qa_add')

    # 武将碎片兑换武将
    if request.POST.get('soul_exchange_card'):
        sid = request.POST.get('sid')
        params = {'cid':sid}
        user['uid'] = uid
        soul.exchange_card(user, params)
    # 删除将魂
    if request.POST.get('delete_card_soul'):
        sid = request.POST.get('sid')
        num = int(request.POST.get('num'))
        user_souls_obj = UserSouls.get_instance(uid)
        user_souls_obj.minus_card_soul(sid, num,where='qa_add')
        user_souls_obj.put()
    data.update(soul.get_all(user, None)[1])

    #武将碎片的显示
    for sid, soul_conf in data['normal_souls'].items():
        soul_conf['name'] = game_config.card_config[sid].get('star','') + u'星 ' + game_config.card_config[sid].get('name','') + u' 碎片'
    #装备碎片的显示
    for sid, soul_conf in data['equip_souls_info'].items():
        all_parts = sid.split('_')
        if len(all_parts) == 2:
            soul_conf['name'] = str(game_config.equip_config[sid].get('star','')) + u'星 ' + game_config.equip_config[sid].get('name','') + u' 碎片'
        else:
            sid = '%s_%s'%(all_parts[0],all_parts[1])
            soul_conf['name'] = str(game_config.equip_config[sid].get('star','')) + u'星 ' + game_config.equip_config[sid].get('name','') + u' 碎片第%s部分'%all_parts[2]

    #  获取玩家武将信息  代码往后放 以保证是最新的信息
    deck_num = 0
    for card in user_card_obj.deck:
        if card:
            ucid = card['ucid']
            card_info = user_card_obj.cards[ucid]
            this_card = Card.get_from_dict(card_info)
            this_card.ucid = ucid
            this_card.is_leader = card.get('leader',0)
            eid = ''#user_card_obj.get_eid(ucid)
            if eid:
                this_card.equip = game_config.equip_config[eid]['name']
            else:
                this_card.equip = ''
            this_card.now_exp = card_info['exp']
            data['deck_cards'].append(this_card)
            deck_num += 1
        else:
            data['deck_cards'].append(None)
    data['deck_num'] = deck_num
    other_ucids = user_card_obj.cards.keys()
    for card in user_card_obj.deck:
        ucid = card.get('ucid')
        if ucid and ucid in other_ucids:
            other_ucids.remove(ucid)
    for ucid in other_ucids:
        card_info = user_card_obj.cards[ucid]
        this_card = Card.get_from_dict(card_info)
        this_card.ucid = ucid
        this_card.now_exp = card_info['exp']
        eid = ''#user_card_obj.get_eid(ucid)
        if eid:
            this_card.equip = game_config.equip_config[eid]['name']
        else:
            this_card.equip = ''
        data['other_cards'].append(this_card)
    #重新整理 下编队
    user_card_obj.decks

    return render_to_response('user/edit.html',data,RequestContext(request))

def view_user(request):
    """
     更新用户信息
    """

    uid = request.GET.get('uid','').strip()
    if not uid:
        pid = request.GET.get('pid','').strip()
        if not pid:
            username = request.GET.get('username','')
            if not username:
                return HttpResponseRedirect('/admin/user/?status=1')
            try:
                uid=ocapp.mongo_store.mongo.db['username'].find({'name':username})[0]['uid']
            except:
                return HttpResponseRedirect('/admin/user/?status=1')
        else:
            account = AccountMapping.get(pid)
            if not account:
                return HttpResponseRedirect('/admin/user/?status=1')
            uid = account.uid

    user = UserBase.get(uid)
    if not user or not user.account:
        return HttpResponseRedirect('/admin/user/?status=1')

    user_card_obj = UserCards.get(user.uid)
    user_equips_obj = UserEquips.get_instance(uid)
    user_property_obj = UserProperty.get(uid)
    user_pack_obj = UserPack.get_instance(uid)

    data = {
        'user_property_obj':user_property_obj,
        'user':user,
        'deck_cards':[],
        'other_cards':[],
        'add_time':timestamp_toString(user.add_time),
        'last_login_time':timestamp_toString(user.user_property.login_time),
        'login_record':UserLogin.get(uid).login_info['login_record'],
    }
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
    for cid in all_cids:
        all_cards.append(Card.get(cid))
    data['all_cards'] = all_cards
    #用户当前战场信息
    user_dungeon_obj = UserDungeon.get_Ex(user.uid)
    pvp_obj = UserPvp.getEx(user.uid)
    #pvp 排名
    top_model = pvp_redis.get_pvp_redis('1')
    rank = top_model.rank(uid)
    pvp_obj.rank = rank+1 if rank != None else 0
    data['pvp'] = pvp_obj
    data['current_dungeon'] = user_dungeon_obj.dungeon_info['normal_current']
    #配置中的所有战场
    data['all_dungeon'] = []
    floor_ids = sorted(map(lambda x:int(x),game_config.normal_dungeon_config.keys()))
    for floor_id in floor_ids:
        for room_id in sorted(game_config.normal_dungeon_config[str(floor_id)]['rooms'].keys()):
            data['all_dungeon'].append('%d-%s' % (floor_id,room_id))
    #用户已经达到最深层时
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
            eid = ''
            if eid:
                this_card.equip = game_config.equip_config[eid]['name']
            else:
                this_card.equip = ''
            this_card.now_exp = card_info['exp']
            data['deck_cards'].append(this_card)
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
        eid = ''
        if eid:
            this_card.equip = game_config.equip_config[eid]['name']
        else:
            this_card.equip = ''
        data['other_cards'].append(this_card)
    #重新整理 下编队
    user_card_obj.decks

    #装备
    equips = user_equips_obj.equips
    eqids_dict = [user_equips_obj.get_equip_dict(ueid) for ueid in equips ]
    data['user_equips'] = [game_config.equip_config[eid_dict['eid']]  for eid_dict in eqids_dict]
    all_equips_tag = sorted([int(i.split('_')[0]) for i in game_config.equip_config.keys()])
    data['all_equips'] = [(i,game_config.equip_config[str(i)+'_equip']) for i in all_equips_tag]
    #item
    data['user_items'] = { iid:{'name':game_config.item_config[iid]['name'],'num':user_pack_obj.items[iid] } for iid in user_pack_obj.items }
    all_item_tag = sorted([int(i.split('_')[0]) for i in game_config.item_config.keys()])
    data['all_items'] = [(i,game_config.item_config.get(str(i)+'_item')) for i in all_item_tag]
    #mat
    data['user_materials'] = {mid :{'name':game_config.material_config[mid]['name'],'num':user_pack_obj.materials[mid]} for mid in user_pack_obj.materials }
    all_materials_tag = sorted([int(i.split('_')[0]) for i in game_config.material_config.keys()])
    data['all_materials'] = [(i,game_config.material_config[str(i)+'_mat']) for i in all_materials_tag]
    #
    data['charge_sum_money'] = user.user_property.charge_sum_money
    data['last_charge_record'] = ChargeRecord.find({'uid':uid})[-1] if ChargeRecord.find({'uid':uid}) else {}


######将魂系统##############

    data.update(soul.get_all(user, None)[1])
    for sid, soul_conf in data['normal_souls'].items():
        soul_conf['name'] = game_config.card_config[sid].get('star','') + u'星 ' + game_config.card_config[sid].get('name','') + u' 将魂'

    return render_to_response('user/view.html',data,RequestContext(request))
