#coding=utf8
'''
Trying to provide some statistics info about total game users, such as,
    daily/weekly/monthly new registered users,
    daily/weekly/monthly new charged value,
    daily/weekly/monthly consumed coins,
    daily/weekly/monthly login users, 
etc.

Some of these statistics may only generated new report once everyday,
or suggests to run on backup database, not on online database.
'''
from __future__ import division
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from apps.admin.decorators import require_permission
from django.conf import settings
from apps.models.user_dungeon import UserDungeon
from apps.models.user_base import UserBase
from apps.models.user_property import UserProperty
from datetime import datetime, timedelta
from apps.models.user_login import UserLogin
from apps.config.game_config import game_config
from apps.oclib import app as ocapp
from bson.son import SON
from bson.code import Code
import time 
import re, os
from apps.admin.views import unicodecsv
from django.core.servers.basehttp import FileWrapper


from apps.models.data_log_mod import get_log_model
LoginRecord = get_log_model('LoginRecord')
ChargeRecord = get_log_model('ChargeRecord')
CoinConsume = get_log_model('CoinConsume')
DungeonRecord = get_log_model('DungeonRecord')
PvpRecord = get_log_model('PvpRecord')
EquProduct = get_log_model('EquProduct')
ItemProduct = get_log_model('ItemProduct')
CoinProduct = get_log_model('CoinProduct')


def sort_dungeon_level( floor_room ):
    ''' This is the key function to sort dungeon levels.
        [ (floor_id, room_id), ... ]
    '''
    floor, room = floor_room
    return int(floor) * 10000 + int(room)

def sort_dungeon_type_level( dtype_floor_room ):
    ''' This is the key function to sort dungeon levels.
        [ 'normal: 10_5', 'special: 3_2', 'weekly: 2_5', ... ]
    '''

    weight = {'normal:': 1, 'weekly:':3, 'special:':2, }

    dtype, floor_room = dtype_floor_room.split()
    floor, room = floor_room.split('_')

    if dtype not in weight:
        return 0
    elif floor == None or room == None:
        return 0
    else:
        return weight[dtype]*1000000000 + int(floor) * 1000 + int(room)



def sort_by_first_int( aStr ):
    ''' This is the key function to sort 
        [ '10_equip', '2_equip', ... ]
    '''
    return int( aStr.split('_')[0] )



@require_permission
def index(request):
    """
    Daily login count ?
    """

    now = datetime.now()
    today_morning = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_morning_ts = time.mktime( today_morning.timetuple() )

    #for monthly statistics
    year_ago = ( today_morning - timedelta(days=365) ).replace(day=1)
    if year_ago < today_morning.replace(year=2014, month=8, day=1):
        #uq started online in 2014-08
        year_ago = today_morning.replace(year=2014, month=8, day=1)


    login_users = {}
    register_users = {}
    daily_charge_sum= {}
    daily_charge_count= {}
    daily_charge_unique_users = {}
    left_rate = {}

    all_users_level = request.GET.get('all_users_level', '')
    yesterday_users_level = request.GET.get('yesterday_users_level', '')
    register_users_charge = request.GET.get('register_users_charge', '')
    charge_users_ratio = request.GET.get('charge_users_ratio', '')



########################### weekly ############
    weekly_users_charges = request.GET.get('weekly_users_charges', '')
    if weekly_users_charges:
        for iDay in range(7):
            #user logins 
            #run on production/online database
            results = LoginRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=iDay) ),
                        '$lt': (today_morning - timedelta(days=(iDay-1) ) ) } } },  
                    {'$group': {'_id': '$uid'} },
                    {"$sort": SON([("_id", 1)]) }
                    ])
            login_users[ (now - timedelta(days=iDay) ).date() ] = len(results)

            #user register time
            results = UserBase.mongo_find( 
                    {'baseinfo.add_time': {
                        '$gte': (today_morning_ts - iDay*24*3600),
                        '$lt': (today_morning_ts - (iDay-1)*24*3600) } },  
                    fields={ 'baseinfo.add_time': 1, 'uid': 1 }
                )
            register_users[ (now - timedelta(days=iDay) ).date() ] = len(results)


            #run on production/online database
            results = ChargeRecord.aggregate([
                    {'$match': {'createtime': {
                        '$gte': str(today_morning - timedelta(days=iDay)),
                        '$lt': str(today_morning - timedelta(days=(iDay-1) ) ) } } 
                        },  
                    {'$group': {'_id': {"$substr":["$createtime",0,10]},
                                "charge_sum": { "$sum" : "$price" },
                                "charge_count":{"$sum" : 1}} 
                        },
                    {"$sort": SON([("_id", 1)]) }
                    ])

            #print '#### charge_results=', results
            if results: #can be []
                daily_charge_sum[ (now - timedelta(days=iDay) ).date() ] = results[0]['charge_sum']
                daily_charge_count[ (now - timedelta(days=iDay) ).date() ] = results[0]['charge_count']
            else:
                daily_charge_sum[ (now - timedelta(days=iDay) ).date() ] = 0
                daily_charge_count[ (now - timedelta(days=iDay) ).date() ] = 0


            #charge unique users
            results = ChargeRecord.aggregate([
                {'$match': {'createtime': { 
                    '$gte': str(today_morning - timedelta(days=iDay)),
                    '$lt': str(today_morning - timedelta(days=(iDay-1) ) ) } } 
                    },  
                {'$group': {'_id': { 'day': {"$substr":["$createtime",0,10]},
                            'uid': '$uid'},
                            } 
                    },
                {'$group': {'_id': "$_id.day",
                            "users":{"$sum" : 1}} } ,
                {"$sort": SON([("_id", 1)]) }
                ])

            if results: #can be []
                daily_charge_unique_users[ (now - timedelta(days=iDay) ).date() ] = results[0]['users']



        for iDay in range(7):
            try:
                left_rate[ (now - timedelta(days=iDay) ).date() ] = (login_users[ (now - timedelta(days=iDay) ).date() ]-register_users[ (now - timedelta(days=iDay) ).date()])/\
                                                                    login_users[ (now - timedelta(days=iDay+1) ).date()]
            except:
                left_rate[ (now - timedelta(days=iDay) ).date() ] = 'no_include'

        weekday_names = {}
        for iDay in range(7):
            weekday_names[(now - timedelta(days=iDay) ).date()] =  (now - timedelta(days=iDay) ).strftime('%a')


        return render_to_response('statistics/weekly_users_charges.html', 
            {'login_users': login_users,
             'register_users': register_users,
             'daily_charge_sum': daily_charge_sum,
             'daily_charge_sum_rmb': dict( [ (aDate, int(daily_charge_sum[aDate] * 0.06)) for aDate in daily_charge_sum ] ),
             'daily_charge_count': daily_charge_count,
             'daily_charge_unique_users': daily_charge_unique_users,
             'left_rate': left_rate,
             'weekday_names': weekday_names,
             },

            RequestContext(request) )



