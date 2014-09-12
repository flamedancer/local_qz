#!/usr/bin/env python
# encoding: utf-8
"""
filename:data_log_mod.py
"""
import datetime
from apps.oclib.model import LogModel
from apps.config.game_config import game_config


ALL_LOG_NAMES = [
    "UserLevelHistory",    # 用户等级  d'add_exp', 'old_lv', 'new_lv','old_exp','new_exp','where'
    "NewGuide",            # 新手引导 'step','complete'
    "LoginRecord"          # 登入记录 'user_lv'
    "CoinProduct",         # coin产出 'where', 'user_lv', 数量 'sum', 产出前数量'before', 产出后总数量'after'
    "CoinConsume",          #  'where', 'user_lv', 'sum', 'before', 'after'
    "GoldProduct",          # 'where','user_lv','sum', 'before', 'after'
    "GoldConsume",          # 'where', 'user_lv', 'sum', 'before', 'after'
    "MatProduct",           # 'where', 'user_lv', 'ma_id', 'sum', 'before', 'after'
    "MatConsume",           # 'where', 'user_lv', 'ma_id', 'sum', 'before', 'after'
    "EquProduct",           # 'where', 'user_lv', 'equip_dict', 'name'
    "EquConsume",           # 'where', 'user_lv', 'equip_dict','name'
    "ItemProduct",          # 'user_lv', 'where', 'sum', 'before', 'after'
    "ItemConsume",          # 'user_lv', 'where', 'sum', 'before', 'after'
    "PropsProduct",         # 'user_lv', 'where', 'sum', 'before', 'after'
    "PropsConsume",         # 'user_lv', 'where', 'sum', 'before', 'after'
    "CardProduct",          # 'where', 'ucid', 'card_msg'
    "CardConsume",          # 'where', 'ucid', 'card_msg'
    "CardUpdate",           # 武将升级   'where', 'ucid', 'card_msg'
    "CardTalentUpdate",     # 武将进阶   'card_msg', 'ucid','before_lv','after_lv'
    "DungeonRecord",        # 打副本记录   开始/结束'statament', 'dungeon_id', 普通/日常/周/特殊'dungeon_type', 'card_deck', 'lv'
    "PvpRecord",            # 'statament','card_deck','pvp_pt','pvp_level','user_level', 'renown'
    "Feed",                 # 发微博回调   'lv', 'platform', 'feed_style'
    "Invite",               # 邀请好友 'inviter','invited'
    "ChargeResultLog",      # 充值行为结果记录  "charge_way","result","oid",'date_time','price'
    "SoulProduct",          # 武将碎片  'user_lv', 'where','soul_id','num'
    "SoulConsume",          # 武将碎片  'user_lv', 'where','soul_id','num'
    "ConsumeRecord",
    "ChargeRecord",
    "DLPvpRank",            # pvp的排名信息记录
    "OrderidRecord",        # ONECLICK 自己产生的订单记录 ['oid','uid','item_id','createtime']
]   


def get_log_model(log_name):
    if log_name in globals():
        return globals()[log_name]
    elif log_name in ALL_LOG_NAMES:
        globals()[log_name] = type(log_name, (DataLogModel,), {})
        return globals()[log_name]


def set_log(log_name, user_model, **argw):
    write_tag = game_config.system_config.get('log_control')
    if not write_tag:
        return

    base_info = {
        "uid": user_model.uid,
        "subarea": user_model.subarea,
        "date_time": datetime.datetime.now(),
    }
    argw.update(base_info)
    if log_name in globals():
        globals()[log_name].set_log(user_model, argw)

    elif log_name in ALL_LOG_NAMES:
        type(log_name, (DataLogModel,), argw)().put()


class DataLogModel(LogModel):
    fields = ['uid', 'subarea']

    @classmethod
    def set_log(cls, user_model, argw):
        obj = cls()
        obj.uid = user_model.uid
        obj.subarea = user_model.subarea
        obj.date_time = datetime.datetime.now()
        [setattr(obj, key, argw[key]) for key in argw]
        obj.put()






