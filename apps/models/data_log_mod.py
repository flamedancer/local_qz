#!/usr/bin/env python
# encoding: utf-8
"""
filename:data_log_mod.py
"""
import datetime
from apps.oclib.model import LogModel
from apps.config.game_config import game_config
from apps.oclib import app as ocapp


ALL_LOG_NAMES = [
    "UserLevelHistory",    # 用户等级  'add_exp', 'old_lv', 'new_lv','old_exp','new_exp', 'where'
    "NewGuide",            # 新手引导 'step_name'  步骤名字,  'step_id', 'complete'  是否完成所有引导
    "LoginRecord",         # 登入记录 'user_lv'  
    "CoinProduct",         # coin产出 'where', 'user_lv', 数量 'num', 产出前数量'before', 产出后总数量'after'
    "CoinConsume",          # 'where', 'num', 'before', 'after'
    "GoldProduct",          # 'where', 'num', 'before', 'after'
    "GoldConsume",          # 'where',  'num', 'before', 'after'
    "MatProduct",           # 'where',  'mat_id', 'sum', 'before', 'after'
    "MatConsume",           # 'where',  'mat_id', 'sum', 'before', 'after'
    "EquProduct",           # 'where',  'equip_dict', 'name'
    "EquConsume",           # 'where',  'equip_dict','name'
    "PropsProduct",         # 'user_lv' 'where', 'num', 'before', 'after'
    "PropsConsume",         # 'user_lv' 'where', 'num', 'before', 'after'
    "CardProduct",          # 'where', 'ucid', 'card_msg'
    "CardConsume",          # 'where', 'ucid', 'card_msg'
    "CardUpdate",           # 武将升级   'ucid', 'card_msg', 'before_lv', 'after_lv'
    "CardTalentUpdate",     # 武将进阶   'card_msg', 'ucid', 'before_lv', 'after_lv'
    "EquUpdate",           # 装备升级   'where', 'eid', 'equip_msg'
    "EquUpgrade",           # 装备升品   'eid', 'old_quality' 升品前的品级, 'new_quality' 升品后的品级, equip_msg'
    "DungeonRecord",        # 打副本记录  'exp_point' 获得经验, 'statament' (start开始/ end结束), 'dungeon_id', 'dungeon_type' 普通/日常/周/特殊, 'card_deck', 'lv'
    "SoulProduct",          # 碎片  'user_lv', 'where','soul_id','num'
    "SoulConsume",          # 碎片  'user_lv', 'where','soul_id','num'
    "HonorProduct",          # 功勋点  'where','before', 'after', 'num'
    "HonorConsume",          # 功勋点  'where','before', 'after', 'num'

    "PvpRecord",            # 实时pvp的结算记录  'winner'  胜者uid,  'loser' 负者uid   end_reason 结束原因
    "Explore",              # 探索   'type' 探索类型 （gold/silver/copper），'cost' 消耗的物品类型， 'cost_num' 消耗的物品数量  'num' 次数
    "MysteryStore",         # 神秘商店购买   'cost' 消耗的物品类型 （coin/fight_soul），'cost_num' 消耗的物品数量  'goods' 购买的商品信息 
    "FightSoulProduct",      # 战魂产出
    "FightSoulConsume",      # 战魂消耗
    "PkStore",             # pk商店购买   'cost_honor' 消耗的荣誉点数，'goods' 购买的商品信息
    "CardExpPoint",        # 武将经验点变化记录   'num' 变化数 为负时表示减少，变化后总数量 'after',   'where'

    #  以下还没用到
    "ChargeRecord",
    "ChargeResultLog",      # 充值行为结果记录  "charge_way","result","oid",'date_time','price'
    "OrderRecord",          # ONECLICK 自己产生的订单记录 ['oid','uid','item_id','createtime']
    "Feed",                 # 发微博回调   'lv', 'platform', 'feed_style'
    "Invite",               # 邀请好友 'inviter','invited'
    
]   


def get_log_model(log_name):
    if log_name in globals():
        return globals()[log_name]
    elif log_name in ALL_LOG_NAMES:
        globals()[log_name] = type(log_name, (DataLogModel,), {})
        return globals()[log_name]


def set_log(log_name, user_model, **argw):
    write_tag = user_model.game_config.system_config.get('log_control')
    if not write_tag:
        return

    base_info = {
        "pid": user_model.user_base.pid,
        "uid": user_model.uid,
        "subarea": user_model.subarea,
        "user_lv": user_model.user_property.lv,
        "date_time": datetime.datetime.now(),
    }
    argw.update(base_info)
    if log_name in globals():
        globals()[log_name].set_log(user_model, argw)

    elif log_name in ALL_LOG_NAMES:
        log_obj = type(log_name, (DataLogModel,), {})()
        log_obj.__dict__.update(argw)
        log_obj.put()


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



class ConfigHistory(LogModel):
    pk = 'date_time'
    fields = ['subarea', 'config_name','username','before_config','after_config','diff','date_time']

    @classmethod
    def set_log(cls,**argw):
        obj = cls()
        obj.date_time = datetime.datetime.now()
        [setattr(obj, k, argw.get(k)) for k in argw]
        obj.put()

        cls.delete_old(keep_num_logs=1000)

    @classmethod
    def delete_old(cls, keep_num_logs=1000):
        '''
        Met problems during sorting via date_time, memory exceeded 32MB.

        So, delete 30-day old logs first, then keep max 1000
        '''
        now = datetime.datetime.now()
        today_morning = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = {'date_time': {'$lt': today_morning - datetime.timedelta(days=30) }}
        ocapp.log_mongo.mongo.db['confighistory'].remove(query)


        logs = ocapp.log_mongo.mongo.db['confighistory'].find({}).sort('date_time', 1)
        if logs.count() > keep_num_logs:
            for log in logs[:-keep_num_logs]:
                log.delete()

    @classmethod
    def log_mongo_find_last_n(cls, query, sort_field='', n=10):
        '''
        find last n elements, sorting via reverse order of sort_key
        '''
#       return app.mongo_store.find(cls, query, **kargs)
        return ocapp.log_mongo.mongo.db['confighistory'].find(query).limit(n).sort(sort_field, -1)




