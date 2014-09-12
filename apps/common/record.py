#!/usr/bin/env python
# encoding: utf-8
"""
filename:consume_record.py
"""

from apps.models import data_log_mod
from bson.son import SON

ConsumeRecord = data_log_mod.get_log_model("ConsumeRecord")


def get_consume_record(uid,start_date,end_date,consume_type):
    match_query = {}
    if uid:
        match_query['uid'] = uid
    if start_date or end_date:
        match_query['createtime'] = {}
        if start_date:
            match_query['createtime']['$gte'] = '%s 00:00:00' % start_date
        if end_date:
            match_query['createtime']['$lte'] = '%s 23:59:59' % end_date
    if consume_type != 'all':
        match_query['consume_type'] = consume_type
    group_code = {"$group":{ "_id" :{"$substr":["$createtime",0,13]}, "item_sum": { "$sum" : "$num" },"item_count":{"$sum" : 1} }}
    result = ConsumeRecord.aggregate([{"$match":match_query},group_code,{"$sort": SON([("_id", 1)])}])

    return result

def get_charge_record(uid,start_date,end_date,platform,item_id,charge_way=None):
    match_query = {}
    if uid:
        match_query['uid'] = uid
    if platform != 'all':
        match_query['platform'] = platform
    if start_date or end_date:
        match_query['createtime'] = {}
        if start_date:
            match_query['createtime']['$gte'] = '%s 00:00:00' % start_date
        if end_date:
            match_query['createtime']['$lte'] = '%s 23:59:59' % end_date
    if item_id != 'all':
        item_id = item_id.split('.')[-1]
        match_query['item_id'] = {'$regex':item_id}
    if charge_way != None and charge_way != 'all':
        if charge_way == '':
            match_query['charge_way'] = {"$in":['',None]}
        else:
            match_query['charge_way'] = charge_way
    match_query['sandbox'] = {"$in":[None]}
    group_code = {"$group":{ "_id" :{"$substr":["$createtime",0,13]}, "charge_sum": { "$sum" : "$price" },"charge_count":{"$sum" : 1} }}
    result = data_log_mod.get_log_model("ChargeRecord").aggregate([{"$match":match_query},group_code,{"$sort": SON([("_id", 1)])}])
    return result