########################### monthly ############
    monthly_login_charges = request.GET.get('monthly_login_charges', '')
    if monthly_login_charges:
        #user logins 
        #run on production/online database
        results = LoginRecord.aggregate([
                {'$match': {'date_time': { '$gte': year_ago } } },  
                {'$group': {'_id': {'uid':'$uid', 
                            'year': {'$year': '$date_time'},
                            'month': {'$month': '$date_time'} } } },
                {'$group': {'_id': { 'year': '$_id.year',
                                     'month': '$_id.month'},
                            'users': {'$sum': 1} } },
                {"$sort": SON([("_id", 1)]) }
                ])


        monthly_login_users = {}
        if results: #can be []
            for row in results:
                monthly_login_users[ str(row['_id']['year']) + '-' + ('%02d' % row['_id']['month']) ] = row['users']



        #run on production/online database
        results = ChargeRecord.aggregate([
                {'$match': {'createtime': { '$gte': str(year_ago) } } },  
                {'$group': {'_id': {"$substr":["$createtime",0,7]},
                            "charge_sum": { "$sum" : "$price" },
                            "charge_count":{"$sum" : 1}} 
                    },
                {"$sort": SON([("_id", 1)]) }
                ])

        monthly_charge_value = {}
        monthly_charge_value_rmb = {}
        monthly_charge_count = {}
        if results: #can be []
            for row in results:
                monthly_charge_value[ row['_id'] ] = row['charge_sum']
                monthly_charge_value_rmb[ row['_id'] ] = int(row['charge_sum']*0.06)
                monthly_charge_count[ row['_id'] ] = row['charge_count']


        #### monthly charge unique users
        results = ChargeRecord.aggregate([
                {'$match': {'createtime': { '$gte': str(year_ago) } } },  
                {'$group': {'_id': { 'month': {"$substr":["$createtime",0,7]},
                            'uid': '$uid'},
                            } 
                    },
                {'$group': {'_id': "$_id.month",
                            "users":{"$sum" : 1}} } ,
                {"$sort": SON([("_id", 1)]) }
                ])
        monthly_charge_unique_users = {}
        if results: #can be []
            for row in results:
                monthly_charge_unique_users[ row['_id'] ] = row['users']


        return render_to_response('statistics/monthly_login_charges.html', 
            {'monthly_login_users': monthly_login_users,
             'monthly_charge_value': monthly_charge_value,
             'monthly_charge_value_rmb': monthly_charge_value_rmb,
             'monthly_charge_count': monthly_charge_count,
             'monthly_charge_unique_users': monthly_charge_unique_users,
             },

            RequestContext(request) )





########################### download monthly charge list ############
    download_monthly_charge_list = request.GET.get('download_monthly_charge_list', '')
    if download_monthly_charge_list:
        year_month = request.GET.get('year_month')
        year, month = year_month.strip().split('-')
        year, month = int(year), int(month)

        #timedelta can't do month=1
        if month == 12:
            next_month = 1
            next_year = year+1
        else:
            next_year = year
            next_month = month+1

        month_start = today_morning.replace(year=year, month=month, day=1)
        next_month_start = month_start.replace(year=next_year, month=next_month)

        results = ChargeRecord.mongo_find({
                    'createtime': { 
                        '$gte': str(month_start),
                        '$lt': str(next_month_start),
                    } },
                    fields={'uid':1, 'price': 1, 'createtime':1 }
                    )

        rows = [ ['User ID', 'Price', 'Time'] ]
        if results: #can be []
            #print '#### monthly charge result[0]=', results[0]
            for row in results:
                rows += [ [row.uid, row.price, row.createtime] ]

        file_full_name = settings.STATIC_ROOT + '/monthly_charges.csv'
        f= open(file_full_name, 'w')
        writer = unicodecsv.writer(f, encoding='utf-8')
        writer.writerows(rows)
        f.close()

        # download
        wrapper = FileWrapper(file(file_full_name))
        response = HttpResponse(wrapper, content_type='application/csv')
        response['Content-Length'] = os.path.getsize(file_full_name)
        response['Content-Disposition'] = 'attachment; filename=monthly_charges.csv'
        return response





##########################################################
    #user level statistics    
    if all_users_level:
        level_stat = {}
        results = UserProperty.mongo_find( {},
                fields={ 'property_info.lv': 1, 'uid': 1 }
                )
        for r in results:
            n = int( r.property_info['lv'] / 10 )
            if n not in level_stat:
                level_stat[n] = 1
            else:
                level_stat[n] += 1

        total_users = sum(level_stat.values())



        #Weekly charge statistics by level
        results = ChargeRecord.mongo_find( {'createtime': 
                {'$gte': str( today_morning - timedelta(days=7) ) } },
                fields={ 'lv': 1, 'price':1, } )

        charge_amounts = {}
        charge_counts = {}
        for r in results:
            n = int( r.lv / 10 )
            if n not in charge_counts:
                charge_counts[n] = 1
                charge_amounts[n] = r.price
            else:
                charge_counts[n] += 1
                charge_amounts[n] += r.price


        total_level_spans = sorted( list( set(level_stat.keys() )  )  )
        level_span_names = {}

        charge_amounts_per_user = {}
        charge_counts_per_user = {}

        for n in total_level_spans:
            level_span_names[n] = str(n*10) + ' - ' + str(n*10+9)
            if n not in charge_amounts:
                charge_amounts[n] = 0
            if n not in charge_counts:
                charge_counts[n] = 0

            charge_counts_per_user[n] = float(charge_counts[n]) / level_stat[n] 
            charge_amounts_per_user[n] = charge_amounts[n] / level_stat[n]

        return render_to_response('statistics/all_users_level.html', 
            {
             'level_stat': level_stat,
             'total_level_spans': total_level_spans,
             'level_span_names': level_span_names,
             'total_users': total_users,
             'charge_counts': charge_counts,
             'charge_amounts': charge_amounts,
             'charge_counts_per_user': charge_counts_per_user,
             'charge_amounts_per_user': charge_amounts_per_user,
             },

            RequestContext(request) )




######################################################################
    #yesterday logged-in users' level distribution
    if yesterday_users_level:
        level_users = {}
        results = LoginRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': today_morning } } },  
                    {'$group': {'_id': '$uid', "level":{"$max" : "$user_lv"} } },
                    {'$group': {'_id': '$level', "count": {"$sum" : 1} } },
                    {"$sort": SON([("_id", 1)]) }
                    ])
        if len(results) > 0:
            for l in results:
                level_users[ l['_id'] ] = l['count']

        return render_to_response('statistics/yesterday_users_level.html', 
            { 'level_users': level_users,
             },
            RequestContext(request) )



