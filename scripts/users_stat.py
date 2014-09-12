#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
#import pymongo
from pymongo import MongoClient
import os
import datetime,time
cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(cur_dir, ".."))



# from apps.models.user_base import UserBase
MONGO_CONF = {
    'host': '10.161.177.70',
    'port': 27017,
    'db': 'cnmaxstrikedb1a',
    'username': 'cnmaxstrikeuser1a',
    'password': 'cnmaxstrikeuPwd1a&o'
}

auth = "%(username)s:%(password)s@" % dict(username=MONGO_CONF['username'],
                                           password=MONGO_CONF['password'])

host = "mongodb://%(auth)s%(host)s:%(port)s/%(db)s" % \
    dict(auth=auth,
        host=MONGO_CONF['host'],
        port=MONGO_CONF['port'],
        db=MONGO_CONF['db'])
    
max_pool_size = 10
document_class = dict
tz_aware = True

conn = MongoClient(host=host,port=MONGO_CONF['port'],max_pool_size=max_pool_size,\
                          document_class=document_class,tz_aware=tz_aware)

db = conn[MONGO_CONF['db']]
collect = db['userbase']
all_users = collect.find()
print all_users.count()
today = datetime.date.today()-datetime.timedelta(days=1)
today_time = int(time.mktime(today.timetuple()))
today_users = collect.find({'add_time':{'$gte':today_time}})
print today_users
f = open('%s/stat.log' % cur_dir,'w')
f.write("总用户数:%d\n" % all_users.count())
f.write("今天注册用户数:%d\n" % today_users.count())
f.close()

