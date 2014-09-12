#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 对级别做出如下调整：12月9号
# 第1且达到68级及以上的玩家
# 前100名且达到48级及以上玩家
# 前1000名且达到28级及以上的玩家
# 前1亿名且达到8级及以上的玩家
# 名次按等级排，同等级按时间先后排。

import pymongo
import datetime
from bson.son import SON

#####只读账号log#####
conn = pymongo.Connection('10.161.177.73',27017)
db = conn["logcnmaxstrikedb1a"]
db.authenticate("logcnmaxstrikeuser1aocdata",'logcnmaxstrikeuPW1oa&oCdata')

####只读账号####
# conn = pymongo.Connection('10.161.177.73',27017)
# db = conn["cnmaxstrikedb1a"]
# db.authenticate("cnmaxstrikeuser1aocdata",'cnmaxstrikeuPwD1&aooCdata')
#######################

# db.collection_names()
now = datetime.datetime.now()
match_query = {"date_time":{},'new_lv':{}}
match_query['date_time']['$lte'] = now
match_query['new_lv']['$gte'] = 8
# group_code = {"$group":{ "_id" :{"$substr":["$createtime",0,13]}, "item_sum": { "$sum" : "$num" },"item_count":{"$sum" : 1} }}
group_code = {"$group":{ "_id" :"$uid", "max_lv": { "$max" : "$new_lv" },'max_date_time':{"$max":"$date_time"}}}
result = db.userlevelhistory.aggregate([{"$match":match_query},group_code,{"$sort": SON([("max_lv", -1),("max_date_time",-1)])},{"$limit":1000}])
all_people = len(result['result'])
all_suit_people = {'level_68':[],'level_48':[],'level_28':[],'level_08':[],}

for postion,msg in enumerate(result['result'],1):
    if postion == 1:
        if msg['max_lv'] >= 68:
            all_suit_people['level_68'].append(msg)
            continue
    if postion <= 100:
        if msg["max_lv"] >= 48:
            all_suit_people['level_48'].append(msg)
            continue
    if postion <= 1000:
        if msg['max_lv'] >= 28:
            all_suit_people['level_28'].append(msg)
            continue
    else:
        all_suit_people['level_08'].append(msg)

file_result = file('level_user','w')
for level in  sorted(all_suit_people.keys(),reverse=True):
    file_result.write(level+'\n')
    file_result.write('\n'.join(all_suit_people[level]))