#################################################################
    if register_users_charge:
        for iDay in range(7):
            #user register time
            results = UserBase.mongo_find( 
                    {'baseinfo.add_time': {
                        '$gte': (today_morning_ts - iDay*24*3600),
                        '$lt': (today_morning_ts - (iDay-1)*24*3600) } },  
                    fields={ 'baseinfo.add_time': 1, 'uid': 1 }
                )
            register_uids= [ l.uid for l in results ]
            register_users[ (now - timedelta(days=iDay) ).date() ] = len(register_uids)


            #run on production/online database
            results = ChargeRecord.aggregate([
                    {'$match': {'createtime': {
                        '$gte': str(today_morning - timedelta(days=iDay)),
                        '$lt': str(today_morning - timedelta(days=(iDay-1) ) )},
                      'uid': {'$in': register_uids} 
                      } 
                    },  
                    {'$group': {'_id': {"$substr":["$createtime",0,10]},
                                "charge_sum": { "$sum" : "$price" },
                                "charge_count":{"$sum" : 1}} 
                        },
                    {"$sort": SON([("_id", 1)]) }
                    ])

            #print '#### charge_results=', results
            if results: #can be []
                daily_charge_sum[ (now - timedelta(days=iDay) ).date() ] = results[0]['charge_sum']
                daily_charge_count[ (now - timedelta(days=iDay) ).date() ] = results[0]['charge_count']
            else:
                daily_charge_sum[ (now - timedelta(days=iDay) ).date() ] = 0
                daily_charge_count[ (now - timedelta(days=iDay) ).date() ] = 0


        return render_to_response('statistics/register_users_charge.html', 
            {
             'register_users': register_users,
             'daily_charge_sum': daily_charge_sum,
             'daily_charge_count': daily_charge_count,
            },
            RequestContext(request) )


##################################################################
    if charge_users_ratio:
        charge_ratio = {}
        charge_users = {}
        for iDay in range(7):
            results = LoginRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=iDay) ),
                        '$lt': (today_morning - timedelta(days=(iDay-1)) ),
                        } } },  
                    {'$group': {'_id': '$uid'} },
                    {"$sort": SON([("_id", 1)]) }
                    ])
            #print '#### login users results=', results
            if len(results) > 0:
                login_users[ (now - timedelta(days=iDay) ).date() ] = len(results)
            else: 
                login_users[ (now - timedelta(days=iDay) ).date() ] = 0

            #run on production/online database
            results = ChargeRecord.aggregate([
                    {'$match': {'createtime': {
                        '$gte': str(today_morning - timedelta(days=iDay)),
                        '$lt': str(today_morning - timedelta(days=(iDay-1) ) )},
                      } 
                    },  
                    {'$group': {'_id': "$uid"} },
                    {"$sort": SON([("_id", 1)]) }
                    ])

            #print '#### charge results=', results
            if results: #can be []
                charge_users[ (now - timedelta(days=iDay) ).date() ] = len(results)
            else:
                charge_users[ (now - timedelta(days=iDay) ).date() ] = 0

            if login_users[ (now - timedelta(days=iDay) ).date() ] == 0:
                charge_ratio[ (now - timedelta(days=iDay) ).date() ] = 0
            else:
                charge_ratio[ (now - timedelta(days=iDay) ).date() ] =  (
                    charge_users[ (now - timedelta(days=iDay) ).date() ] * 1./ 
                    login_users[ (now - timedelta(days=iDay) ).date() ] )



        return render_to_response('statistics/charge_users_ratio.html', 
            {
             'charge_users': charge_users,
             'login_users': login_users,
             'charge_ratio': charge_ratio,
            },
            RequestContext(request) )




############################################################################
    dungeon_level_users = request.GET.get('dungeon_level_users', '')
    if dungeon_level_users:
#       for iDay in range(7):
        floors = game_config.normal_dungeon_config.keys()
#       floors.sort(key=int)
        floor_rooms = {}
        for f in floors:
            floor_rooms[f] = game_config.normal_dungeon_config[f]['rooms'].keys()
