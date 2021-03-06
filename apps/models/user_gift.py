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
    fields = ['uid','gift_list','today','gift_code_type','gift_code_info', 'has_got_lv_gift', 'has_got_gift_code',
        'sign_in_record', 'open_server_record', 'sign_month']

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
        self.sign_in_record = {}   # 记录签到奖励的信息
        self.sign_month = ''       # 签到的月份
        self.open_server_record = {
            'gifts': {},
            'date_info': {}
        } # 记录开服奖励的信息

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

    # def get_new_gift_num(self,user_property_obj):
    #     from apps.models.user_login import UserLogin
    #     gift_count = len(self.new_gift())
    #     ul = UserLogin.get(self.uid)
    #     gift_count += ul.get_bonus_num(user_property_obj)
    #     return gift_count

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
                    # elif k == 'item':
                    #     name = self.game_config.item_config[kk].get('name','')
                    #     num = vv
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
        if gift_code in self.has_got_gift_code:
            return False
        else:
            self.has_got_gift_code[gift_code] = 1
            self.put()
            return True

    def has_got_all_open_server_gifts(self):
        for info in self.open_server_record['gifts'].values():
            if not info['has_got']:
                return False
        return True

    def today_can_sign(self):
        '''独立字段 判断今天是否可以签到'''
        now = datetime.datetime.now()
        today = str(now.day)
        return not self.sign_in_record.setdefault(today, {}).setdefault('today_has_signed_in', False)
 
    def openserver_can_get(self):
        '''判断今天是否可领取开服礼包'''
        today_str = utils.get_today_str()
        return not self.open_server_record['date_info'].get(today_str, False)

    @property
    def total_sign_days(self):
        '''已签到的天数'''
        days = 0
        for info in self.sign_in_record.values():
            if info.get('has_got', False):
                days += 1
        return days

    @property
    def total_open_days(self):
        '''已领取开服奖励的天数'''
        days = 0
        for info in self.open_server_record['gifts'].values():
            if info['has_got']:
                days += 1
        return days