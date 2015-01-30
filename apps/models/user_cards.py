#!/usr/bin/env python
# encoding: utf-8
"""
user_cards.py
"""
import copy
import datetime
from apps.common.utils import create_gen_id
from apps.models.user_property import UserProperty as UserPropertyMod
from apps.models.user_base import UserBase
#from apps.models.virtual.card import Card as CardMod
from apps.models.user_collection import UserCollection
from apps.common import utils
import time
from apps.models import data_log_mod

from apps.models import GameModel

class UserCards(GameModel):
    """
    用户游戏内部基本信息
    """
    pk = 'uid'
    fields = ['uid','cards','cards_info']

    def __init__(self):
        """初始化用户游戏内部基本信息

        Args:
            uid: 用户游戏ID
            data:游戏内部基本信息
        """
        self.uid = None

        self.cards = {}
        self.cards_info = {}


    @classmethod
    def get_instance(cls,uid):
        obj = super(UserCards,cls).get(uid)
        if obj is None:
            obj = cls._install(uid)
        return obj

    @classmethod
    def _install(cls,uid):
        uc = cls()
        uc.uid = uid
        uc.cards = {}
        uc.cards_info = {
            "cur_deck_index":0,
        }
        uc.cards_info['decks'] = [[{}] * 5] * 5

        #初始化给的武将
        deck_index = 0
        leader = True
        for cid in uc.game_config.user_init_config['init_cards']:
            fg,p1,ucid,is_first = uc.add_card(cid, where='init_cards')
            if deck_index < uc.game_config.system_config['deck_length']:
                if leader:
                    uc.deck[deck_index] = {'ucid':ucid,'leader':1}
                    leader = False
                else:
                    uc.deck[deck_index] = {'ucid':ucid}
                deck_index += 1

        uc.put()
        return uc

    def reset_cards(self):
        self.cards_info["decks"][self.cur_deck_index] = self.cards_info["decks"][1]

        self.put()

    @property
    def deck(self):
        return self.cards_info["decks"][self.cur_deck_index]

    @property
    def decks(self):
        is_put = False
        for deck in self.cards_info['decks']:
            for i, card in enumerate(deck):
                if card != {} and card['ucid'] not in self.cards:
                    deck[i] = {}
                    is_put = True
        if self.cards_info['decks'][self.cur_deck_index] != self.deck:
            self.cards_info['decks'][self.cur_deck_index] = self.deck
            is_put = True
        #检查编队确保有leader
        for deck_index in range(len(self.cards_info['decks'])):
            if self.get_leader(deck_index) == "":
                sub_deck = self.cards_info['decks'][deck_index]
                set_leader = False
                for card in sub_deck:
                    if card.get('ucid',''):
                        card['leader'] = 1
                        set_leader = True
                        break
                if not set_leader:
                    leader_cid = self.get_leader(self.cur_deck_index)
                    if leader_cid:
                        sub_deck[0] = {'ucid':leader_cid,'leader':1}
                is_put = True
        if is_put is True:
            self.put()
        return self.cards_info['decks']

    def get_leader(self,deck_index):
        """
        获取编队leader
        """
        deck = self.cards_info['decks'][deck_index]
        card_ls = [card['ucid'] for card in deck if card.get('leader',0)]
        if card_ls:
            return card_ls[0]
        else:
            return ''

    def get_leader_card(self,deck_index):
        """
        获取编队leader
        miaoyichao
        """
        deck = self.cards_info['decks'][deck_index]
        card_ls = [card for card in deck if card.get('leader',0)]
        if card_ls:
            return card_ls[0]
        else:
            return {}

    @property
    def cur_deck_index(self):
        """
        当前编队的索引
        miaoyichao
        """
        return self.cards_info['cur_deck_index']

    def get_cards(self):
        """
        获得平台UID 对应的用户对象
        miaoyichao
        """
        return copy.deepcopy(self.cards)

    def get_card_info(self,ucid):
        """
        获取用户的卡信息
        Args:
            ucid: 自动生成的卡ID
        miaoyichao
        """
        card_info = copy.deepcopy(self.cards[ucid])
        card_info['card_detail'] = self.game_config.card_config[card_info['cid']]
        return card_info

    def get_card_dict(self,ucid):
        """
        获取用户卡片信息，字典结构
        miaoyichao
        """
        card_info = copy.deepcopy(self.cards[ucid])
        return card_info

    def has_card(self, ucid):
        """判断用户是否有这张卡
        miaoyichao
        """
        return ucid in self.cards

    def set_decks(self, decks):
        """设置5个编队
        """
        self.cards_info['decks'] = decks
        self.put()

    def has_talent(self,ucids):
        '''
        判断是否已经有天赋等级了
        miaoyichao
        '''
        for ucid in ucids:
            if self.cards[ucid].get('talent_lv',0):
                return True
        return False

    def advanced_talent(self, ucid):
        '''
        *天赋进阶
        miaoyichao
        '''

        if not self.cards[ucid].get('talent_lv',''):
            self.cards[ucid]['talent_lv'] = 0
        #天赋进阶前的天赋等级
        before_lv = copy.deepcopy(self.cards[ucid]['talent_lv'])
        #判断和最大天赋等级之间的差距
        max_talent_lv = int(self.game_config.card_config[self.cards[ucid]['cid']]['max_talent_lv'])
        if self.cards[ucid]['talent_lv'] >= max_talent_lv:
            self.cards[ucid]['talent_lv'] = max_talent_lv
        else:
            self.cards[ucid]['talent_lv'] += 1

        #开始记录日志信息
        cid_config = self.game_config.card_config[self.cards[ucid]['cid']]
        log_data = {
            'cid': self.cards[ucid]['cid'],
            'ucid': ucid,
            'before_talent_lv': before_lv,
            'after_talent_lv': self.cards[ucid]['talent_lv'],
            'card_msg': self.cards[ucid],
            'name': cid_config['name'],
            'star': cid_config['star'],
        }

        data_log_mod.set_log('CardTalentUpdate', self, **log_data)
        #日志记录完毕
        self.put()

    def set_cur_deck_index(self, cur_deck_index):
        """
        设置当前编队索引
        miaoyichao
        """
        if cur_deck_index > 9 or cur_deck_index < 0:
            cur_deck_index = 0
        self.cards_info['cur_deck_index'] = cur_deck_index
        self.put()

    def get_cards_num(self):
        """
        获取用户的卡枚数
        """
        return len(self.cards)

    def is_equip_used(self,ucids):
        if not ucids:
            return False
        from apps.models.user_equips import UserEquips
        equips = UserEquips.get(self.uid).equips
        used_by_ucids = [equips[ueid]['used_by'] for ueid in equips if equips[ueid].get('used_by')]
        if set(used_by_ucids)&set(ucids):
            return True
        else:
            return False

    def add_card(self, cid, lv=1, where=""):
        """将得到的卡加入背包中
        args
            cid: string 卡ID
            lv: 卡的等级
            sk_lv: string 卡特技等级
        return:
            bool:True 加入成功，False：超过最大上限，加入失败
            int:现在背包中卡的枚数
            int:用户的上限枚数
            string:卡的自定义ID
            is_first:是否是首次得到该卡片
        """
        ucid,is_first = self.__add_card(cid, int(lv), where=where)
        cid_config = self.game_config.card_config[cid]
        all_cards_num = self.get_cards_num()

        log_data = {
            'where':where,
            'ucid':ucid,
            'card_msg': self.cards[ucid],
            'name': cid_config['name'],
            'star': cid_config['star'],
        }

        data_log_mod.set_log('CardProduct', self, **log_data)
        return True,all_cards_num,ucid,is_first
    
    def __can_get_supercategory(self,where):
        """
        是否可以获取超类型
        """
        if not where:
            return False
        if 'gacha' in where or 'free_multi' in where:
            source_type = 'gacha'
        elif 'dungeon_' in where:
            source_type = 'dungeon'
        elif 'soul_exchange' in where:
            source_type = 'soul_exchange'
        else:
            return False
        supercategory_card_source = self.game_config.gacha_config.get('supercategory_card_source',{})
        if not supercategory_card_source:
            return False
        source_type_time = supercategory_card_source.get(source_type,[])
        if not source_type_time:
            return False
        now_str = utils.datetime_toString(datetime.datetime.now())
        if source_type_time[0] <= now_str <= source_type_time[1]:
            return True
        else:
            return False
        
    def __add_card(self,cid,lv,where=None):
        """
        新加武将
        """
        ucid = create_gen_id()
        is_first = False
        if not self.cards.has_key(ucid):
            clv = lv
            exp_type = self.game_config.card_config[cid].get('exp_type','a')
            #取得卡片的技能ID
            self.cards[ucid] = {
                'cid':cid,
                'lv':clv,
                'exp':self.game_config.card_level_config['exp_type'][exp_type][str(clv)],
                'talent_lv':0,
                'upd_time':int(time.time()),
            }
            is_first = UserCollection.get_instance(self.uid).add_collected_card(cid)
            self.put()
        return ucid,is_first

    def del_card_info(self,ucids,where=None):
        """
        批量删除用户的卡信息
        Args:
            ucid: 自动生成的卡ID
        """
        put_fg = False
        for ucid in ucids:
            if ucid in self.cards:
                card_info = self.cards[ucid]
                cid = card_info['cid']
                #默认只有四星五星的武将
                cid_config = self.game_config.card_config[cid]
                if where:
                    card_msg = {
                        'cid': cid,
                        'ctype': cid_config['ctype'],
                        'lv': card_info['lv'],
                        'exp': self.cards[ucid]['exp'],
                        'name': cid_config['name'],
                        'star': cid_config['star'],
                    }
                    log_data = {
                        'where':where,
                        'ucid':ucid,
                        'card_msg': card_msg,
                    }
                    data_log_mod.set_log('CardConsume', self, **log_data)
                self.cards.pop(ucid)
                put_fg = True
        if put_fg:
            self.put()

    def add_card_exp(self,ucid,exp,where=None):
        """
        增加卡片经验值
        args:
            ucid:卡片的唯一id
            exp:所要增加的经验值
        return:
            {
                'old_exp':原始经验
                'old_lv':原始lv
                'old_attack':原始攻击
                'old_defense':原始防御
                'new_exp':新经验
                'new_lv’：新lv
                'new_attack':新攻击
                'new_defense':新防御
                'max_lv':最大级别
            }
        """
        data = {}
        #获取武将对象
        card_info = self.cards[ucid]
        #加经验
        card_info['exp'] += exp
        #获取用户的等级
        user_lv = UserPropertyMod.get(self.uid).lv
        all_lv = range(card_info['lv'],user_lv + 1)
        #初始化参数
        new_lv = card_info['lv']
        old_lv = card_info['lv']
        cid_config = self.game_config.card_config[card_info['cid']]
        #获取可以升级的最大等级
        for lv in all_lv:
            if lv <= new_lv:
                continue
            if card_info['exp'] >= self.game_config.card_level_config['exp_type'][cid_config['exp_type']][str(lv)]:
                new_lv = lv
            else:
                break
        #判断是否大于用户的当前等级
        if new_lv>=user_lv:
            card_info['exp'] = self.game_config.card_level_config['exp_type'][cid_config['exp_type']][str(user_lv)]
            new_lv = user_lv
        card_info['lv'] = new_lv
        if old_lv < new_lv and where:
            #log message
            card_msg = {
                'cid': card_info['cid'],
                'ctype': cid_config['ctype'],
                'lv': card_info['lv'],
                'exp': card_info['exp'],
                'name': cid_config['name'],
                'star': cid_config['star'],
                'defense': cid_config['defense'],
                'attack': cid_config['attack'],
            }
            log_data = {
                'where':where,
                'ucid':ucid,
                'card_msg': card_msg,
            }
            data_log_mod.set_log('CardUpdate', self, **log_data)
        self.put()
        return data

    @property
    def leader_ucid(self):
        return self.get_leader(self.cur_deck_index)
    
    def lock(self,ucids):
        """
        锁定武将
        """

        for ucid in self.cards:
            if ucid in ucids:
                if not self.cards[ucid].get('lock',False):
                    self.cards[ucid]['lock'] = True
                else:
                    self.cards[ucid]['lock'] = False
        self.put()

    def is_locked(self,ucids):
        """
        ucids中如果有一个被锁定即返回True
        """
        for ucid in ucids:
            if self.cards[ucid].get('lock',False):
                return True
        return False
    
    def is_same_cid(self,cid,ucids):
        '''
        判断ucids是否是和要求的一致
        '''
        for ucid in ucids:
            if self.cards[ucid]['cid'] != cid:
                #只要有一个不一致就返回不一致
                return False
        #默认一致
        return True


    def has_5star_card(self,cards):
        """
        判断是否有五星卡
        """
        for cid in cards:
            if self.game_config.card_config[cid]['star'] == '5':
                return True
        return False 

    def has_card_in_list(self, cards):
        has_cids = [card_info['cid'] for card_info in self.cards.values()]
        return True if set(has_cids) & set(cards) else False

    def has_cards_in_cur_deck(self, cards_lists):
        cur_deck_ucids = [card_info['ucid'] for card_info in self.deck if card_info]
        cur_deck_cards = [self.cards[ucid]['cid'] for ucid in cur_deck_ucids]
        for cards_list in cards_lists:
            if not set(cur_deck_cards) & set(cards_list):
                return False
        return True

    def get_deck_info(self):
        """获得对手的编队信息
        return [{"category": "4","exp": 0,"cid": "1_card","upd_time": 1395231243,"lv": 1,"eid": "","sk_lv": 1,"leader": 1}] * 5
        """
        dlist = []
        for d in self.deck:
            ddict = {}
            if 'leader' in d:
                ddict['leader'] = d['leader']

            if 'ucid' in d:
                ucinfo = self.cards[d['ucid']]
                ddict.update(ucinfo)
                ddict['ucid'] = d['ucid']
                # ddict['talent_lv'] = ucinfo['talent_lv']
            dlist.append(ddict)
        return dlist