#           floor_rooms[f].sort(key=int)

        dlevel_users ={}
        results = UserDungeon.aggregate([
#                   { '$match': {} },
#                       '$match': {'date_time': {
#                       '$gte': (today_morning - timedelta(days=iDay) ),
#                       '$lt': (today_morning - timedelta(days=(iDay-1)) ),
#                       } } },  
                    {'$group': {
                        '_id': {'floor_id': '$dungeon_info.normal_current.floor_id',
                            'room_id': '$dungeon_info.normal_current.room_id' },
                        "users":{"$sum" : 1}
                        } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### dungeon level users results=', results
        if len(results) > 0:
            for d in results:
                dlevel_users[ (d['_id']['floor_id'], d['_id']['room_id']) ] = d['users']
            for f in floors:
                for r in floor_rooms[f]:
                    if (f, r) not in dlevel_users:
                        dlevel_users[ (f, r) ] = 0

        dlevel_users_keys = dlevel_users.keys()
        dlevel_users_keys.sort(key=sort_dungeon_level)


        #Yesterday Login Users'
        results = LoginRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': today_morning } } },  
                    {'$group': {'_id': '$uid'} },
                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '### yesterday login results=', results
        yesterday_login_uids = [ r['_id'] for r in results ]
        #print '### yesterday login uids=', yesterday_login_uids

        yesterday_dlevel_users ={}
        results = UserDungeon.aggregate([
                    {'$match': {'uid': {'$in': yesterday_login_uids} } },
                    {'$group': {
                        '_id': {'floor_id': '$dungeon_info.normal_current.floor_id',
                            'room_id': '$dungeon_info.normal_current.room_id' },
                        "users":{"$sum" : 1}
                        } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### dungeon level users results=', results
        if len(results) > 0:
            for d in results:
                yesterday_dlevel_users[ (d['_id']['floor_id'], d['_id']['room_id']) ] = d['users']

        for k in dlevel_users_keys:
            if k not in yesterday_dlevel_users:
                yesterday_dlevel_users[k] = 0

        yesterday_login_users = sum(yesterday_dlevel_users.values())
        all_login_users = sum(dlevel_users.values())




        
        #Yesterday Registered Users'
        results = UserBase.mongo_find( 
                    {'baseinfo.add_time': {
                        '$gte': (today_morning_ts - 24*3600),
                        '$lt': today_morning_ts } },  
                    fields={'baseinfo.add_time':1, 'uid': 1 }
                )
        yesterday_register_uids = [l.uid for l in results]
        print '### yesterday_register_uids=', yesterday_register_uids


        yesterday_register_users_stat ={}
        results = UserDungeon.aggregate([
                    {'$match': {'uid': {'$in': yesterday_register_uids} } },
                    {'$group': {
                        '_id': {'floor_id': '$dungeon_info.normal_current.floor_id',
                            'room_id': '$dungeon_info.normal_current.room_id' },
                        "users":{"$sum" : 1}
                        } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### dungeon level users results=', results
        if len(results) > 0:
            for d in results:
                yesterday_register_users_stat[ (d['_id']['floor_id'], d['_id']['room_id']) ] = d['users']


        for k in dlevel_users_keys:
            if k not in yesterday_register_users_stat:
                yesterday_register_users_stat[k] = 0

        total_yesterday_register_users = sum(yesterday_register_users_stat.values())




        return render_to_response('statistics/dungeon_level_users.html', 
            {
             'dungeon_level_users': dlevel_users,
             'dlevel_users_keys': dlevel_users_keys,
             'all_login_users': all_login_users,

             'yesterday_dlevel_users': yesterday_dlevel_users,
             'yesterday_login_users': yesterday_login_users,

             'yesterday_register_users_stat': yesterday_register_users_stat,
             'total_yesterday_register_users': total_yesterday_register_users,
            },
            RequestContext(request) )


############################################################################
    coins_consumed = request.GET.get('coins_consumed', '')
    if coins_consumed:
        results = CoinConsume.aggregate([
                    { 
                        '$match': {'createtime': {
                            '$gte': str(today_morning - timedelta(days=7) )[:19],
                            '$lt': str(today_morning - timedelta(days=0) )[:19],
                        } } },  
                    {'$group': {
                        '_id': { 'date': { "$substr":["$createtime",0,10] },
                            'consume_type': '$consume_type'},
                        'total':{'$sum' : '$num' },
                        } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### consume results=', results

        coins_by_date = {}
        for row in results:
            if row['_id']['date'] not in coins_by_date:
                coins_by_date[ row['_id']['date'] ] = {}
            if row['_id']['consume_type'] not in coins_by_date[ row['_id']['date'] ]:
                coins_by_date[ row['_id']['date'] ][ row['_id']['consume_type'] ] = row['total']


        results = CoinConsume.aggregate([
                    { 
                        '$match': {'createtime': {
                            '$gte': str(today_morning - timedelta(days=7) )[:19],
                            '$lt': str(today_morning - timedelta(days=0) )[:19],
                        } } },  
                    {'$group': {
                        '_id': { 'date': { "$substr":["$createtime",0,10] },
                            'consume_type': '$consume_type', 'uid': '$uid'},
                        } }, 
                    {'$group': {
                        '_id': { 'date': "$_id.date",
                            'consume_type': '$_id.consume_type' }
                        , 'users': {'$sum' : 1},
                        } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### coins_consumed, users results=', results

        users_by_date = {}
        for row in results:
            if row['_id']['date'] not in users_by_date:
                users_by_date[ row['_id']['date'] ] = {}
            if row['_id']['consume_type'] not in users_by_date[ row['_id']['date'] ]:
                users_by_date[ row['_id']['date'] ][ row['_id']['consume_type'] ] = row['users']


        #print '#### consume users_by_date=', users_by_date
        data_dict = {
            'coins_by_date': coins_by_date,
            'users_by_date': users_by_date,
        }

        return render_to_response('statistics/coin_consumed.html', 
            data_dict,
            RequestContext(request) )



############################ revive statistics ##################
    revive_stat = request.GET.get('revive_stat', '')
    if revive_stat:
        revive_date = request.GET.get('revive_date', '')
        days_delta = 0
        if revive_date:
            year, month, day = revive_date.split('-')
            revive_datetime = today_morning.replace(year=year, month=month, 
                                day=day)
            days_delta = (now - revive_datetime).days

        #### yesterday 
        revive_coins_consume = {}
        results = CoinConsume.aggregate([
                    { 
                        '$match': {'date_time': {
                            '$gte': (today_morning - timedelta(days=1) ),
                            '$lt': (today_morning - timedelta(days=0) ),
                                },
                            'where': {'$regex': 'revive*'},
                        } },  
                    {'$group': {
                        '_id': '$where',
                        'total':{'$sum' : '$sum' },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### revive results=', results
        for row in results:
            k = row['_id']
            if row['_id'].count('_') == 3:
                keys = row['_id'].split('_')
                k = keys[-1] + ': ' + keys[1] + '_' + keys[2]
            revive_coins_consume[ k ] = row['total']
        revive_coins_total = sum(revive_coins_consume.values())


        ####### yesterday
        revive_users = {}
        results = CoinConsume.aggregate([
                    { 
                        '$match': {'date_time': {
                            '$gte': (today_morning - timedelta(days=1) ),
                            '$lt': (today_morning - timedelta(days=0) ),
                                },
                            'where': {'$regex': 'revive*'},
                        } },  
                    {'$group': {
                        '_id': {'where':'$where', 'uid':'$uid'},
                       } }, 
                    {'$group': {
                        '_id': '$_id.where',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### revive results=', results

        for row in results:
            k = row['_id']
            if row['_id'].count('_') == 3:
                keys = row['_id'].split('_')
                k = keys[-1] + ': ' + keys[1] + '_' + keys[2]
            revive_users[ k ] = row['users']
        revive_users_total = sum(revive_users.values())



        ############################ all users/logs in Mongo
        all_revive_coins_consume = {}
        results = CoinConsume.aggregate([
                    { 
                        '$match': {
                            'where': {'$regex': 'revive*'},
                        } },  
                    {'$group': {
                        '_id': '$where',
                        'total':{'$sum' : '$sum' },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### revive results=', results
        for row in results:
            k = row['_id']
            if row['_id'].count('_') == 3:
                keys = row['_id'].split('_')
                k = keys[-1] + ': ' + keys[1] + '_' + keys[2]
            all_revive_coins_consume[ k ] = row['total']
        all_revive_coins_total = sum(all_revive_coins_consume.values())



        all_dungeon_levels = []
        for floor, v in game_config.normal_dungeon_config.items():
            for room in v['rooms'].keys():
                all_dungeon_levels += [ 'normal: ' + floor + '_' + room ]
        for floor, v in game_config.special_normal_dungeon_config.items():
            for room in v['rooms'].keys():
                all_dungeon_levels += [ 'special: ' + floor + '_' + room ]
        for floor, v in game_config.weekly_normal_dungeon_config.items():
            for room in v['rooms'].keys():
                all_dungeon_levels += [ 'weekly: ' + floor + '_' + room ]

        all_dungeon_levels_sorted = all_dungeon_levels
        all_dungeon_levels_sorted.sort( key=sort_dungeon_type_level)


        #################### all users
        all_revive_users = {}
        results = CoinConsume.aggregate([
                    { 
                     '$match': {
                            'where': {'$regex': 'revive*'},
                        } },  
                    {'$group': {
                        '_id': {'where':'$where', 'uid':'$uid'},
                       } }, 
                    {'$group': {
                        '_id': '$_id.where',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        for row in results:
            k = row['_id']
            if row['_id'].count('_') == 3:
                keys = row['_id'].split('_')
                k = keys[-1] + ': ' + keys[1] + '_' + keys[2]
            all_revive_users[ k ] = row['users']
        all_revive_users_total = sum(all_revive_users.values())




        all_dungeon_levels_sorted = all_dungeon_levels
        #for dlevel in all_revive_users.keys():
        for dlevel in all_dungeon_levels_sorted:
            if dlevel not in all_revive_users:
                all_revive_users[dlevel] = 0
            if dlevel not in revive_users:
                revive_users[dlevel] = 0
            if dlevel not in revive_coins_consume:
                revive_coins_consume[dlevel] = 0
            if dlevel not in all_revive_coins_consume:
                all_revive_coins_consume[dlevel] = 0



        #### yesterday login users
        level_users = {}
        results = LoginRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': today_morning } } },  
                    {'$group': {'_id': '$uid'} },
                    {"$sort": SON([("_id", 1)]) }
                    ])
        if len(results) > 0:
            yesterday_login_uids = [ l['_id'] for l in results ]

        ### yesterday login users' max level
        yesterday_login_users_level ={}
        results = UserDungeon.aggregate([
                    {
                      '$match': {'uid': {'$in': yesterday_login_uids} }
                        },  
                    {'$group': {
                        '_id': {'floor_id': '$dungeon_info.normal_current.floor_id',
                            'room_id': '$dungeon_info.normal_current.room_id' },
                        "users":{"$sum" : 1}
                        } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### dungeon level users results=', results
        if len(results) > 0:
            for d in results:
                yesterday_login_users_level[ 'normal: ' + str(d['_id']['floor_id']) + '_' + str(d['_id']['room_id']) ] = d['users']

        #set None to 0
        yesterday_login_users_total = 0
        for dlevel in all_dungeon_levels_sorted:
            if dlevel[:7] != 'normal:':
                continue
            if dlevel in yesterday_login_users_level:
                yesterday_login_users_total += yesterday_login_users_level[dlevel]
                continue
            yesterday_login_users_level[dlevel] = 0


        #### yesterday Weekly/Special dungeon unique users
        results = DungeonRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': today_morning },
                        'statament': 'end',
                        'dungeon_type': {'$in' : ['special', 'weekly']},
                        } },  
                    {'$group': {'_id': {
                        'dungeon_type':'$dungeon_type', 
                        'dungeon_id':'$dungeon_id',  
                        'uid':'$uid'} }
                        },

                    {'$group': {'_id': {
                        'dungeon_type':'$_id.dungeon_type', 
                        'dungeon_id':'$_id.dungeon_id',  
                        },
                        'users': {'$sum': 1} }
                        },

                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### DungeonRecord special, weekly =', results

        yesterday_special_weekly_users = {}
        for row in results:
            yesterday_special_weekly_users[ row['_id']['dungeon_type'] + ': ' +
                    row['_id']['dungeon_id'] ]= row['users']



        #### yesterday Weekly/Special dungeon unique users
        results = DungeonRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': today_morning },
                        'statament': 'end',
                        'dungeon_type': {'$in' : ['special', 'weekly']},
                        } },  

                    {'$group': {'_id': {
                        'dungeon_type':'$dungeon_type', 
                        'dungeon_id':'$dungeon_id',  
                        },
                        'times': {'$sum': 1} }
                        },

                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### DungeonRecord special, weekly =', results

        yesterday_special_weekly_times = {}
        for row in results:
            yesterday_special_weekly_times[ row['_id']['dungeon_type'] + ': ' +
                    row['_id']['dungeon_id'] ]= row['times']


        for dlevel in all_dungeon_levels_sorted:
            if dlevel not in yesterday_special_weekly_times:
                yesterday_special_weekly_times[dlevel] = 0
            if dlevel not in yesterday_special_weekly_users:
                yesterday_special_weekly_users[dlevel] = 0


        data_dict = {
            'revive_coins_consume': revive_coins_consume,
            'revive_coins_total': revive_coins_total,
            'revive_users': revive_users,
            'revive_users_total': revive_users_total,

            'all_revive_coins_consume': all_revive_coins_consume,
            'all_revive_coins_total': all_revive_coins_total,
            'all_revive_users': all_revive_users,
            'all_revive_users_total': all_revive_users_total,

            'all_dungeon_levels_sorted': all_dungeon_levels_sorted,
            'yesterday_login_users_level': yesterday_login_users_level,
            'yesterday_login_users_total': yesterday_login_users_total,

            'yesterday_special_weekly_users': yesterday_special_weekly_users,
            'yesterday_special_weekly_times': yesterday_special_weekly_times,

        }

        return render_to_response('statistics/revive.html', 
            data_dict,
            RequestContext(request) )





############################################################################
    continue_login = request.GET.get('continue_login', '')
    if continue_login:
        #all users in database
        continue_login_count = UserLogin.aggregate([
                    {'$group': {
                        '_id': '$login_info.continuous_login_num',
                        'total':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #0, 1 days results is not correct, due to first-time user, its login 
        #time was set one day earlier, for gift-giving purpose.
        continue_login_count = [ {'total':i['total'],'days':i['_id']} for i in continue_login_count if i['_id'] not in (0,1) ]  



        #yesterday-login or today-login users in database
        results = UserLogin.aggregate([
                    {    '$match': {'login_info.login_time': {
                            '$gte': (today_morning_ts - 24*3600) } }
                    },

                    {'$group': {
                        '_id': '$login_info.continuous_login_num',
                        'total':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### yesterday_login_continue_count, results=', results
        #0, 1 days results is not correct, due to first-time user, its login 
        #time was set one day earlier, for gift-giving purpose.
        yesterday_today_login_continue_count = dict( [ (i['_id'], i['total']) for i in results if i['_id'] not in (0,1) ] )


        #yesterday-login users in database
        results = UserLogin.aggregate([
                    {    '$match': {'login_info.login_time': {
                            '$gte': (today_morning_ts - 24*3600),
                            '$lt': today_morning_ts } }
                    },

                    {'$group': {
                        '_id': '$login_info.continuous_login_num',
                        'total':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### yesterday_login_continue_count, results=', results
        #0, 1 days results is not correct, due to first-time user, its login 
        #time was set one day earlier, for gift-giving purpose.
        yesterday_login_continue_count = dict( [ (i['_id'], i['total']) for i in results if i['_id'] not in (0,1) ] )


        #today-login users in database
        results = UserLogin.aggregate([
                    {    '$match': {'login_info.login_time': {
                            '$gte': today_morning_ts, } }
                    },

                    {'$group': {
                        '_id': '$login_info.continuous_login_num',
                        'total':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### yesterday_login_continue_count, results=', results
        #0, 1 days results is not correct, due to first-time user, its login 
        #time was set one day earlier, for gift-giving purpose.
        today_login_continue_count = dict( [ (i['_id'], i['total']) for i in results if i['_id'] not in (0,1) ] )


        #print '#### yesterday_login_continue_count=', yesterday_login_continue_count

        data_dict = {
            'continue_login_count': continue_login_count,
            'yesterday_today_login_continue_count': yesterday_today_login_continue_count,
            'yesterday_login_continue_count': yesterday_login_continue_count,
            'today_login_continue_count': today_login_continue_count,
        }

        return render_to_response('statistics/continue_login.html', 
            data_dict,
            RequestContext(request) )





############################################################################
    coins_in_hand = request.GET.get('coins_in_hand', '')
    if coins_in_hand:

        results = UserProperty.aggregate([
                    {'$group': {
                        '_id': '$property_info.coin',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        coin_users = dict( [ (row['_id'], row['users']) for row in results ] )

        #10000 are manually added, not bought
        for k,v in coin_users.items():
            if k > 10000:
                del(coin_users[k])

        coins_max = max (coin_users.keys())
        coins_step = int ( coins_max / 90 )
        if coins_step == 0:
            coins_step = 1
        coins_step = int(coins_step/10)*10

        coins_stat = {}
        for i in range(100):
            coins_stat[i] = 0
        for coins, users in coin_users.items():
            coins_stat[ int(coins/coins_step) ] += users

        coins_steps = {}
        for i in range(100):
            coins_steps[i] = str( i * coins_step ) + ' - ' + str( (i+1)*coins_step - 1) 


        #### charged users
        results = UserProperty.aggregate([
                {'$match': {'property_info.charge_sumcoin': {'$gt':0}}},
                    {'$group': {
                        '_id': '$property_info.coin',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])
        coin_charged_users = dict( [ (row['_id'], row['users']) for row in results ] )
        #10000 are manually added, not bought
        for k,v in coin_charged_users.items():
            if k > 10000:
                del(coin_charged_users[k])

        coins_charged_stat = {}
        for i in range(100):
            coins_charged_stat[i] = 0
        for coins, users in coin_charged_users.items():
            coins_charged_stat[ int(coins/coins_step) ] += users

        coins_never_charged_stat = {}
        for i in range(100):
            coins_never_charged_stat[i] = coins_stat[i] - coins_charged_stat[i]




        #### yesterday login users
        results = LoginRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': today_morning } } },  
                    {'$group': {'_id': '$uid'} },
                    {"$sort": SON([("_id", 1)]) }
                    ])
        yesterday_login_uids = [ r['_id'] for r in results ]
        results = UserProperty.aggregate([
                {'$match': {'uid': {'$in': yesterday_login_uids}}},
                    {'$group': {
                        '_id': '$property_info.coin',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])
        coin_yestlogin_users = dict( [ (row['_id'], row['users']) for row in results ] )
        #10000 are manually added, not bought
        for k,v in coin_yestlogin_users.items():
            if k > 10000:
                del(coin_yestlogin_users[k])

        coins_yestlogin_stat = {}
        for i in range(100):
            coins_yestlogin_stat[i] = 0
        for coins, users in coin_yestlogin_users.items():
            coins_yestlogin_stat[ int(coins/coins_step) ] += users


        data_dict = {
            'coins_steps': coins_steps,
            'coins_stat': coins_stat,
            'coins_charged_stat': coins_charged_stat,
            'coins_never_charged_stat': coins_never_charged_stat,
            'coins_yestlogin_stat': coins_yestlogin_stat,
        }

        return render_to_response('statistics/coins_in_hand.html', 
            data_dict,
            RequestContext(request) )



#################################################################
    if request.GET.get('equip'):
        equip_id_sorted = game_config.equip_config.keys()
        equip_id_sorted.sort(key=sort_by_first_int)


        mapper = Code("""
                function () {
                    for(var key in this.equips) { 
                        if(key!='_id') emit(key, this.equips[key].has); 
                    } 
                }
                """)
        reducer = Code("""
                function (key, values) {
                    return Array.sum(values); 
                }
                """)

        results = ocapp.bk_mongo.mongo.db['userequips'].map_reduce(mapper,
                reducer, 'myresults')

        equips_store = dict([ (row['_id'], int(row['value']) ) for row in results.find() ])



        #### cards
        mapper = Code("""
                function () {
                    for(var card_id in this.cards) { 
                        if( 'eid_list' in this.cards[card_id] ) { 
                            for(var i in this.cards[card_id]['eid_list'])
                            { equip_id = this.cards[card_id]['eid_list'][i];
                              if ( equip_id != '' )
                                emit(equip_id, 1);
                            }
                        }
                    } 
                }
                """)
        reducer = Code("""
                function (key, values) {
                    return Array.sum(values); 
                }
                """)

        results = ocapp.bk_mongo.mongo.db['usercards'].map_reduce(mapper,
                reducer, 'myresults')   #, full_response=True)

        equips_attached = dict([ (row['_id'], int(row['value']) ) for row in results.find() ])
        

        ### generated yesterday
        results = EquProduct.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': today_morning } } },  
                    {'$group': {'_id': '$equip_dict.eid',
                                'count': {'$sum': '$equip_dict.has'} } },
                    {"$sort": SON([("_id", 1)]) }
                    ])
        yesterday_gen_equips = dict( [ (row['_id'], row['count']) for row in results ] )


        ### generated last week
        results = EquProduct.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=8) ),
                        '$lt': today_morning } } },  
                    {'$group': {'_id': '$equip_dict.eid',
                                'count': {'$sum': '$equip_dict.has'} } },
                    {"$sort": SON([("_id", 1)]) }
                    ])
        last_week_gen_equips = dict( [ (row['_id'], row['count']) for row in results ] )


        #### has-equip unique users, either in-store, or attached.
        mapper = Code("""
                function () {
                    for(var key in this.equips) { 
                        emit(key, this.uid); 
                    } 
                }
                """)
        reducer = Code("""
                function (key, values) {
                    reduced_value = []
                    reduced_value += [values]
                    return reduced_value
                }
                """)

        results = ocapp.bk_mongo.mongo.db['userequips'].map_reduce(mapper,
                reducer, 'myresults')

        store_equip_uids = dict([ (row['_id'], row['value'] ) for row in results.find() ])


        ### attached to cards
        mapper = Code("""
                function () {
                    for(var card_id in this.cards) { 
                        if( 'eid_list' in this.cards[card_id] ) { 
                            for(var i in this.cards[card_id]['eid_list'])
                            { equip_id = this.cards[card_id]['eid_list'][i];
                              if ( equip_id != '' )
                                emit(equip_id, this.uid);
                            }
                        }
                    } 
                }
                """)

        #results = ocapp.bk_mongo.mongo.db['usercards'].aggregate([
        #            {'$group': {'_id': '$cards.eid_list',
        #                        'uids': {'$addToSet': '$uid'} } },
        #            {"$sort": SON([("_id", 1)]) }
        #        ]) 

        results = ocapp.bk_mongo.mongo.db['usercards'].map_reduce(mapper,
                reducer, 'myresults')   #, full_response=True)

        attached_equip_uids = dict([ (row['_id'], row['value'] ) for row in results.find() ])

        #count unique users
        unique_users = {}
        for equip_id in equip_id_sorted:
            tmp_list = []
            if equip_id in store_equip_uids:
                tmp_list +=  store_equip_uids[equip_id].split(',')
            if equip_id in attached_equip_uids:
                tmp_list +=  attached_equip_uids[equip_id].split(',')

            unique_users[equip_id] = len( set(tmp_list) )

        #print '#### uids=', uids


        data_dict = {
                'equips_store': equips_store,
                'equips_attached': equips_attached,
                'equip_id_sorted': equip_id_sorted,
                'yesterday_gen_equips': yesterday_gen_equips,
                'last_week_gen_equips': last_week_gen_equips,
                'unique_users': unique_users,
                }

        return render_to_response('statistics/equipment.html', 
            data_dict,
            RequestContext(request) )

#################################################################
    if request.GET.get('dungeon_type_hot'):
        dungeon_yestordy_resutls = DungeonRecord.aggregate([
                    { 
                    '$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': (today_morning - timedelta(days=0) ),
                            },
                        'statament': 'start',
                    } },  
                    {'$group': {
                        '_id': {'uid':'$uid','dungeon_type':'$dungeon_type',},
                       } }, 
                    {'$group': {
                        '_id': '$_id.dungeon_type',#能有3个group吗
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
            ])  

        dungeon_all_resutls = DungeonRecord.aggregate([
                    { 
                    '$match': {
                        'statament': 'start',
                    } },  
                    {'$group': {
                        '_id': {'dungeon_type':'$dungeon_type', 'uid':'$uid'},
                       } }, 
                    {'$group': {
                        '_id': '$_id.dungeon_type',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
            ])

        special_dungeon_detail_resutls = DungeonRecord.aggregate([
                    { 
                    '$match': {
                        'statament': 'start',
                        'dungeon_type':{"$not":re.compile("normal.*")}
                    } },  
                    {'$group': {
                        '_id': {'dungeon_id':'$dungeon_id', 'uid':'$uid'},
                       } }, 
                    {'$group': {
                        '_id': '$_id.dungeon_id',
                        'users':{'$addToSet' : '$_id.uid' },
                       } }, 
                    {"$sort": SON([("_id", 1)])}
            ])
        
        special_dungeon_detail_resutls_yestoday = DungeonRecord.aggregate([
                    { 
                    '$match': {
                        'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': (today_morning - timedelta(days=0) ),
                            },
                        'statament': 'start',
                        'dungeon_type':{"$not":re.compile("normal.*")}
                    } },  
                    {'$group': {
                        '_id': {'dungeon_id':'$dungeon_id', 'uid':'$uid'},
                       } }, 
                    {'$group': {
                        '_id': '$_id.dungeon_id',
                        'users':{'$addToSet' : '$_id.uid' },
                       } }, 
                    {"$sort": SON([("_id", 1)])}
            ])

        # [ i. for i in special_dungeon_detail_resutls]
        special_dungeon_floor = {}
        for special_room in special_dungeon_detail_resutls:
            floor_id = special_room['_id'].split('_')[0]
            if floor_id not in special_dungeon_floor:
                special_dungeon_floor[floor_id] = set()
            special_dungeon_floor[floor_id].update(set(special_room['users']))   

        special_dungeon_floor = dict([ (floor,len(special_dungeon_floor[floor])) for floor in special_dungeon_floor ])

        special_dungeon_floor_yestoday = {}
        for special_room in special_dungeon_detail_resutls_yestoday:
            floor_id = special_room['_id'].split('_')[0]
            if floor_id not in special_dungeon_floor_yestoday:
                special_dungeon_floor_yestoday[floor_id] = set()
            special_dungeon_floor_yestoday[floor_id].update(set(special_room['users']))   

        special_dungeon_floor_yestoday = dict([ (floor,len(special_dungeon_floor_yestoday[floor])) for floor in special_dungeon_floor_yestoday ])



        pvp_yestordy_resutls = PvpRecord.aggregate([
                    { 
                    '$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=1) ),
                        '$lt': (today_morning - timedelta(days=0) ),
                            },
                        'statament': 'start',
                    } },  
                    {'$group': {
                        '_id': '$uid',
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
            ]) 

        pvp_all_resutls = PvpRecord.aggregate([
                    { 
                    '$match': {
                        'statament': 'start',
                    } },  
                    {'$group': {
                        '_id': '$uid',
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
            ])  
        # dungeon_hot_show = {'normal':{}}
        yesterday_dict = dict([ (tmp['_id'],tmp['users']) for tmp in dungeon_yestordy_resutls ])
        yesterday_dict['pvp'] = len(pvp_yestordy_resutls)
        total_dict = dict([ (tmp['_id'],tmp['users']) for tmp in dungeon_all_resutls ])
        total_dict['pvp'] = len(pvp_all_resutls)
        data_dict = {}
        data_dict['total_dict'] = total_dict
        data_dict['special_dungeon_floor_yestoday'] = special_dungeon_floor_yestoday
        data_dict['special_dungeon_floor'] = special_dungeon_floor
        data_dict['yesterday_dict'] = yesterday_dict
        return render_to_response('statistics/dungeon_type_hot.html', 
            data_dict,
            RequestContext(request) )



#################### revive statistics on certain day, not yesterday ##########
    revive_stat_by_date = request.GET.get('revive_stat_by_date', '')
    if revive_stat_by_date:

        revive_date = request.GET.get('revive_date', '')
        year, month, day = revive_date.split('-')
        year, month, day = int(year), int(month), int(day)
        revive_datetime = today_morning.replace(year=year, month=month, 
                            day=day)
        days_delta = (now - revive_datetime).days

        #### certain day
        revive_coins_consume = {}
        results = CoinConsume.aggregate([
                    { 
                        '$match': {'date_time': {
                            '$gte': (today_morning - timedelta(days=days_delta+1) ),
                            '$lt': (today_morning - timedelta(days=days_delta) ),
                                },
                            'where': {'$regex': 'revive*'},
                        } },  
                    {'$group': {
                        '_id': '$where',
                        'total':{'$sum' : '$sum' },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### revive results=', results
        for row in results:
            k = row['_id']
            if row['_id'].count('_') == 3:
                keys = row['_id'].split('_')
                k = keys[-1] + ': ' + keys[1] + '_' + keys[2]
            revive_coins_consume[ k ] = row['total']
        revive_coins_total = sum(revive_coins_consume.values())

        all_dungeon_levels = []
        for floor, v in game_config.normal_dungeon_config.items():
            for room in v['rooms'].keys():
                all_dungeon_levels += [ 'normal: ' + floor + '_' + room ]
        for floor, v in game_config.special_normal_dungeon_config.items():
            for room in v['rooms'].keys():
                all_dungeon_levels += [ 'special: ' + floor + '_' + room ]
        for floor, v in game_config.weekly_normal_dungeon_config.items():
            for room in v['rooms'].keys():
                all_dungeon_levels += [ 'weekly: ' + floor + '_' + room ]

        all_dungeon_levels_sorted = all_dungeon_levels
        all_dungeon_levels_sorted.sort( key=sort_dungeon_type_level)


        ####### certain day 
        revive_users = {}
        results = CoinConsume.aggregate([
                    { 
                        '$match': {'date_time': {
                            '$gte': (today_morning - timedelta(days=days_delta+1) ),
                            '$lt': (today_morning - timedelta(days=days_delta) ),
                                },
                            'where': {'$regex': 'revive*'},
                        } },  
                    {'$group': {
                        '_id': {'where':'$where', 'uid':'$uid'},
                       } }, 
                    {'$group': {
                        '_id': '$_id.where',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        #print '#### revive results=', results

        for row in results:
            k = row['_id']
            if row['_id'].count('_') == 3:
                keys = row['_id'].split('_')
                k = keys[-1] + ': ' + keys[1] + '_' + keys[2]
            revive_users[ k ] = row['users']
        revive_users_total = sum(revive_users.values())



        #### certain day login users
        level_users = {}
        results = LoginRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=(days_delta+1)) ),
                        '$lt': today_morning - timedelta(days=days_delta) } } },  
                    {'$group': {'_id': '$uid'} },
                    {"$sort": SON([("_id", 1)]) }
                    ])
        that_day_login_uids = []
        if len(results) > 0:
            that_day_login_uids = [ l['_id'] for l in results ]

        ### certain day login users' max level
        that_day_login_users_level ={}
        results = UserDungeon.aggregate([
                    {
                      '$match': {'uid': {'$in': that_day_login_uids} }
                        },  
                    {'$group': {
                        '_id': {'floor_id': '$dungeon_info.normal_current.floor_id',
                            'room_id': '$dungeon_info.normal_current.room_id' },
                        "users":{"$sum" : 1}
                        } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### dungeon level users results=', results
        if len(results) > 0:
            for d in results:
                that_day_login_users_level[ 'normal: ' + str(d['_id']['floor_id']) + '_' + str(d['_id']['room_id']) ] = d['users']

        #set None to 0
        that_day_login_users_total = 0
        for dlevel in all_dungeon_levels_sorted:
            if dlevel[:7] != 'normal:':
                continue
            if dlevel in that_day_login_users_level:
                that_day_login_users_total += that_day_login_users_level[dlevel]
                continue
            that_day_login_users_level[dlevel] = 0


        #### certain day Weekly/Special dungeon unique users
        results = DungeonRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=(days_delta+1)) ),
                        '$lt': today_morning - timedelta(days=days_delta) },
                        'statament': 'end',
                        'dungeon_type': {'$in' : ['special', 'weekly']},
                        } },  
                    {'$group': {'_id': {
                        'dungeon_type':'$dungeon_type', 
                        'dungeon_id':'$dungeon_id',  
                        'uid':'$uid'} }
                        },

                    {'$group': {'_id': {
                        'dungeon_type':'$_id.dungeon_type', 
                        'dungeon_id':'$_id.dungeon_id',  
                        },
                        'users': {'$sum': 1} }
                        },

                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### DungeonRecord special, weekly =', results

        that_day_special_weekly_users = {}
        for row in results:
            that_day_special_weekly_users[ row['_id']['dungeon_type'] + ': ' +
                    row['_id']['dungeon_id'] ]= row['users']



        #### certain day Weekly/Special dungeon unique users
        results = DungeonRecord.aggregate([
                    {'$match': {'date_time': {
                        '$gte': (today_morning - timedelta(days=(days_delta+1)) ),
                        '$lt': today_morning - timedelta(days=days_delta) },
                        'statament': 'end',
                        'dungeon_type': {'$in' : ['special', 'weekly']},
                        } },  

                    {'$group': {'_id': {
                        'dungeon_type':'$dungeon_type', 
                        'dungeon_id':'$dungeon_id',  
                        },
                        'times': {'$sum': 1} }
                        },

                    {"$sort": SON([("_id", 1)]) }
                    ])
        #print '#### DungeonRecord special, weekly =', results

        that_day_special_weekly_times = {}
        for row in results:
            that_day_special_weekly_times[ row['_id']['dungeon_type'] + ': ' +
                    row['_id']['dungeon_id'] ]= row['times']



        data_dict = {
            'revive_coins_consume': revive_coins_consume,
            'revive_coins_total': revive_coins_total,
            'revive_users': revive_users,
            'revive_users_total': revive_users_total,

            'revive_date': revive_date,

#           'all_revive_coins_consume': all_revive_coins_consume,
#           'all_revive_coins_total': all_revive_coins_total,
#           'all_revive_users': all_revive_users,
#           'all_revive_users_total': all_revive_users_total,

            'all_dungeon_levels_sorted': all_dungeon_levels_sorted,
            'that_day_login_users_level': that_day_login_users_level,
            'that_day_login_users_total': that_day_login_users_total,

            'that_day_special_weekly_users': that_day_special_weekly_users,
            'that_day_special_weekly_times': that_day_special_weekly_times,

        }

        return render_to_response('statistics/revive_by_date.html', 
            data_dict,
            RequestContext(request) )





#################### ItemProduct,  Item bought in one week 药水购买的 #########
    items_bought_stat = request.GET.get('items_bought_stat', '')
    if items_bought_stat:
        results = ItemProduct.aggregate([
                    { 
                        '$match': {'date_time': {
                            '$gte': (today_morning - timedelta(days=7) ),
                            '$lt': today_morning,
                                },
                        } },  
                    {'$group': {
                        '_id': '$item_id',
                        'total':{'$sum' : '$sum' },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        items_bought = dict( [ (row['_id'], row['total']) for row in results ] )


        results = ItemProduct.aggregate([
                    { 
                        '$match': {'date_time': {
                            '$gte': (today_morning - timedelta(days=7) ),
                            '$lt': today_morning,
                                },
                        } },  
                    {'$group': {
                        '_id': {'item_id':'$item_id', 'uid': '$uid'},
                       } }, 
                    {'$group': {
                        '_id': '$_id.item_id',
                        'users':{'$sum' : 1 },
                       } }, 
                    {"$sort": SON([("_id", 1)]) }
                    ])

        buy_item_users = dict( [ (row['_id'], row['users']) for row in results ] )

        all_item_ids = items_bought.keys()
        all_item_ids.sort(key=sort_by_first_int)

        all_item_names = {}
        for item_id, details in game_config.city_shop_config['city_goods'].items():
            all_item_names[item_id] = details['describe']


        data_dict = {
                'all_item_ids': all_item_ids,
                'all_item_names': all_item_names,
                'items_bought': items_bought,
                'buy_item_users': buy_item_users,
                }
        data_dict["index_list"] = request.index_list
        return render_to_response('statistics/items_bought.html', 
            data_dict,
            RequestContext(request) )




########################## default index page #############
    else:
        return render_to_response('statistics/index.html', {"index_list": request.index_list},
            RequestContext(request) )
