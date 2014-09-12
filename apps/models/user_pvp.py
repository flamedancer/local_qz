#!/usr/bin/env python
# encoding: utf-8

from apps.models import data_log_mod
import random
import traceback
from apps.models.random_name import Random_Names
from apps.models import pvp_redis
import time
import datetime
from apps.models.pt_users import PtUsers
import copy
from apps.models.user_property import UserProperty
from django.conf import settings
from apps.oclib.model import TopModel
from apps.common.utils import award_return_form
from apps.common import utils
from apps.models.user_marquee import UserMarquee
from apps.models.user_base import UserBase
from apps.models import GameModel
from apps.common.utils import send_exception_mailEx
from apps.models.user_mail import UserMail
from apps.logics import mails

class UserPvp(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid','pvp_info']

    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        pass

    @classmethod
    def get(cls,uid):
        obj = super(UserPvp,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def get_for_self(cls,uid):
        obj = super(UserPvp,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        try:
            obj.update_pvp_stamina()
            obj.pvp_rankaward_by_auto()
            obj.clear_old_rank_record()
        except:
            terror = traceback.format_exc()
            print terror
            send_exception_mailEx()
        return obj

    @classmethod
    def getEx(cls,uid):
        obj = super(UserPvp,cls).get(uid)
        return obj

    @classmethod
    def _install(cls,uid):
        obj = cls.create(uid)
        obj.put()
        return obj

    @classmethod
    def create(cls,uid):
        user_pvp = UserPvp()
        user_pvp.uid = uid
        user_pvp.pvp_info = {
            'base_info':{
                'pt':0,
                'renown': 0,#名声
                'win':0,
                'lose':0,
                'pt_user_lv':1,
                'pvp_level':1,
                'pvp_stamina':user_pvp.max_pvp_stamina,
                'pvp_title':user_pvp.game_config.pvp_config['pvp_level_config']['1']['title'],
                'pvp_stamina_update':int(time.time()),
                'choose_times':0,
                'history_max_rank': 0,
                'pvp_rankaward_gettime': time.strftime('%Y-%m-%d %H', time.localtime(user_pvp.user_base.add_time)),
            },
            'award_record':[],#  到达哪一等级 获得那些奖励。
            'detail_info':{
                'total_win':0,
                'total_lose':0,
                'total_join':0,
                'continue_win':0,
                'defence_continue_win':0,
                'defence_win':0,
                'property_kill':{   #'1'为火，'2'为水，'3'为木，'4'为雷，'5'为阳,'6'为阴
                    '1':0,
                    '2':0,
                    '3':0,
                    '4':0,
                    '5':0,
                    '6':0,
                },
                'star_kill':{'1':0,'2':0,'3':0,'4':0,'5':0},
                    'time_out_win':0,
                    'perfect_win':0,
                    'bb_win':0,
                    'kill_attack':0,
                    'one_bout_max_attack':0,
                    'max_spark_time':0,
                    'total_attack':0,
                    'total_recover':0,
                    'total_spark_time':0,
                    'BB_total_time':0,
                    'total_ABP':0,#累积获得的ABP
                },
            'last':{},
            'arena_opponents_rname': {#每天的随机npc信息
                str(datetime.datetime.now().date()): {},
             },
            'back_uid': '',
            'rank_record': {
            },
        }
        return user_pvp

    @property
    def pvp_detail(self):
        total_join = self.pvp_info['base_info']["win"] + self.pvp_info['base_info']["lose"]
        self.pvp_info['detail_info']['total_join'] = total_join
        self.pvp_info['detail_info']['total_win'] = self.pvp_info['base_info']["win"]
        self.pvp_info['detail_info']['total_lose'] = self.pvp_info['base_info']["lose"]
        self.put()
        return self.pvp_info['detail_info']

    @property
    def pt_level(self):
        return self.pvp_info['base_info']['pt']/self.game_config.pvp_config.get('pt_user_gap',500)

    def add_pt(self,num):
        # pt_user
        old_pt = self.pt
        pvp_level_config = copy.deepcopy(self.game_config.pvp_config['pvp_level_config'])
        max_pvp_level = max([ int(level) for level in pvp_level_config.keys()])
        before_pvp_level = self.pvp_level
        if  self.pvp_info['base_info']['pt'] + num < 0:
            self.pvp_info['base_info']['pt'] = 0
        else:
            self.pvp_info['base_info']['pt'] += num

        now_pt = self.pvp_info['base_info']['pt']
        now_pt_level = self.pt_level
        if now_pt_level != self.pvp_info['base_info']['pt_user_lv']:
            before_pt_users = PtUsers.get_instance(self.pvp_info['base_info']['pt_user_lv'])
            before_pt_users.remove_user(self.uid)
            now_pt_users = PtUsers.get_instance(now_pt_level)
            now_pt_users.add_user(self.uid)
            self.pvp_info['base_info']['pt_user_lv'] = now_pt_level
        # 是否升级
        next_lv = 1
        for i in range(1,max_pvp_level+1):
            if now_pt >= pvp_level_config[str(i)]['pt']:
                next_lv = i
            else:
                break
        self.pvp_info['base_info']['pvp_level'] = next_lv
        up_obj = UserProperty.get(self.uid)
        # 升级奖励
        update_award = {}
        if before_pvp_level != self.pvp_info['base_info']['pvp_level']:

            level_detail = self.game_config.pvp_config['pvp_level_config'][str(self.pvp_info['base_info']['pvp_level'])]
            self.pvp_info['base_info']['pvp_title'] = level_detail['title']
            if before_pvp_level < self.pvp_info['base_info']['pvp_level']:
                #写入跑马灯
                rk_user = UserBase.get(self.uid)
                user_marquee_obj = UserMarquee.get(rk_user.subarea)
                marquee_params = {
                    'type': 'pvp_end',
                    'username': rk_user.username,
                    'pvp_title': level_detail['title'],
                }
                user_marquee_obj.record(marquee_params)

                for i in range(before_pvp_level+1,self.pvp_info['base_info']['pvp_level']+1):
                    if i not in self.pvp_info['award_record']:
                        awards = pvp_level_config[str(i)].get('award',{})
                        if awards:
                            tmp_award = up_obj.give_award(awards)
                            update_award[i] = tmp_award
                        self.pvp_info['award_record'].append(i)

        #累积ABP
        if num > 0:
            self.pvp_info['detail_info']['total_ABP'] += num
        self.put()
#        if old_pt != now_pt:
#            top_model = pvp_redis.get_pvp_redis(self.user_base.subarea)
#            top_model.set(self.uid,self.pt)
        update_award_format = award_return_form(update_award)
        return update_award_format

    @property
    def max_pvp_stamina(self):
        lv = str(self.user_base.user_property.lv)
        mpstamina = self.game_config.user_level_config[lv].get('max_pvp_stamina', 3)
        return mpstamina

    def update_pvp_stamina(self):
        current_stamina = self.pvp_info['base_info']['pvp_stamina']
        if current_stamina >= self.max_pvp_stamina:
            return
        now = int(time.time())
        last_up_time = self.pvp_info['base_info']['pvp_stamina_update']
        if now < last_up_time:
            return
        pvp_recover_inter_time = self.game_config.pvp_config['pvp_recover_inter_time']
        get_stamina = int((now-last_up_time)/(pvp_recover_inter_time*60))
        #只有变了 才更新时间
        pt_fg = False
        if get_stamina > 0:
            if get_stamina + current_stamina > self.max_pvp_stamina:
                self.pvp_info['base_info']['pvp_stamina'] = self.max_pvp_stamina
                self.pvp_info['base_info']['pvp_stamina_update'] = now
            else:
                self.pvp_info['base_info']['pvp_stamina'] = get_stamina + current_stamina
                self.pvp_info['base_info']['pvp_stamina_update'] = int(last_up_time + get_stamina*pvp_recover_inter_time*60)
            pt_fg = True
        if pt_fg:
            self.put()

    @property
    def pvp_stamina(self):
        return self.pvp_info['base_info']['pvp_stamina']

    @property
    def pvp_level(self):
        return self.pvp_info['base_info']['pvp_level']


    def minus_pvp_stamina(self,num=1):
        if self.pvp_stamina > 0:
            if self.pvp_info['base_info']['pvp_stamina'] >= self.max_pvp_stamina:
                self.pvp_info['base_info']['pvp_stamina_update'] = int(time.time())
            self.pvp_info['base_info']['pvp_stamina'] -= num
            self.put()

    def recover_pvp_stamina(self):
        if self.pvp_info['base_info']['pvp_stamina'] < self.max_pvp_stamina:
            self.pvp_info['base_info']['pvp_stamina'] = self.max_pvp_stamina
            self.pvp_info['base_info']['pvp_stamina_update'] = int(time.time())
            self.put()

    @property
    def pt(self):
        return self.pvp_info['base_info']['pt']

    def clear_dungeon(self):
        self.pvp_info['last'] = {}
        self.put()

    def record_pk_result(self,pk_result):
        if pk_result == 'win':
            self.pvp_info['base_info']['win'] += 1
        elif pk_result == 'lose':
            self.pvp_info['base_info']['lose'] += 1
        elif pk_result == 'default_win':
            self.pvp_info['base_info']['lose'] -= 1
            if self.pvp_info['base_info']['lose'] < 0:
                self.pvp_info['base_info']['lose'] = 0
        elif pk_result == 'default_lose':
            self.pvp_info['base_info']['lose'] += 1
        self.put()

    def refresh_choose(self):
        if self.pvp_info['base_info']['choose_times'] > 1000:
            self.pvp_info['base_info']['choose_times'] = 0
            self.put()

    def next_level_pt(self):
        pt_level_config = self.game_config.pvp_config['pvp_level_config']
        max_level = max([ int(i) for i in pt_level_config.keys()])
        if self.pvp_level < max_level:
            return {'next_level_pt':pt_level_config[str(self.pvp_level+1)]['pt'],'current_level_pt':pt_level_config[str(self.pvp_level)]['pt']}
        else:
            return {'next_level_pt':-1,'current_level_pt':-1}
    
    @property
    def pvp_title(self):
        return self.pvp_info['base_info']['pvp_title']
    
    def add_pvp_stamina(self,num):
        self.pvp_info['base_info']['pvp_stamina'] += num
        self.put()

    def pvp_rank(self):
        """返回自己pvp的排行，如果没有则添加最后一名到排行"""
        top_model = pvp_redis.get_pvp_redis(self.user_base.subarea)
        srank = top_model.score(self.uid)
        if srank is None or int(srank) == 0:
            top_model.set(self.uid, top_model.count() + 1)
            log_data = {
                'self_rank': top_model.count()
            }
            data_log_mod.set_log('DLPvpRank', self, **log_data)
        return top_model.score(self.uid)

    def get_arena_opponents(self):
        """获得竞争对手的信息
        '1000': {#排名
            'gold': 10000,#维持该排名可获得的铜钱
            'renown': 300,#维持该排名可获得的声望
            'player_uid': u'9100213353',#对手id
            'user_lv': 4,#玩家等级
            'user_name': u'\u51af\u4fca\u535a',#玩家名字
            "deck": [{#玩家的编队信息
                "category": "4",
                "exp": 0,
                "cid": "1_card",
                "upd_time": 1395231243,
                "lv": 1,
                "eid": "",
                "sk_lv": 1,
                "leader": 1
                }, 
            ],
        }
        """
        data = {}
        #玩家自己的排名
        prank = self.pvp_rank()
        #可挑战对手
        top_model = pvp_redis.get_pvp_redis(self.user_base.subarea)
        #获得可pvp的对手id列表
        arena_opponents_list = top_model.get_arena_opponents_uids(prank)
        #如果对手是npc，则名字将使用今天随机出来的npc名字，这样玩家在看到对手的名字时，不至于一直在变化。
        for i, (opponent_rank, opponent_uid) in enumerate(arena_opponents_list):
            pvp_rank_awards = utils.get_rank_awards_by_rank(opponent_rank)
            awards = pvp_rank_awards['awards']
            opponent_data = data[str(opponent_rank)] = {}
            if "@npc" in opponent_uid:
                #如果是npc则，获得随机好的名字，这些随机的名字一天之内保持一直
                npc_opponets = self.get_npc_opponents(opponent_rank)
                opponent_data['user_name'] = npc_opponets['npc_name']
                opponent_data['player_uid'] = opponent_uid.split("@")[1]
                opponent_data['deck'] = npc_opponets['deck']
                opponent_data['user_lv'] = npc_opponets['npc_lv']
            else:
                opponent_user_base_obj = UserBase.get(opponent_uid)
                opponent_data['user_name'] = opponent_user_base_obj.username
                opponent_data['player_uid'] = opponent_uid
                opponent_data['deck'] = opponent_user_base_obj.user_cards.get_deck_info()
                opponent_data['user_lv'] = opponent_user_base_obj.user_property.lv
                opponent_data['back'] = opponent_user_base_obj.user_pvp.is_back_uid(self.uid)
            opponent_data['gold'] = int(awards['gold'])
            opponent_data['renown'] = awards['renown']
        return data

    def set_pvp_vs_player(self, player_uid):
        """记录下挑战的对手id，在出战场的时候用于验证"""
        if not "last" in self.pvp_info:
            self.pvp_info['last'] = {}
            self.put()
        self.pvp_info['last']['vs_player'] = player_uid
        self.put()

    def get_pvp_vs_player(self):
        """挑战的对手id，在出战场的时候用于验证"""
        return self.pvp_info.get('last', {}).get('vs_player', '')

    def get_renown(self):
        """获得自己的名声"""
        return self.pvp_info.get('base_info', {}).get('renown', 0)

    def get_npc_opponents(self, opponent_rank):
        """获得npc信息"""
        data = {}
        date_str = str(datetime.datetime.now().date())
        if not date_str in self.pvp_info['arena_opponents_rname']:
            self.pvp_info['arena_opponents_rname'] = {date_str: {}}
            self.put()
        date_str = str(datetime.datetime.now().date())
        opponent_rank = str(opponent_rank)
        if not opponent_rank in self.pvp_info['arena_opponents_rname'][date_str]:
            self.pvp_info['arena_opponents_rname'][date_str][opponent_rank] = {
                'npc_name': '',
                'deck': {},
            }
            r = random.random()
            try:
                rname = Random_Names.find({'random' : { '$gte' : r }},limit=1)[0].name
            except:
                rname = 'Lawes'
            self.pvp_info['arena_opponents_rname'][date_str][opponent_rank]['npc_name'] = rname
            pvp_npc_config = self.game_config.pvp_config.get('npc', {})
            odecks = []
            npc = {"category": "4","exp": 0,"cid": "1_card","upd_time": 1395231243,"lv": 1,"eid": "","sk_lv": 1}
            for npc_irank in pvp_npc_config:
                if npc_irank[1] >= int(opponent_rank) >= npc_irank[0]:
                    npcs_lv = pvp_npc_config[npc_irank].get('npcs_lv', [1, 2])
                    npc['npc_lv'] = random.randrange(npcs_lv[0], npcs_lv[1] + 1)
                    self.pvp_info['arena_opponents_rname'][date_str][opponent_rank]['npcs_lv'] = npc['npc_lv']
                    self.put()
                    deck_for_star_index = 'deck%s_for_star'
                    deck_index = 'deck%s'
                    for i in range(1, 6):
                        dfs_index = deck_for_star_index % i
                        d_index = deck_index % i
                        if dfs_index in pvp_npc_config[npc_irank]:
                            star = str(pvp_npc_config[npc_irank][dfs_index])
                            clist = [cid for cid in self.game_config.card_config if self.game_config.card_config[cid].get('star', '1') == star and not self.game_config.card_config[cid].get('category', '') in ['7', '8']]
                        elif d_index in pvp_npc_config[npc_irank]:
                            clist = pvp_npc_config[npc_irank][d_index]
                        try:
                            cid = random.sample(clist, 1)[0]
                        except:
                            cid = "1_card"
                        npc['cid'] = cid
                        npc['category'] = self.game_config.card_config[cid].get('category', '')
                        cards_lv = pvp_npc_config[npc_irank].get('cards_lv', [1, 2])
                        npc['lv'] = random.randrange(cards_lv[0], cards_lv[1] + 1)
                        copy_npc = copy.deepcopy(npc)
                        if not odecks:
                            copy_npc['leader'] = 1
                        odecks.append(copy_npc)
                    break
            if not odecks:
                lender_npc = copy.deepcopy(npc)
                lender_npc['leader'] = 1
                odecks = [lender_npc] + [copy.deepcopy(npc)] * 4
                self.pvp_info['arena_opponents_rname'][date_str][opponent_rank]['npcs_lv'] = 1
                self.put()
            self.pvp_info['arena_opponents_rname'][date_str][opponent_rank]['deck'] = odecks
            self.put()
        data['npc_name'] = self.pvp_info['arena_opponents_rname'][date_str][opponent_rank]['npc_name']
        data['deck'] = self.pvp_info['arena_opponents_rname'][date_str][opponent_rank]['deck']
        data['npc_lv'] = self.pvp_info['arena_opponents_rname'][date_str][opponent_rank]['npcs_lv']
        return data

    def record_pvp_back(self, opponent_uid):
        if not 'back' in self.pvp_info:
            self.pvp_info['back'] = ''
            self.put()
        self.pvp_info['back_uid'] = opponent_uid
        self.put()

    def is_back_uid(self, opponent_uid):
        return self.pvp_info.get('back_uid', '') == opponent_uid

    def set_history_max_rank(self, rank):
        nrank = self.pvp_info['base_info'].get('history_max_rank', 0)
        if nrank == 0 or rank < nrank:
            self.pvp_info['base_info']['history_max_rank'] = rank
            self.put()
            return True
        return False

    def add_renown(self, renown):
        self.pvp_info['base_info']['renown'] += renown
        self.put()

    def pvp_rankaward_by_auto(self):
        """自动生成排名奖励"""
        user_YmdH = self.get_pvp_rankaward_gettime()
        now_YmdH = datetime.datetime.now().strftime('%Y-%m-%d %H')
        now_date = datetime.datetime.now()
        YmdH_rank_dict = {}
        self_pvp_rank = self.pvp_rank()
        if now_YmdH > user_YmdH:
            pvprank_record = mails._get_pvprank_record(self.uid)
            if pvprank_record:
                now_rank = pvprank_record[0][1]
            else:
                now_rank = self_pvp_rank
            for i in range(0, 16)[::-1]:
                now_strftime = (now_date - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
                now_strftime_10 = now_strftime + ' 10'
                now_strftime_22 = now_strftime + ' 22'

                if not pvprank_record:
                    if now_YmdH > now_strftime_22 >= user_YmdH:
                        YmdH_rank_dict[now_strftime_22] = now_rank
                    if now_YmdH > now_strftime_10 >= user_YmdH: 
                        YmdH_rank_dict[now_strftime_10] = now_rank
                else:
                    if now_strftime_10 >= pvprank_record[-1][0]:
                        YmdH_rank_dict[now_strftime_10] = self_pvp_rank
                    if now_strftime_22 >= pvprank_record[-1][0]:
                        YmdH_rank_dict[now_strftime_22] = self_pvp_rank
                    now_rank = pvprank_record[0][1]
                    for YmdH_rank in pvprank_record:
                        YmdH = YmdH_rank[0]
                        now_rank = rank = YmdH_rank[1]
                        if not now_strftime_22 in YmdH_rank_dict:
                            if YmdH >= now_strftime_22 >= user_YmdH:
                                YmdH_rank_dict[now_strftime_22] = now_rank
                        if not now_strftime_10 in YmdH_rank_dict:
                            if YmdH >= now_strftime_10 >= user_YmdH:
                                YmdH_rank_dict[now_strftime_10] = now_rank

        for YmdH in YmdH_rank_dict:
            self.add_rank_record(YmdH, YmdH_rank_dict[YmdH])

    def get_pvp_rankaward_gettime(self):
        """自动获得排名奖励的时间"""
        return self.pvp_info['base_info'].get('pvp_rankaward_gettime', time.strftime('%Y-%m-%d %H', time.localtime(self.user_base.add_time)))

    def update_pvp_rankaward_gettime(self):
        self.pvp_info['base_info']['pvp_rankaward_gettime'] = datetime.datetime.now().strftime('%Y-%m-%d %H')
        self.put()

    def add_rank_record(self, YmdH, rank):
        if not 'rank_record' in self.pvp_info: 
            self.pvp_info['rank_record'] = {}
        # if not YmdH in self.pvp_info['rank_record']:
        #     #发奖励
        #     pvp_rank_awards = utils.get_rank_awards_by_rank(rank)
        #     sid = 'system_%s' % (utils.create_gen_id())
        #     content=u'擂台每日排名奖励\n来自：系统奖励\n%s'%(YmdH)
        #     user_mail_obj = UserMail.hget(self.uid, sid)
        #     user_mail_obj.set_mail(type='system',content=content,award=pvp_rank_awards['awards'],create_time=YmdH)
        #     self.pvp_info['rank_record'][YmdH] = rank
        #     self.update_pvp_rankaward_gettime()
        #     self.put()

    def clear_old_rank_record(self):
        rank_record_list = self.pvp_info['rank_record'].keys()
        now_date = datetime.datetime.now()
        clear_data = (now_date - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        for rank_record in rank_record_list:
            if clear_data > rank_record:
                self.pvp_info['rank_record'].pop(rank_record)
                self.put()
