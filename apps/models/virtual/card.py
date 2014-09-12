# encoding: utf-8

""" class name: Card
"""
import copy
from apps.config.game_config import game_config

class Card(object):
    CARD_TYPE = {'1':u'火' ,'2':u'水' ,'3':u'木','4':u'金','5':u'土'}
    def __init__(self,cid,lv=1, config=None):
        self.cid = cid
        self.lv = lv
        self.card_detail = {}
        self.card_level_detail = {}
        self.game_config = config or game_config


    @classmethod
    def get(cls,cid,lv=1,exp=0,pl_attack=0,pl_hp=0,pl_recover=0, game_config=game_config):
        obj = cls(cid,lv)
        obj.card_detail = copy.deepcopy(game_config.card_config[cid])
        if not exp:
            obj.exp = game_config.card_level_config['exp_type'][obj.exp_type][str(obj.lv)]
        else:
            obj.exp = exp
        return obj

    @classmethod
    def get_from_dict(cls, card_dict, game_config=game_config):
        obj = cls(card_dict['cid'])
        obj.lv = card_dict['lv']
        obj.exp = card_dict['exp']
        obj.card_detail = copy.deepcopy(game_config.card_config[card_dict['cid']])
        return obj

    @property
    def name(self):
        return self.card_detail.get('name')

    @property
    def exp_type(self):
        return self.card_detail.get('exp_type')

    @property
    def ctype(self):
        return self.card_detail.get('ctype')

    @property
    def star(self):
        return self.card_detail.get('star')

    # @property
    # def max_lv(self):
    #     return self.card_detail.get('max_lv',1)

    # @property
    # def next_lv(self):
    #     next_lv = self.lv
    #     all_lv = range(1,self.max_lv + 1)
    #     for lv in all_lv:
    #         if lv <= next_lv:
    #             continue
    #         next_lv = lv
    #         break
    #     return next_lv

    # @property
    # def max_exp(self):
    #     max_exp = self.game_config.card_level_config['exp_type'][self.exp_type][str(self.max_lv)]
    #     return max_exp

    # @property
    # def next_lv_exp(self):
    #     next_lv_exp = self.game_config.card_level_config['exp_type'][self.exp_type][str(self.next_lv)]
    #     return next_lv_exp
