#!/usr/bin/env python
# encoding: utf-8
"""
file_name:user_property.py
"""
import time

from apps.models.level_user import LevelUser
from apps.models.virtual.user_level import UserLevel as UserLevelMod
from apps.models.virtual.card import Card as CardMod
from apps.models import data_log_mod
from apps.models.friend import Friend
from apps.common import utils
from django.conf import settings
from apps.oclib.model import TopModel
from apps.models.user_souls import UserSouls
from apps.models import GameModel


lv_top_model = TopModel.create(settings.LV_TOP)


class UserProperty(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid', 'property_info', 'charge_award_info', 'consume_award_info']
    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        self.uid = None
        self.property_info = {}
        self.charge_award_info = {}
        self.consume_award_info = {}

    @classmethod
    def get_instance(cls,uid):
        obj = super(UserProperty,cls).get(uid)

        if obj is None:
            obj = cls.create(uid)
        return obj


    @classmethod
    def get(cls,uid):
        obj = super(UserProperty,cls).get(uid)
        return obj

    @property
    def double_charge(self):
        return self.property_info.get('double_charge', False)
    
    @classmethod
    def create(cls,uid):
        up = cls()
        up.uid = uid
        up.charge_award_info = {}
        up.consume_award_info = {}

        up.property_info = {
                            'exp':0,#经验值
                            'lv':1,
                            'gold':0,
                            'coin':0,
                            'stamina':0,
                            'card_exp_point': 1000, # 拥有的武将经验点数
                            'fight_soul': 0, #战魂
                            'stamina_upd_time': int(time.time()),

                            'newbie': True,     # 是否新手
                            'newbie_steps':0,     # 已完成的新手步骤

                            'bind_award':True,

                            'has_bought_vip_package':[],     #Vip等级所购买的vip礼包 只可以买一次
                            'charge_coins': 0,       # 总共充值的人民币
                            'charge_money': 0,      #  总共购买过元宝数
                            'charge_item_bought_times': {},    #  每种充值商品已购买次数
                            'monthCard_remain_days': {},       # 每种月卡剩余使用天数   'monthCard30': 29
                            "update_award":[], #版本更新奖励

                            'charged_user':False,#是否付费用户，包含大礼包

                            'recover_times':{
                                'today_str':utils.get_today_str(),
                                'recover_stamina':0,            #回复体力次数
                                'recover_pvp_stamina':0,        #回复PVP次数
                                'recover_mystery_store':0,      #刷新神秘商店的次数
                                'recover_copy':{
                                    'normal':0,
                                    'special':0,
                                    'daily': {},
                                },               #刷新副本次数                                
                            },         #使用元宝购买回复的次数
                            'wipe_out_times': 0,    # 当天已扫荡次数

                        }
        # 初始化每个试炼战场回复次数都为0
        daily_floods = up.game_config.daily_dungeon_config.keys()
        for daily_flood in daily_floods:
            up.property_info['recover_times']['recover_copy']['daily'][daily_flood] = 0
        # 用户初始化 体力值
        userLevelMod = UserLevelMod.get(str(up.property_info['lv']), game_config=up.game_config)
        up.property_info['stamina'] = userLevelMod.stamina
        # 用户初始化 铜钱 元宝等
        user_info_init = up.game_config.user_init_config["init_user_info"]
        up.property_info.update(user_info_init)
        up.put()

        return up


    @property
    def lv(self):
        """
        用户lv
        miaoyichao
        """
        return self.property_info['lv']

    def reach_max_lv(self):
        return str(self.lv + 1) not in self.game_config.user_level_config

    @property
    def next_lv(self):
        """
        用户下一lv
        """
        if not self.reach_max_lv():
            #如果配置中有下一等级的时候 返回+1
            return self.lv + 1
        else:
            #配置中没有的话就还显示当前的
            return self.lv

    @property
    def exp(self):
        """
        用户exp
        miaoyichao
        """
        return self.property_info['exp']

    @property
    def this_lv_exp(self):
        """
        当前级别所需的经验值
        miaoyichao
        """
        return UserLevelMod.get(self.lv).exp

    @property
    def next_lv_exp(self):
        """
        下一级别所需的经验值
        miaoyichao
        """
        return UserLevelMod.get(self.next_lv).exp

    @property
    def this_lv_now_exp(self):
        """
        当前级别内，现在积累的经验值
        如果达到最大等级，返回最后两等级的差
        """
        if self.reach_max_lv():
            return UserLevelMod.get(self.lv).exp - UserLevelMod.get(self.lv - 1).exp
        return self.exp - self.this_lv_exp

    @property
    def charged_fg(self):
        """
        用户充值过与否的标识，不包括6元大礼包
        miaoyichao
        """
        return self.property_info['charged_fg']
    
    @property
    def charged_user(self):
        """
        用户充值过与否的标识，包括6元大礼包
        miaoyichao
        """
        return self.property_info.get('charged_user', False)

    @property
    def vip_cur_level(self):
        '''
        获取当前vip等级
        '''
        current_vip_level = 0
        charge_sum_coin = self.charge_sumcoin
        try:
            # 从vip配置信息中循环找出当前用户充值所匹配的vip等级
            for level,value in self.game_config.user_vip_config.items():
                # 获取vip等级
                if value['coin'] <= charge_sum_coin:
                    # 该层判断是为了防止字典的无序所产生的错误
                    if current_vip_level > int(level):
                        pass
                    else:
                        current_vip_level = int(level)
        except:
            #没有获取到vip的配置信息
            #测试使用
            current_vip_level = 1000
        #vip等级结果的返回
        return current_vip_level

    @property
    def vip_next_level(self):
        '''
        计算vip的下一等级
        '''
        vip_cur_level = self.vip_cur_level
        next_lv = self.game_config.user_vip_config.get(str(vip_cur_level+1),0)
        if next_lv:
            return vip_cur_level + 1
        else:
            return vip_cur_level

    @property
    def next_lv_need_coin(self):
        '''
        计算下一级所需要的金钱
        '''
        vip_cur_level = self.vip_cur_level
        vip_next_level = self.vip_next_level
        if vip_cur_level == vip_next_level:
            needcoin = 0
        else:
            vip_conf = self.game_config.user_vip_config
            cur_coin = vip_conf[str(vip_cur_level)]['coin']
            nxt_coin = vip_conf[str(vip_next_level)]['coin']
            needcoin = nxt_coin - cur_coin
        return needcoin

    @property
    def next_lv_need_exp(self):
        """
        到下一级别需要的经验值
        如果达到最大等级，返回最后两等级的差
        """
        if self.reach_max_lv():
            return 0
        return self.next_lv_exp - self.exp

    @property
    def lv_region(self):
        """
        用户级别所属的区间
        """
        return (self.property_info['lv'] / 6) + 1

    @property
    def login_time(self):
        """
        用户登录时间
        """
        from apps.models.user_login import UserLogin
        return UserLogin.get_instance(self.uid).login_info['login_time']

    @property
    def gold(self):
        """
        用户的gold
        """
        return self.property_info['gold']

    @property
    def coin(self):
        """
        用户的coin
        """
        return self.property_info['coin']

    @property
    def newbie(self):
        """
        用户是否是新手
        """
        return self.property_info.get('newbie', True)

    @property
    def newbie_steps(self):
        """
        用户新手引导的步骤
        """
        return self.property_info['newbie_steps']

    @property
    def first_charge(self):
        '''
        首充标志
        '''
        return self.property_info.get('first_charge',False)

    @property
    def stamina(self):
        '''
        返回当前用户的体力值
        '''
        return self.property_info['stamina']

    @property
    def get_fight_soul(self):
        '''
        返回战魂
        '''
        return self.property_info['fight_soul']

    @property
    def update_award(self):
        return self.property_info["update_award"]

    @property
    def charge_sumcoin(self):
        """
        得到该玩家累计的充值元宝个数
        """
        return self.property_info["charge_coins"]

    @property
    def charge_sum_money(self):
        '''
        得到玩家累计充值rmb
        '''
        return self.property_info["charge_money"]

    def refresh_lv(self,version):
        """
        刷新等级
        """

        max_lv = max([int(i) for i in self.game_config.user_level_config.keys()])
        new_lv = 1
        old_lv = self.lv
        for next_lv in range(1,max_lv + 1):
            userLevelMod = UserLevelMod.get(next_lv)
            if self.property_info['exp'] >= userLevelMod.exp:
                new_lv = next_lv
            else:
                break
        if old_lv != new_lv:
            self.property_info['lv'] = new_lv
            userLevelMod = UserLevelMod.get(new_lv)
            self.property_info['stamina'] = userLevelMod.stamina

            #将用户写入新级别对应的用户列表中
            subarea = self.user_base.subarea
            LevelUser.get_instance(subarea, self.lv_region).add_user(self.uid)
        self.put()

    def add_exp(self, exp, where=''):
        '''
        添加用户的经验
        不管是加还是扣经验都会触发等级变化
        返回： 是否升级, {}
        '''
        #保存变化前的exp
        from apps.models.user_gift import UserGift
        old_exp = self.property_info['exp']


        old_lv = self.lv
        new_lv = self.lv
        self.property_info['exp'] = self.property_info['exp'] + exp
        while True:
            new_lv += 1
            userLevelMod = UserLevelMod.get(new_lv)
            if not userLevelMod.exp or self.property_info['exp'] < userLevelMod.exp:
                new_lv -= 1
                break

        if new_lv > old_lv:
            #有升级的话就写日志和重新排名
            #写日志
            log_data = {}
            log_data['old_exp'] = old_exp
            log_data['old_lv'] = old_lv
            log_data['add_exp'] = exp
            log_data['new_lv'] = new_lv
            log_data['new_exp'] = self.property_info['exp']
            log_data['where'] = where
            data_log_mod.set_log('UserLevelHistory', self, **log_data)
            #新等级
            self.property_info['lv'] = new_lv
            userLevelMod = UserLevelMod.get(new_lv)
            #获取前20000名对应的分数
            rank_lv = lv_top_model.get_score(20000)
            #只有等级能到达50000名的才会进入排行榜
            if not rank_lv or new_lv>rank_lv:
                lv_top_model.set(self.uid,new_lv)
            #更新体力，cost
            self.property_info['stamina'] += userLevelMod.lv_stamina

            #将用户写入新级别对应的用户列表中
            subarea = self.user_base.subarea 
            LevelUser.get_instance(subarea, self.lv_region).add_user(self.uid)
            inviter_uid = Friend.get(self.uid).inviter
            if inviter_uid:
                inviter_friend = Friend.get(inviter_uid)
            else:
                inviter_friend = None
            #升级时，检查是否有礼品码的升级奖励
            user_gift_obj = UserGift.get_instance(self.uid)
            user_gift_obj.get_giftcode_lv_up_award()
            #升级时，检查是否有升级奖励
            msg = utils.get_msg('user','lv_up_award', self)

            for lv in range(old_lv + 1, new_lv + 1):
                if 'award' in self.game_config.user_level_config[str(lv)]:
                    user_gift_obj.add_gift(self.game_config.user_level_config[str(lv)]['award'],msg % lv)
                #用户升级后，将自己信息写入邀请者
                if inviter_friend:
                    inviter_friend.record_invited_user(self.uid, lv)

        self.put()
        return new_lv > old_lv, {}

    def reset_recover_times(self):
        '''
        重置回复次数
        input None
        output None
        '''
        #将所有的回复次数全部清空  代表着新的一天
        self.property_info['recover_times']['today_str'] = utils.get_today_str()
        self.property_info['recover_times']['recover_stamina'] = 0
        self.property_info['recover_times']['recover_pvp_stamina'] = 0
        self.property_info['recover_times']['recover_mystery_store'] = 0
        self.property_info['recover_times']['recover_copy'] = {}
        self.property_info['recover_times']['recover_copy'] = {
            'normal':0,
            'special':0,
            'daily': {},
        }
        # 初始化每个试炼战场回复次数都为0
        daily_floods = self.game_config.daily_dungeon_config.keys()
        for daily_flood in daily_floods:
            self.property_info['recover_times']['recover_copy']['daily'][daily_flood] = 0
        self.put()

    
    def update_stamina_from_time(self):
        '''
        每隔一段时间会恢复体力  根据现在和上次回复stamina的时间差计算可以获得的体力
        '''

        #获取上一次更新的时间差  分钟数
        diff_minutes = self.get_update_time_minutes()
        #获取系统的每隔多少时间回复一个体力值
        stamina_recover_time_config = self.game_config.system_config['stamina_recover_time']
        #统计可以回复的体力数
        restore_stamina_num = int(diff_minutes / stamina_recover_time_config)
        if restore_stamina_num <= 0:
            #不合符更新要求的 直接返回
            return
        #计算体力值 若已经超过体力上限，不进行回复
        if self.property_info['stamina'] < self.max_stamina:
            stamina_temp = min(self.property_info['stamina'] + restore_stamina_num, self.max_stamina)
            self.property_info['stamina'] = stamina_temp

        # 更新时间
        self.property_info['stamina_upd_time'] = int(self.property_info['stamina_upd_time'] +
        stamina_recover_time_config * restore_stamina_num * 60)
        self.put()
        return

    def get_update_time_minutes(self):
        """
        返回上次更新到这次更新的时间差，分钟数
        """
        now = int(time.time())
        should_update_time = self.property_info.get("stamina_upd_time",now)
        to_now = now - should_update_time
        diff_minutes = to_now / 60
        return diff_minutes

    def is_gold_enough(self,gold):
        """
        检查用户的gold是否足够
        args:
            gold: int
        return:
            bool
        """
        return self.property_info['gold'] >= abs(gold)

    def is_coin_enough(self,coin):
        '''
        判断元宝是否足够
        args:
            coin: int
        return:
            bool
        '''
        return self.property_info['coin'] >= abs(coin)

    def minus_coin(self, coin, where):
        '''
        扣除元宝
        args:
            coin: int
        return:
            bool
        '''
        coin = abs(coin)
        if self.is_coin_enough(coin):
            #元宝足够
            before = self.property_info['coin']
            self.property_info['coin'] -= coin
            self.put()
            after = self.property_info['coin']
            #记录消耗的元宝 因为可能发奖励
            # from apps.models.user_gift import UserGift
            # user_gift_obj = UserGift.get(self.uid)
            # user_gift_obj.get_consume_award(coin)

            #写日志
            log_data = {'where': where, 'num': coin, 'before': before, 'after': after}
            data_log_mod.set_log('CoinConsume', self, **log_data)
            return True
        else:
            #元宝不够的话
            return False

    def is_fight_soul_enough(self, fight_soul):
        '''
        判断战魂是否足够
        '''
        return self.property_info['fight_soul'] >= abs(fight_soul)

    def minus_fight_soul(self, fight_soul, where=None):
        """
        扣除战魂点
        """
        fight_soul = abs(fight_soul)
        if self.is_fight_soul_enough(fight_soul):
            self.property_info['fight_soul'] -= fight_soul
            self.put()
            #写日志
            if where:
                log_data = {'where':where, 'num': fight_soul, "after": self.get_fight_soul}
                data_log_mod.set_log('FightSoulConsume', self, **log_data)
            return True
        else:
            return False

    def minus_gold(self,gold,where=""):
        """
        减少gold数量
        input gold
        output True False
        """
        gold = abs(gold)
        #判断金币是否足够
        if self.is_gold_enough(gold):
            #之前的金币和减少后的
            before = self.property_info['gold']
            self.property_info['gold'] -= gold
            self.put()
            after  = self.property_info['gold']
            #写日志

            log_data = {'where':where, 'num':gold, 'before': before, 'after': after}
            data_log_mod.set_log('GoldConsume', self, **log_data)
            return True
        else:
            return False

    @property
    def max_stamina(self):
        '''
        根据用户的等级获取最大体力值
        '''
        userlvmod = UserLevelMod.get(self.lv, self.game_config)
        return userlvmod.stamina

    @property
    def max_friend_num(self):
        lv = self.property_info['lv']
        level = UserLevelMod.get(lv)
        vip_lv = self.vip_cur_level
        #miaoyichao start
        vip_add_friend_num = self.game_config.user_vip_config[str(vip_lv)].get('friend_upper',0)
        max_num = level.friend_num + self.property_info.get('friend_extend_num',0)+vip_add_friend_num
        #miaoyichao end
        #max_num = level.friend_num + self.property_info.get('friend_extend_num',0)
        return max_num

    @property
    def friend_extend_num(self):
        friend_extend_num = self.property_info.get('friend_extend_num',0)
        return friend_extend_num

    @property
    def invite_code(self):
        return str(hex(int(self.uid)))[2:]

    @property
    def invite_info(self):
        if 'invite_info' not in self.property_info:
            self.property_info['invite_info'] = {
                'inviter':'',
                'has_award':False,
                'new_lv_10_user':[],
                'all_lv_10_user':[],
                'all_invited_user':0,
            }
            self.put()
        return self.property_info.get('invite_info')

    def is_gacha_pt_enough(self,gacha_point):
        """
        检查用户gacha_pt是否足够  删除  不再需要

        args:
            gacha_pt: int
        return:
            bool
        """
        return self.property_info['gacha_pt'] >= abs(gacha_point)

    def is_stamina_enough(self,stamina):
        """
        检查用户stamina是否足够

        args:
            stamina: int
        return:
            bool
        """
        return self.stamina >= abs(stamina)


    def minus_gacha_pt(self,gacha_pt):
        """
        减少用户的gacha_pt

        args:
            gacha_pt:int
        """
        gacha_pt = abs(gacha_pt)
        if self.is_gacha_pt_enough(gacha_pt):
            self.property_info['gacha_pt'] -= gacha_pt
            self.put()
            return True
        else:
            return False

    def minus_stamina(self,stamina):
        """
        减少stamina数量
        """
        stamina = abs(stamina)
        if self.is_stamina_enough(stamina):
            #如果当前stamina是满值，则下次更新时间是10分钟后
            if self.property_info['stamina'] == self.max_stamina:
#                stamina_recover_time_config = self.game_config.system_config['stamina_recover_time']
                self.property_info['stamina_upd_time'] = int(time.time())
#                + stamina_recover_time_config * 60
            self.property_info['stamina'] -= stamina
            self.put()
            return True
        else:
            return False


    def is_card_exp_point_enough(self, card_exp_point):
        """
        检查用户card_exp_point是否足够

        args:
            card_exp_point: int
        return:
            bool
        """
        return self.property_info['card_exp_point'] >= card_exp_point

    def minus_card_exp_point(self, card_exp_point, where=""):
        """
        减少card_exp_point 武将经验点
        """
        card_exp_point = abs(card_exp_point)
        if self.is_card_exp_point_enough(card_exp_point):
            self.property_info['card_exp_point'] -= card_exp_point
            self.put()
            #写日志
            log_data = {'where': where, 'num': -card_exp_point, 'after': self.property_info['card_exp_point']}
            data_log_mod.set_log('CardExpPoint', self, **log_data)
            return True
        else:
            return False

    def add_card_exp_point(self, card_exp_point, where=""):
        """
        添加武将经验点
        """
        card_exp_point = abs(card_exp_point)
        self.property_info['card_exp_point'] += card_exp_point

        #写日志
        log_data = {'where': where, 'num': card_exp_point, 'after': self.property_info['card_exp_point']}
        data_log_mod.set_log('CardExpPoint', self, **log_data)
        self.put()

    def update_self_common(self,common):
        """
        更新自我介绍

        args:
            common:string 自我介绍
        """
        if (common):
            self.property_info['self_common'] = common
            self.put()
            return True

    def add_stamina(self, stamina):
        """
        增加用户的stamina 没有上限的
        """
        self.property_info['stamina'] += stamina
        self.put()
        return

    def add_gold(self, gold, where=""):
        """
        增加用户的金币
        """
        before = self.property_info['gold'] 
        self.property_info['gold'] += gold
        self.put()
        after = self.property_info['gold']

        #写日志
        log_data = {'where': where, 'num': gold, 'before': before, 'after': after, }
        data_log_mod.set_log('GoldProduct', self, **log_data)
        return

    def add_coin(self, coin, where=""):
        """
        增加用户的代币
        input coin
        output None
        """
        before = self.property_info['coin']
        self.property_info['coin'] += coin
        self.put()
        after  = self.property_info['coin']

        log_data = {'where': where, 'num': coin, 'before': before, 'after': after}
        data_log_mod.set_log('CoinProduct', self, **log_data)
        return

    def test_give_award(self, award, where=None):
        '''
        发奖励 返回格式化后的信息
        '''
        data = {}
        for k in award:
            if k == 'coin':
                #处理元宝奖励
                self.add_coin(award[k],where=where)
                #格式化返回的参数
                data[k] = award[k]
            elif k == 'gold':
                #处理金币的奖励
                self.add_gold(award[k],where=where)
                #格式化返回的参数
                data[k] = award[k]
            elif k == 'card':
                #处理武将的奖励
                from apps.models.user_cards import UserCards
                uc = UserCards.get(self.uid)
                data[k] = []
                for cid in award[k]:
                    #获取武将的数量
                    num = int(award[k][cid])
                    for i in xrange(num):
                        #添加武将并记录
                        fg,all_cards_num,ucid,is_first = uc.add_card(cid,1,where=where)
                        tmp = {'ucid':ucid}
                        tmp.update(uc.cards[ucid])
                        #格式化返回的参数
                        data[k].append(tmp)
            elif k == 'equip':
                from apps.models.user_equips import UserEquips
                ue = UserEquips.get(self.uid)
                data[k] = []
                for eid in award[k]:
                    #获取装备的数量
                    num = int(award[k][eid])
                    for i in xrange(num):
                        #添加装备并记录
                        fg,all_equips_num,ueid,is_first = ue.add_equip(eid,where=where)
                        tmp = {'ueid':ueid}
                        tmp.update(ue.equips[ueid])
                        #格式化返回的参数
                        data[k].append(tmp)
            elif k == 'mat':
                data[k] = {}
                from apps.models.user_pack import UserPack
                up = UserPack.get_instance(self.uid)
                for material_id in award[k]:
                    num = int(award[k][material_id])
                    if material_id not in data[k]:
                        data[k][material_id] = 0
                    #格式化返回的参数
                    data[k][material_id] += num
                    up.add_material(material_id,num,where=where)
            elif k == 'item':
                data[k] = {}
                from apps.models.user_pack import UserPack
                up = UserPack.get_instance(self.uid)
                for item_id in award[k]:
                    num = int(award[k][item_id])
                    if item_id not in data[k]:
                        data[k][item_id] = 0
                    #格式化返回的参数
                    data[k][item_id] += num
                    up.add_item(item_id,num,where=where)
            elif k == 'props':
                data[k] = {}
                from apps.models.user_pack import UserPack
                up = UserPack.get_instance(self.uid)
                for props_id in award[k]:
                    num = int(award[k][props_id])
                    if props_id not in data[k]:
                        data[k][props_id] = 0
                    #格式化返回的参数
                    data[k][props_id] += num
                    #用户添加道具
                    up.add_props(props_id,num,where=where)
            elif k == 'soul':
                #处理碎片的逻辑
                data[k] = {}
                soul_info = award[k]
                us = UserSouls.get_instance(self.uid)
                for soul_type in soul_info:
                    if soul_type == 'card':
                        #处理武将碎片的逻辑
                        data[k][soul_type] = {}
                        card_soul_info = soul_info[soul_type]
                        for card_id in card_soul_info:
                            num = int(card_soul_info[card_id])
                            if card_id not in data[k][soul_type]:
                                data[k][soul_type][card_id] = 0
                            #格式化返回的参数
                            data[k][soul_type][card_id] += num
                            #用户添加碎片
                            us.add_normal_soul(card_id,num,where=where)
                    elif soul_type == 'equip':
                        #处理装备碎片的逻辑
                        data[k][soul_type] = {}
                        equip_soul_info = soul_info[soul_type]
                        for equip_id in equip_soul_info:
                            num = int(equip_soul_info[equip_id])
                            if equip_id not in data[k][soul_type]:
                                data[k][soul_type][equip_id] = 0
                            #格式化返回的参数
                            data[k][soul_type][equip_id] += num
                            #用户添加碎片
                            us.add_equip_soul(equip_id,num,where=where)
                    else:
                        #未识别碎片
                        pass
            elif k == 'stamina':
                #添加体力信息
                self.add_stamina(int(award[k]))
                #格式化返回的参数
                data[k] = int(award[k])
            elif k == 'normal_soul':
                data[k] = {}
                user_souls_obj = self.user_souls
                for soul_id in award[k]:
                    user_souls_obj.add_normal_soul(soul_id, award[k][soul_id], where)
                    data[k][soul_id] = award[k][soul_id]
            elif k == 'exp':
                # 经验
                self.add_exp(award[k], where=where)
                data[k] = award[k]
            elif k == 'exp_point':
                # 卡经验
                self.add_card_exp_point(award[k], where=where)
                data[k] = award[k]

            else:
                pass
        return data

    def give_award(self,award,where=None):
        """
        给用户奖励
        """
        tmp = {}
        for key in award:
            if key == 'gold':
                self.add_gold(award[key],'award_%s' % where)
                tmp[key] = award[key]
            elif key == 'coin':
               self.add_coin(award[key],'award_%s' % where)
               tmp[key] = award[key]
            elif key == 'card':
                tmp[key] = {}
                from apps.models.user_cards import UserCards
                uc = UserCards.get(self.uid)
                for cid in award[key]:
                    this_card = CardMod.get(cid, game_config=self.game_config)
                    lv = min(award[key][cid].get('lv',1),this_card.max_lv)
                    num = award[key][cid].get("num", 1)
                    category = award[key][cid].get("category", '')
                    quality = award[key][cid].get("quality", '')
                    for index in range(num):
                        fg,all_cards_num,ucid,is_first = uc.add_card(cid,lv,where='award_%s' % where,category=category,quality=quality)
                        tmp[key][ucid] = uc.get_card_dict(ucid)
            elif key == 'equip':
                tmp[key] = {}
                from apps.models.user_equips import UserEquips
                eq_obj = UserEquips.get(self.uid)
                for equip in award[key]:
                    num = award[key][equip].get("num", 1)
                    for ind in range(num):
                        fg,all_equips_num,ueid,is_first = eq_obj.add_equip(equip,'award_%s' % where)
                        tmp[key][ueid] = eq_obj.get_equip_dict(ueid)
            elif key == 'item':
                tmp[key] = {}
                user_pack_obj = self.user_pack
                for item_id in award[key]:
                    user_pack_obj.add_item(item_id, award[key][item_id],'award_%s' % where)
                    tmp[key][item_id] = award[key][item_id]
            elif key == 'material':
                tmp[key] = {}
                user_pack_obj = self.user_pack
                for material_id in award[key]:
                    user_pack_obj.add_material(material_id, award[key][material_id],'award_%s' % where)
                    tmp[key][material_id] = award[key][material_id]
            elif key == 'stamina':
                self.add_stamina(int(award[key]))
                tmp[key] = award[key]
            #elif key == 'super_soul':
            #    user_souls_obj = UserSouls.get_instance(self.uid)
            #    user_souls_obj.add_super_soul(int(award[key]), 'award_%s' % where)
            #    tmp[key] = award[key]
            elif key == 'normal_soul':
                tmp[key] = {}
                user_souls_obj = UserSouls.get_instance(self.uid)
                for soul_id in award[key]:
                    user_souls_obj.add_normal_soul(soul_id, award[key][soul_id], 'award_%s' % where)
                    tmp[key][soul_id] = award[key][soul_id]
            elif key == 'renown':
                user_pvp_obj = self.user_base.user_pvp
                user_pvp_obj.add_renown(int(award[key]))
            elif key == 'honor':
                user_real_pvp = self.user_real_pvp
                user_real_pvp.add_honor(award[key])
                tmp[key] = award[key]
        return tmp

    def dungeon_clear(self):
        """首次通关战场时，给予奖励
        """
        coin = self.game_config.system_config['dungeon_clear_coin']
        self.add_coin(coin, "dungeon_clear")
        self.put()
        return coin

#    def is_newbie_in_time(self, hours=0, minutes=0):
#        """
#        检查用户是否是在完成新手引导一定时间内
#        args:
#            hours(int):小时数
#            minutes(int):分钟数
#        return:
#            目前是否处于新手引导完成后一定时间段内的bool值
#        """
#        #如果用户没有完成新手引导时，返回False
#        if self.property_info['newbie']:
#            return False
#        now = int(time.time())
#        newbie_done_time = self.property_info['newbie_done_time']
#        flag = now <= (newbie_done_time + datetime.timedelta(hours = hours, minutes = minutes))
#        return flag

    def recover_stamina(self):
        """回复体力
        """
        self.property_info['stamina'] = self.max_stamina
        self.property_info['stamina_upd_time'] = int(time.time())
        self.put()

    def add_recover_times(self, where, dtype='', floor_id=''):
        """ 更新已回复次数"""
        if where in self.property_info['recover_times']:
            if dtype == 'normal':
                self.property_info['recover_times'][where][dtype] += 1
            elif dtype == 'daily':
                self.property_info['recover_times'][where][dtype].setdefault(floor_id, 0)
                self.property_info['recover_times'][where][dtype][floor_id] += 1
            else:
                self.property_info['recover_times'][where] += 1
        self.put()

    def get_recover_times(self):
        '''
        * 获取今日可回复次数
        miaoyichao
        '''
        data = {}
        all_dungeon = ['normal','daily','special']
        #获取vip等级
        vip_lv = self.vip_cur_level
        vip_conf = self.game_config.user_vip_config
        user_config = vip_conf.get(str(vip_lv),{})
        today_str = utils.get_today_str()
        recover_list = ['recover_stamina','recover_pvp_stamina','recover_mystery_store']
        recover_times = self.property_info['recover_times']
        if recover_times['today_str'] == today_str:
            for recover in recover_list:
                data[recover] = user_config['can_'+recover+'_cnt'] - recover_times[recover]
            data['recover_copy'] = {}
            for i in all_dungeon:
                data['recover_copy'][i] = user_config['can_recover_copy_cnt'][i]  - recover_times['recover_copy'][i]
        else:
            self.reset_recover_times()
            data = self.property_info['recover_times']
        return data

    def extend_friend_num(self,num):
        """
        扩展用户的好友上限
        miaoyichao
        """
        self.property_info['friend_extend_num'] += num
        self.put()

    def set_newbie(self):
        '''
        设置新手未非新手的标志
        '''
        self.property_info['newbie'] = False
        self.put()

    def set_newbie_steps(self, step, step_name):
        '''
        记录新手引导中的步骤信息
        '''
        step = int(step)
        newbie_step = int(self.property_info['newbie_steps'])

        # 只是处理符合要求的新手引导
        if newbie_step < step:
            self.property_info['newbie_steps'] = step
            #获取系统配置中的新手步骤   也就是走多少步可以认为不是新手
            newbie_steps_num = int(self.game_config.system_config.get('newbie_steps',6))
            step_flag = (1 << (newbie_steps_num - 1)) - 1
            log_data = {"step_name": step_name, "step_id": step, "complete": False}
            # #判断是否需要将新手设置为非新手
            if self.newbie and step_flag <= step:
                log_data["complete"] = True
                self.set_newbie()
            data_log_mod.set_log('NewGuide', self, **log_data)

            # 只要完成最后一步的新手引导完成 就认为不是新手
            
            print "deubg guochen set_newbie", self.uid, "this step", step, "last_step", step_flag, "step_name", step_name, "complete",  log_data["complete"]
            self.put()

    def max_recover(self):
        """检查用户体力是否已满"""
        max_stamina = self.game_config.user_level_config[str(self.lv)]['stamina']
        return self.property_info['stamina'] >= max_stamina
        
    def add_bought_vip_package(self, vip_gift_id):
        self.property_info['has_bought_vip_package'].append(vip_gift_id)
        self.put()
        
    def get_bind_weibo_award(self):
        from apps.models.user_gift import UserGift
        if self.user_base.platform != 'oc' and \
            self.property_info.get('bind_award'):
            self.property_info['bind_award'] = False
            content = utils.get_msg('user', 'bind_award', self)
            award = self.game_config.weibo_config['bind_award']
            user_gift_obj = UserGift.get(self.uid)
            user_gift_obj.add_gift(award,content)
            self.put()

    def add_fight_soul(self, fight_soul, where=""):
        '''
        添加战魂
        '''
        self.property_info["fight_soul"] += fight_soul

        log_data = {'where':where, 'num': fight_soul, "after": self.get_fight_soul}
        data_log_mod.set_log('FightSoulProduct', self, **log_data)

        self.put()

