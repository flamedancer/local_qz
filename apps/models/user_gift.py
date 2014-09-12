#!/usr/bin/env python
# encoding: utf-8

import time
import datetime
import copy
import bisect
from apps.models.user_property import UserProperty
from apps.common import utils
from apps.common.utils import datetime_toString
from apps.models import GameModel
from apps.models.user_equips import UserEquips
from apps.models.user_cards import UserCards
from apps.models.user_souls import UserSouls
from apps.models.user_pack import UserPack
import traceback

class UserGift(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid','gift_list','today','gift_code_type','gift_code_info', 'has_got_lv_gift', 'has_got_gift_code']

    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        self.uid = None
        self.gift_list = {}
        self.gift_code_type = []
        self.today = ''
        self.gift_code_info = {}
        self.has_got_lv_gift = []   # 精确记录已经领取的等级奖励，eg.  ['1', '10',..]
        self.has_got_gift_code = {}

    @classmethod
    def get_instance(cls,uid):
        obj = super(UserGift,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def get(cls,uid):
        obj = super(UserGift,cls).get(uid)
        if obj:
            obj.refresh_info()
        return obj

    @classmethod
    def _install(cls,uid):
        obj = cls.create(uid)
        obj.put()
        return obj

    @classmethod
    def create(cls,uid):
        user_gift_obj = UserGift()
        user_gift_obj.uid = uid
        user_gift_obj.gift_list = {}
        user_gift_obj.today = utils.get_today_str()
        user_gift_obj.gift_code_type = []
        user_gift_obj.gift_code_info = {
                                     'lv_up':{},
                                    }
        user_gift_obj.has_got_gift_code = {}
        return user_gift_obj

    def refresh_info(self):
        """
        要刷新数据,过期数据清除
        """
        today = utils.get_today_str()
        if today != self.today:
            self.today = today
            gift_list = self.gift_list
            gift_list_copy = copy.deepcopy(gift_list)
            now = datetime.datetime.now()
            for _index in gift_list_copy:
                upd_time = gift_list[_index]['upd_time']
                has_got = gift_list_copy[_index].get('has_got',0)
                #奖励已经领过，并且过期7天则删除
                if has_got and now >= utils.timestamp_toDatetime(upd_time) + datetime.timedelta(days=7):
                    gift_list.pop(_index)
            self.put()

    def add_lv_up_giftcode(self,gift_id):
        """
        记录升级获得奖励的礼品id
        """
        pt_fg = False
        if 'lv_up' not in self.gift_code_info:
            self.gift_code_info['lv_up'] = {}
            pt_fg = True
        if gift_id not in self.gift_code_info['lv_up']:
            self.gift_code_info['lv_up'][gift_id] = []
            pt_fg = True
        if pt_fg:
            self.put()
    
    def get_giftcode_lv_up_award(self,gift_id=''):
        """
        检查是否有可领取的升级奖励
        """
        if not gift_id:
            gift_ids = self.gift_code_info.get('lv_up',{}).keys()
        else:
            gift_ids = [gift_id]
        if not gift_ids:
            return
        gift_config = self.game_config.gift_config.get('gift_config',{})
        user_prop_obj = UserProperty.get(self.uid)
        pt_fg = False
        for _id in gift_ids:
            if _id not in gift_config or _id not in self.gift_code_info.get('lv_up',{}):
                continue
            lv_up_gift = gift_config[_id].get('lv_up_gift',{})
            for need_lv in lv_up_gift:
                if int(need_lv)<=user_prop_obj.lv and need_lv not in self.gift_code_info['lv_up'][_id]:
                    self.gift_code_info['lv_up'][_id].append(need_lv)
                    pt_fg = True
                    msg = utils.get_msg('gift', 'lv_up_gift_award', self)
                    self.add_gift(lv_up_gift[need_lv], content=msg % need_lv)
        if pt_fg:
            self.put()

    def new_gift(self):
        '''
        获取所有的未领取的礼包
        '''
        data = {}
        for i in self.gift_list:
            if not self.gift_list[i].get('has_got',0):
                data[i] = self.gift_list[i]
        return data

    def new_gift_to_client(self,version):
        data = {}
        gift_list = copy.deepcopy(self.gift_list)
        for i in gift_list:
            if not gift_list[i].get('has_got',0):
                data[i] = gift_list[i]
                for k,v in data[i]['award'].items():
                    if isinstance(v,dict):
                        for kk,vv in v.items():
                            if isinstance(vv,dict):
                                data[i]['award'][k][kk] = vv.get('num',1)
        return data

    def get_gift(self,gift_id):
        tmp = {}
        if gift_id in self.gift_list and not self.gift_list[gift_id].get('has_got',0):
            up_obj = UserProperty.get(self.uid)
            tmp = up_obj.give_award(self.gift_list[gift_id]['award'],where='gift')
            self.gift_list[gift_id]['has_got'] = 1
            self.gift_list[gift_id]['got_time'] = int(time.time())
            self.put()
        return tmp

    @property
    def gift_num(self):
        gift_count = len(self.new_gift())
        return gift_count

    def get_new_gift_num(self,user_property_obj):
        from apps.models.user_login import UserLogin
        gift_count = len(self.new_gift())
        ul = UserLogin.get(self.uid)
        gift_count += ul.get_bonus_num(user_property_obj)
        return gift_count

#    def change_read(self,tag=1):
#        if tag:
#            self.read = 1
#        else:
#            self.read = 0
#        self.put()

    def add_gift(self,award,content=''):
        """
        award-奖励
        content-奖励原因,unicode字符串
        """
        if not award:
            return -1
        if not self.gift_list:
            index = 1
        else:
            index = max([int(i) for i in self.gift_list])+1
        pt_fg = False
        return_index = -1
        #version = float(self.game_config.system_config['version'])
        for k,v in award.items():
            if isinstance(v,int):
                award = {k:v}
                if k == 'gold':
                    content_save = content
                elif k == 'gacha_pt':
                    content_save = content
                elif k == 'coin':
                    content_save = content
                elif k == 'pvp_stamina':
                    content_save = content
                elif k == 'stamina':
                    content_save = content
                elif k == 'honor':
                    content_save = content
                else:
                    continue
                self.gift_list[str(index)] = {
                                         'content':content_save,
                                         'upd_time':int(time.time()),
                                         'has_got':0,
                                         'award':award,
                                         }
                return_index = str(index)
                index += 1
                pt_fg = True
            elif isinstance(v,dict):
                for kk,vv in v.items():
                    award = {k:{kk:vv}}
                    name = ''
                    num = ''
                    if k == 'equip':
                        name = self.game_config.equip_config[kk].get('name','')
                        num = vv.get('num',1)
                    elif k == 'card':
                        name = self.game_config.card_config[kk].get('name','')
                        num = vv.get('num',1)
                    elif k == 'item':
                        name = self.game_config.item_config[kk].get('name','')
                        num = vv
                    elif k == 'material':
                        name = self.game_config.material_config[kk].get('name','')
                        num = vv
                    elif k == 'props':
                        name = self.game_config.props_config[kk].get('name','')
                        num = vv
                    elif k == 'normal_soul':
                        name = self.game_config.card_config[kk.replace('soul', 'card')].get('name','') + utils.get_msg('soul', 'this_name', self)
                        num = vv
                    else:
                        continue
                    content_save = content
                    self.gift_list[str(index)] = {
                                     'content':content_save,
                                     'upd_time':int(time.time()),
                                     'has_got':0,
                                     'award':award,
                                     }
                    return_index = str(index)
                    index += 1
                    pt_fg = True
        if pt_fg:
            self.put()
        return return_index


    def remove(self,_id):
        if _id in self.gift_list:
            self.gift_list.pop(_id)
            self.put()

    def add_gift_by_dict(self, award, msg):
        """
        以如下格式添加gift：  
        {'160_card':{'lv':1,'category':'4','num':1}},  武将
        {'160_soul':1},  将魂
        """
        k = award.keys()[0]
        if k in ['gold','gacha_pt','coin']:
            self.add_gift(award, content=msg)
        elif 'card' in k:
            if isinstance(award[k], dict):
                self.add_gift({'card':award}, content=msg)
            # 区别是武将还是将魂， 如果是将魂 {'160_card':num}
            elif isinstance(award[k], int):
                self.add_gift({'normal_soul':award}, content=msg)
        elif 'equip' in k:
            self.add_gift({'equip':award}, content=msg)
        elif 'item' in k:
            self.add_gift({'item':award}, content=msg)
        elif 'props' in k:
            self.add_gift({'props':award}, content=msg)
        elif 'mat' in k:
            self.add_gift({'material':award}, content=msg)
        elif 'soul' in k:
            self.add_gift({'normal_soul':{k.replace("soul", "card"): award[k]}}, content=msg)

    def get_consume_award(self, coin):
        try:
            #获取运营配置的消耗奖励
            consume_award_conf = copy.deepcopy(self.game_config.operat_config.get("consume_award"))
            if not consume_award_conf:
                return
            #获取消耗奖励的内容
            user_property_obj = UserProperty.get(self.uid)
            consume_award_info = user_property_obj.consume_award_info
            old_consume_award_info = copy.deepcopy(consume_award_info)
            #遍历查找奖励内容
            for gift_id in consume_award_conf:
                gift_conf = consume_award_conf[gift_id]
                start_time = gift_conf.get('start_time')
                end_time = gift_conf.get('end_time','2111-11-11 11:11:11')
                now_str = datetime_toString(datetime.datetime.now())
                #未开放或已过期的礼包
                if now_str > end_time or now_str < start_time:
                    continue
                if gift_id not in consume_award_info:
                    consume_award_info[gift_id] = {
                                              'consume_coin': coin,
                                              'has_got_cnt': 0,   # 已领取的次数
                    }
                else:
                    consume_award_info[gift_id]['consume_coin'] += coin

                #金额未达到
                if consume_award_info[gift_id]['consume_coin'] - gift_conf.get('consume_coin',0) < 0:
                    continue
                #满足条件，发奖励

                #已经领取过的礼包
                print('chenhaiou gift_id: ', gift_id)
                # 如果有一次消耗元宝超过两倍 gift_conf['consume_coin']    
                for cnt in range(consume_award_info[gift_id]['consume_coin'] / gift_conf.get('consume_coin',0)):
                    consume_award_info[gift_id]['has_got_cnt'] += 1
                    if gift_conf.get('award', []):
                        msg =  gift_conf.get('name', '') + utils.get_msg('operat', 'consume_award', self).format(gift_conf.get('consume_coin',0))
                        for award_warp in gift_conf['award'].values():
                            award = utils.get_item_by_random_simple(award_warp)
                            self.add_gift_by_dict(award, msg)
                consume_award_info[gift_id]['consume_coin'] %= gift_conf.get('consume_coin',0)
            if old_consume_award_info != consume_award_info:
                user_property_obj.put()
        except:
            print traceback.format_exc()

    def get_lv_gift(self):
        """
        领取等级奖励
        """
        lv_up_award_conf = copy.deepcopy(self.game_config.operat_config.get("lv_up_award"))
        if not lv_up_award_conf:
            return

        main_msg = utils.get_msg('operat', 'lv_up_award', self)

        all_awards_lv = sorted(map(int, lv_up_award_conf.keys()))
        user_property_obj = UserProperty.get(self.uid)
        user_level = user_property_obj.lv
        # 比现在lv小的等级奖励都应该获得
        sould_send_awards_lv = all_awards_lv[:bisect.bisect(all_awards_lv, user_level)]
        for awards_lv in sould_send_awards_lv:
            awards_lv = str(awards_lv)
            if awards_lv in self.has_got_lv_gift:
                continue
            self.add_gift(lv_up_award_conf[awards_lv], main_msg.format(awards_lv))
            self.has_got_lv_gift.append(awards_lv)
        self.put()

    def get_bind_phone_gift(self):
        """
        领取绑定奖励， 每个礼拜只能领一次
        miaoyichao
        """
        #获取是否开启手机绑定功能
        bind_phone_is_open = self.game_config.system_config.get('bind_phone_is_open')
        if not bind_phone_is_open:
            return
        #获取绑定手机的奖励配置信息
        bind_phone_award_conf = copy.deepcopy(self.game_config.loginbonus_config.get("bind_phone_award"))
        if not bind_phone_award_conf:
            return
        #检查是否绑定手机
        user_property_obj = UserProperty.get(self.uid)
        has_bind = user_property_obj.property_info['bind_phone_number_info']['has_bind']
        if not has_bind:
            return
        #获取当前的星期
        now_week = datetime.date.today().isocalendar()[:2]
        last_got_award_week = user_property_obj.property_info['bind_phone_number_info'].get('last_got_award_week')
        # 最后一次领取的星期 与现在相同  不发
        if last_got_award_week and now_week <= last_got_award_week:
            return
        #获取提示语信息
        msg = utils.get_msg('bind', 'get_bind_award_msg', self)
        #添加奖励
        self.add_gift(bind_phone_award_conf, msg)
        #更新绑定信息
        user_property_obj.property_info['bind_phone_number_info']['last_got_award_week'] = now_week
        user_property_obj.put()
        self.put()

    def add_has_got_gift_code(self, gift_code):
        if not hasattr(self, 'has_got_gift_code'):
            self.has_got_gift_code = {}
            self.put()
        if gift_code in self.has_got_gift_code:
            return False
        else:
            self.has_got_gift_code[gift_code] = 1
            self.put()
            return True

    def vip_gift_format(self,vip_gift_sale_config,vip_gift_value):
        '''
        vip礼包格式化礼包信息(列表,购买)
        '''
        temp = {}
        data = {}
        vip_gift_id = ''
        vip_charge_info = []
        if type(vip_gift_value) == list:
            vip_charge_info  =  vip_gift_value
            temp = vip_gift_sale_config
        elif type(vip_gift_value) == str:
            vip_gift_id = vip_gift_value
            temp[vip_gift_id] = vip_gift_sale_config[vip_gift_id]
        else:
            return data
        if temp:   
            for k in temp:
                coin = temp[k].get('coin',0)
                gift = temp[k].get('gift',{})
                data[k] = {'gift':{},'coin':int(coin)}
                if vip_charge_info:
                    if k in vip_charge_info:
                        data[k]['buy'] = True
                    else:
                        data[k]['buy'] = False
                if gift:
                    for t in gift:
                       #exp = t.split('_')
                        num = gift[t]
                        if 'item' in t:
                            if 'item' not in data[k]['gift']:
                                data[k]['gift']['item'] = {}
                            data[k]['gift']['item'][t] = num
                        elif 'props' in t:
                            if 'props' not in data[k]['gift']:
                                data[k]['gift']['props'] = {}
                            data[k]['gift']['props'][t] = num
                        elif 'card' in t:
                            if 'card'  not in data[k]['gift']:
                                data[k]['gift']['card'] = {}
                            data[k]['gift']['card'][t] = num
                        elif 'equip' in t:
                            if 'equip'  not in data[k]['gift']:
                               data[k]['gift']['equip'] = {}
                            data[k]['gift']['equip'][t] = num
                        elif 'mat' in t:
                            if 'material' not in data[k]['gift']:
                               data[k]['gift']['material'] = {}
                            data[k]['gift']['material'][t] = num 
                        elif 'soul' in t:
                            if 'soul' not in data[k]['gift']:
                               data[k]['gift']['soul'] = {}
                            for r in gift['soul']:
                               #exp = r.split('_')
                                num = gift['soul'][r]
                                count = len(r)
                                if count == 3:
                                    if 'card' in r:
                                        if vip_gift_id:
                                            if 'card' not in data[k]['gift']['soul']:
                                                data[k]['gift']['soul']['card'] = {}
                                            data[k]['gift']['soul']['card'][r.rstrip('_soul')] = num
                                        else: 
                                            data[k]['gift']['soul'][r.rstrip('_soul')] = num
                                    if 'equip' in r:
                                        if vip_gift_id:
                                            if 'equip' not in data[k]['gift']['soul']:
                                                data[k]['gift']['soul']['equip'] = {}
                                            data[k]['gift']['soul']['equip'][r.rstrip('_soul')] = num 
                                        else:   
                                            data[k]['gift']['soul'][r.rstrip('_soul')] = num
                                if count == 4:
                                    str_path = r[-2:]
                                    if vip_gift_id:       
                                        if 'equip' not in data[k]['gift']['soul']:
                                            data[k]['gift']['soul']['equip'] = {}
                                        data[k]['gift']['soul']['equip'][r[0:r.find('_soul')]+str_path] = num
                                    else:
                                        data[k]['gift']['soul'][r[0:r.find('_soul')]+str_path] = num
        return data

    def add_vip_gift(self,uid,gift,vip_gift_id):
        '''
        添加vip礼包的物品

        '''
        user_property_obj = UserProperty.get_instance(uid)
        user_pack_obj = UserPack.get_instance(uid)
        user_equips_obj = UserEquips.get_instance(uid)
        user_card_obj = UserCards.get_instance(uid)
        user_soul_obj = UserSouls.get_instance(uid)
        data = {}
        if gift[vip_gift_id]:
            temp = gift[vip_gift_id]['gift']
            for k in temp:
                if k:
                    #添加武将
                    if k == 'card':
                        if 'get_cards' not in data:
                            data['get_cards'] = []
                        for m in temp[k]:
                            num = temp[k][m]
                            for i in xrange(num):
                                success_fg,all_cards_num,ucid,is_first = user_card_obj.add_card(m,1,where='vip_gift')
                                tmp = {'ucid':ucid}
                                tmp.update(user_card_obj.cards[ucid])
                                data['get_cards'].append(tmp)
                    #添加装备
                    elif k == 'equip':
                        if 'get_equips' not in data:
                            data['get_equips'] = []
                        for m in temp[k]:
                            num = temp[k][m]
                            fg,all_equips_num,ueid,is_first = user_equips_obj.add_equip(m,num)
                            tmp = {'ueid':ueid}
                            tmp.update(user_equips_obj.equips[ueid])
                            data['get_equips'].append(tmp)
                    #添加药水
                    elif k == 'item':
                        for m in temp[k]:
                            num  = temp[k][m]
                            user_pack_obj.add_item(m,num)
                        data[k] = temp[k]
                    #添加道具
                    elif k == 'props':
                        for m in temp[k]:
                            num = temp[k][m]
                            user_pack_obj.add_props(m,num)
                        data[k] = temp[k]
                    #添加材料
                    elif k == 'material':
                        for m in temp[k]:
                            num = temp[k][m]
                            user_pack_obj.add_material(m,num)
                        data[k] = temp[k]
                    #添加碎片
                    elif k == 'soul':
                        if 'equip' in temp[k]:
                            for m in temp[k]['equip']:
                                user_soul_obj.add_equip_soul(m,num)
                        if 'card' in temp[k]:
                            for m in temp[k]['card']:
                                user_soul_obj.add_normal_soul(m,num)
                        data[k] = temp[k]
        #添加已购买过vid的id
        user_property_obj.add_vip_gift_id(vip_gift_id)
        return data 
