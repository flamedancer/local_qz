#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json 
import pymongo
import os
cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(cur_dir, ".."))
# import apps.settings as settings
import apps.settings_stg as settings
from django.core.management import setup_environ
setup_environ(settings)
import random
from apps.models.gift_code import GiftCode



# from apps.models.user_base import UserBase


mongo_setting = settings.STORAGE_CONFIG[settings.STORAGE_INDEX]['mongodb']

conn = pymongo.Connection(mongo_setting['host'],mongo_setting['port'])

db = conn[mongo_setting['db']]

all_users = db.userbase.find()   #内测参与礼包
level_top_10 = db.userproperty.find().sort('property_info.lv',pymongo.DESCENDING)[:10] # 战狂
gold_top_5 = db.userproperty.find().sort('property_info.gold',pymongo.DESCENDING)[:5] # 战狂
#完成所有章节的
dungeon_config = eval(db.config.find_one({'config_name':'dungeon_config'})['data'])
max_fool = str(max([ int(i) for i in dungeon_config]))
max_room = str(max([ int(i) for i in dungeon_config[max_fool]['rooms']]))
# normal_current
finish_dungeon = db.userdungeon.find({'dungeon_info.normal_current.floor_id':max_fool,'dungeon_info.normal_current.room_id':max_room,'dungeon_info.normal_current.status':2})
#持之以恒
continue_login = db.userlogin.find({'total_login_num':{"$gt":24}})

all_uids = [i['uid']for i in all_users]
level_top_10_uids = [i['uid']for i in level_top_10]
gold_top_5_uids = [i['uid']for i in gold_top_5]
finish_dungeon_uids = [i['uid']for i in finish_dungeon]
continue_login_uids = [i['uid']for i in continue_login]

a = {
    'test_1':dict(zip(all_uids,\
        random.sample(GiftCode.get('test_1').codes,len(all_uids)))),
    'test_2':dict(zip(level_top_10_uids,\
        random.sample(GiftCode.get('test_2').codes,len(level_top_10_uids)))),
    'test_3':dict(zip(gold_top_5_uids,\
        random.sample(GiftCode.get('test_3').codes,len(gold_top_5_uids)))),
    'test_4':dict(zip(finish_dungeon_uids,\
        random.sample(GiftCode.get('test_4').codes,len(finish_dungeon_uids)))),
    'test_5':dict(zip(continue_login_uids,\
        random.sample(GiftCode.get('test_5').codes,len(continue_login_uids)))),
    }

# all_uids = set(reduce(lambda x,y:x+y,a.values()))

user_gift_record = {}
for uid in all_uids:
    user_gift_record[uid] = []
    for gift_id in a:
        if uid in a[gift_id]:
            user_gift_record[uid].append(a[gift_id][uid])

f = file('%s/user_gift_record' % cur_dir,'w')
# json.dumps(a,f)
f.write(json.dumps(user_gift_record))
f.close()

f = file('%s/gift_result.log' % cur_dir,'w')
# json.dumps(a,f)
# f.write(json.dumps(user_gift_record))
a = {
    'level_top_10':[''.join([i['uid'],'lv:',i['property_info']['lv']]) for i in level_top_10],
    'gold_top_5:':[''.join([i['uid'],'lv:',i['property_info']['gold']]) for i in gold_top_5],
    'finish_dungeon':[i['uid'] for i in finish_dungeon],
    'continue_login':[''.join([i['uid'],'total_login_num:',i['login_info']['total_login_num']]) for i in continue_login],
    }

f.write('all_users:sum:%s\r\n' % len(all_users))

f.write('level_top_10:sum:%s' % len(a['level_top_10']))
f.write('level_top_10:%s' % '\r\n'.join(a['level_top_10']))

f.write('gold_top_5:sum:%s' % len(a['gold_top_5']))
f.write('gold_top_5:%s' % '\r\n'.join(a['gold_top_5']))

f.write('finish_dungeon:sum:%s' % len(a['finish_dungeon']))
f.write('finish_dungeon:%s' % '\r\n'.join(a['finish_dungeon']))

f.write('continue_login:sum:%s' % len(a['continue_login']))
f.write('continue_login:%s' % '\r\n'.join(a['continue_login']))

f.close()


