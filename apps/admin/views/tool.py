#-*- coding:utf-8 -*-
import copy
import os, os.path
#import json

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext

from apps.admin.decorators import require_permission
#from apps.admin.decorators import get_moderator_username
from apps.common import utils
from apps.config.game_config import game_config
from apps.logics import dungeon
from apps.logics.gacha import __select_gacha_card
from apps.models.virtual.card import Card
from apps.admin.bulletin import Bulletin
import glob, datetime, time

import shutil
from apps.models import data_log_mod
from apps.common.utils import string_toDatetime
from apps.oclib import app
from apps.common import utils
from urllib import urlencode

from apps.models import data_log_mod
ChargeRecord = data_log_mod.get_log_model("ChargeRecord")
ConsumeRecord = data_log_mod.get_log_model("CoinConsume")


total_notice_versions = 10

@require_permission
def index(request):
    """
    """
    debug = settings.DEBUG
    data = {'support': False, 'debug':debug}
    data['app_name'] = ''
    data['notice_versions'] = range(total_notice_versions)
    return 'tool/index.html', data


def gacha(request):
    """
    测试求将
    """
    
    data = {
        'plus_count': 0,
    }
    gacha_type = request.REQUEST.get("type",'')
    data['type'] = gacha_type
    rate_conf = game_config.gacha_config[gacha_type]
    count = request.REQUEST.get("count")
    if not count:
        count = '1'
    count = int(count)
    data['count'] = count
    i = 0
    card_dict = {}
    new_cards = []
    new_cards_ex = []
    while i < count:
        cid,clv = __select_gacha_card(rate_conf)
        new_cards.append((cid, clv))
        i += 1

    #如果是10的倍数，认为是10连抽
#    if count%10 ==0 and gacha_type == "charge_rate":
#        for i in range(0, len(new_cards), 10):
#            new_cards_10 = new_cards[i:i+10]
#            __switch_cards(new_cards_10)
#            new_cards_ex.extend(new_cards_10)
#    else:
    new_cards_ex = new_cards
    card_update_config = game_config.card_update_config
    CARD_CATEGORY = {'0':u'攻击型','1':u'防御型','2':u'血型','3':u'回复型',\
    '4':u'平衡型','5':u'超生命型','6':u'超攻击型','7':u'转生道具','8':u'强化合成','9':u'超防御型','10':u'超回复型'}
    for cid, clv in new_cards_ex:
        card_obj = Card.get(cid)
        category = card_obj.category
        quality = ''
        if not category or category not in ['7','8']:
            category = utils.get_item_by_random_simple(card_update_config['card_category_weight'])
            #平衡型是没有品质
            if category != '4':
                quality = utils.get_item_by_random_simple(card_update_config['card_quality_weight'])
        keys_str = '%s:%s:%s' % (cid,category,quality)
        if keys_str in card_dict and category == card_dict[keys_str]['category'] and quality == card_dict[keys_str]['quality']:
            card_dict[keys_str]['count'] += 1
        else:
            card_dict[keys_str] = {
                'name':card_obj.name,
                'star':card_obj.star,
                'ctype':card_obj.ctype,
                'cid':cid,
                'lv':clv,
                'count':1,
                'plus_num':0,
                'category':category,
                "category_name":CARD_CATEGORY[category],
                'quality':quality,
            }

        #记录抽到plus属性的个数
        #cardmod_obj = Card.get(cid)
#        if utils.is_happen(float(cardmod_obj.pl_rate)):
#            plus_type = random.choice(['pl_attack','pl_hp','pl_recover'])
#        elif gacha_type == 'free_rate':
#            plus_type = utils.getPlusCard("gacha_free")
#        elif gacha_type == 'charge_rate':
#            plus_type = utils.getPlusCard("gacha_charge")
#        if plus_type:
#            card_dict[cid]['plus_num'] += 1
#            data['plus_count'] += 1

    order = request.REQUEST.get('order')
    data['order'] = order
    card_list = sorted(card_dict.items(),key=lambda x:x[1][order],reverse=True)
    data['card_list'] = card_list
    return render_to_response('tool/gacha.html',{"data":data},RequestContext(request))

def __dungeon_fun(max_stone,min_stone,max_gold,min_gold,get_stone,get_gold):
    """战场测试功能，记录经验和铜钱
    """
    if not max_stone or get_stone > max_stone:
        max_stone = get_stone
    if not min_stone or get_stone < min_stone:
        min_stone = get_stone
    if not max_gold or get_gold > max_gold:
        max_gold = get_gold
    if not min_gold or get_gold < min_gold:
        min_gold = get_gold
    return max_stone,min_stone,max_gold,min_gold

def card(request):
    """查找武将
    """

    star = request.REQUEST.get('star')
    ctype = request.REQUEST.get('ctype')
    cids_list = []
    name_list = []
    name_str = u'#'
    cid_str = '['
    for cid in game_config.card_config:
        if star and ctype:
            if star == game_config.card_config[cid]['star'] and\
            ctype == game_config.card_config[cid]['ctype']:
                cids_list.append("'%s'" % cid)
                name_list.append(u'%s星' % game_config.card_config[cid]['star']\
                 + game_config.card_config[cid]['name'])
        elif star:
            if star == game_config.card_config[cid]['star']:
                cids_list.append("'%s'" % cid)
                name_list.append(u'%s星' % game_config.card_config[cid]['star']\
                 + game_config.card_config[cid]['name'])
        elif ctype:
            if ctype == game_config.card_config[cid]['ctype']:
                cids_list.append("'%s'" % cid)
                name_list.append(u'%s星' % game_config.card_config[cid]['star']\
                 + game_config.card_config[cid]['name'])
        else:
            cids_list.append("'%s'" % cid)
            name_list.append(u'%s星' % game_config.card_config[cid]['star']\
             + game_config.card_config[cid]['name'])
    name_str += u','.join(name_list)
    cid_str += ','.join(cids_list)
    cid_str += ']'
    return render_to_response('tool/card.html',{"name_str":name_str,\
    "cid_str":cid_str,"card_star":star,"ctype":ctype},RequestContext(request))

def dungeon_test(request):
    """
    测试关卡掉落
    """
    
    dungeon_type = request.REQUEST.get('dungeon_type')
    floor_id = request.REQUEST.get('floor_id')

    room_id = request.REQUEST.get('room_id')
    count = request.REQUEST.get('count')
    count = int(count)
    user_type = request.REQUEST.get("user_type")
    if user_type == "odd":
        uid = 'xxxx1'
    else:
        uid = 'xxxx2'
    #所有关卡测试
    if str(floor_id) == '*':
        dungeon_test_all(request)
        return HttpResponse('<script>alert("所有关卡通过测试（100次为佳）");history.go(-1)</script>')
    #获得影响铜板值的主将的列表
    lstitem = request.REQUEST.items()
    params = {}
    for key, value in lstitem:
        if value != "" and key in ['deck_1', 'deck_2']:
            value = str(value) + "_card"
        params[key] = value
    deck_1 = params['deck_1']
    deck_2 = params['deck_2']
    card_dict = {}
    result = []
    max_gold = 0
    min_gold = 0
    max_stone = 0
    min_stone = 0
    total_gold = 0
    total_stone = 0
#    total_exp = 0
    avg_exp = 0
    avg_gold = 0
    drop_cards_num = 0
    total_material_drop = {}
    mat_config = game_config.material_config
    try:
        conf = dungeon.__get_conf(request.REQUEST, uid)
        deck1_skid = ''
        deck2_skid = ''
        if deck_1:
            deck1_skid = Card.get(deck_1).leader_skid
        if deck_2:
            deck2_skid = Card.get(deck_2).leader_skid
        for i in range(count):
            step_info = dungeon.__calculate_steps(params, conf, None, deck1_skid, deck2_skid)
            get_cards = step_info['get_cards']
            gold = int((step_info['total_gold']+step_info['dungeon_gold']) * step_info['dungeon_effect']['gold'])
            stone = int(step_info['total_stone']*step_info['dungeon_effect']['stone'])
            avg_exp = step_info['exp']
            material_drop = step_info['total_material_drop_all']
            total_material_drop = {ma_id :{'cnt':total_material_drop.get(ma_id,{}).get('cnt',0)+material_drop.get(ma_id,0), \
                                           'name':mat_config[ma_id]['name']} \
                                   for ma_id in set(total_material_drop.keys()+material_drop.keys())}
            for cid in get_cards:
                drop_cards_num += 1
                if cid in card_dict:
                    card_dict[cid]['count'] += 1
                else:
                    card_dict[cid] = {'name':Card.get(cid).name,'count':1, }

            max_stone,min_stone,max_gold,min_gold = __dungeon_fun(\
            max_stone,min_stone,max_gold,min_gold,stone,gold)
            total_gold += gold
            total_stone += stone
#            total_exp += exp
        result = sorted(card_dict.items(),key = lambda x:x[1]['count'])
        avg_gold = total_gold / count
#        avg_exp = total_exp / count
        avg_stone = total_stone / count
        for ma_id in total_material_drop:
            total_material_drop[ma_id]['cnt'] /= count*1.0
        material_list = sorted(total_material_drop.items(),key=lambda x:x[1]['cnt'])

    except:
        import traceback
        print traceback.print_exc()
        return render_to_response('tool/dungeon.html',{'msg':'选择正确的战场'},RequestContext(request))
    return render_to_response('tool/dungeon.html',{"result":result,\
    "dungeon_type":dungeon_type,"floor_id":floor_id,"room_id":room_id,\
    'max_stone':max_stone,'min_stone':min_stone,'max_gold':max_gold,'min_gold':min_gold,\
    'avg_gold':avg_gold,'avg_stone':avg_stone,'avg_exp':avg_exp, 'drop_cards_num': drop_cards_num,\
     'material_list':material_list,'count': str(count), },RequestContext(request))

def dungeon_test_all(request):
    """
    所有关卡测试
    """
    

    dungeon_type = str(request.REQUEST.get('dungeon_type'))
    count = request.REQUEST.get('count')
    user_type = request.REQUEST.get("user_type")
    if user_type == "odd":
        uid = 'xxxx1'
    else:
        uid = 'xxxx2'
    conf = {
        'normal':copy.deepcopy(game_config.normal_dungeon_config),
        'special':copy.deepcopy(game_config.special_dungeon_config),
        'weekly':copy.deepcopy(game_config.weekly_dungeon_config),
    }[dungeon_type]
    try:
        for floor_id in conf:
            for room_id in conf[floor_id]['rooms']:
                new_params = dict(copy.deepcopy(request.REQUEST))
                new_params[u'floor_id'] = floor_id
                new_params[u'room_id'] = room_id
                get_conf = dungeon.__get_conf(new_params, uid)
                for i in range(int(count)):
                    step_info = dungeon.__calculate_steps(new_params, get_conf, None)

    except Exception,e:
        import traceback
        import sys
        traceback.print_exc(file=sys.stderr)
        data = {}
        data['msg'] = traceback.format_exc()
        data['dungeon_type'] = dungeon_type
        data['floor_id'] = floor_id
        data['room_id'] = room_id
        return render_to_response(data)

@require_permission
def customer_service(request):
    """客服工具
    """
    data = {'search_type':'all'}
    uid = request.REQUEST.get('uid','').strip()
    pid = request.REQUEST.get('pid','').strip()
    uid_charge = request.REQUEST.get('uid_charge','').strip()
    oid = request.REQUEST.get('oid','').strip()
    start_date_charge = request.REQUEST.get('start_date_charge','')
    end_date_charge = request.REQUEST.get('end_date_charge','')
    for i in ["uid","pid","uid_charge","start_date_charge","oid","end_date_charge"]:
        data[i] = request.REQUEST.get(i,'')
    result_consume = []
    result_charge = []
    from apps.models.account_mapping import AccountMapping
    if not uid and pid:
        uid = AccountMapping.get(pid).uid
    if uid:
        search_type = request.REQUEST.get('search_type','all')
        start_date = request.REQUEST.get('start_date','')
        data['start_date'] = start_date
        end_date = request.REQUEST.get('end_date','')
        data['end_date'] = end_date
        data['uid'] = uid
        data['search_type'] = search_type
        if search_type == 'charge' or search_type == 'all':
            result_charge = _get_charge_record(uid,start_date,end_date)
        if search_type == 'consume' or search_type == 'all':
            result_consume = _get_consume_record(uid,start_date,end_date)
    all_result = result_consume + result_charge
    tmp = sorted([(i.createtime,i)for i in all_result],key=lambda x:x[0])
    sorted_result = [ i[1] for i in tmp]
    data['result'] = sorted_result
    data["charge_log"] = {}
    match_query = {}
    if uid_charge or oid:
        shop_config = copy.deepcopy(game_config.shop_config)
        sale = shop_config['sale']
        sale.update(shop_config.get('google_sale',{}))
        sale.update(shop_config.get('new_sale',{}))
        sale.update(shop_config.get('mycard_sale',{}))
        if uid_charge:
            match_query['uid'] = uid_charge
        if oid:
            match_query['oid'] = oid
        if start_date_charge or end_date_charge:
            match_query['date_time'] = {}
            if start_date_charge:
                match_query['date_time']['$gte'] = string_toDatetime('%s 00:00:00' % start_date_charge)
            if end_date_charge:
                match_query['date_time']['$lte'] = string_toDatetime('%s 23:59:59' % end_date_charge)
        charge_log = data_log_model.get_log_model("ChargeResultLog").find(match_query)
        charge_log_list = []
        for c_log in charge_log:
            tmp = {}
            tmp['uid'] = c_log.uid
            tmp['oid'] =  c_log.oid if hasattr(c_log,'oid') else ''
            tmp['item_id'] = '%s元(%s元宝)' % (sale.get(c_log.item_id,{}).get('price','None'),sale.get(c_log.item_id,{}).get('num','None')) \
                              if hasattr(c_log,'item_id') else ''
            tmp['charge_way'] = c_log.charge_way
            tmp['result'] = c_log.result
            tmp['date_time'] = c_log.date_time
            charge_log_list.append(tmp)
        data['charge_log'] = charge_log_list
        data['sale'] = sale
    return 'tool/customer_service.html', data

def _get_charge_record(uid,start_date,end_date):
    match_query = {}
    if uid:
        match_query['uid'] = uid
    if start_date or end_date:
        match_query['createtime'] = {}
        if start_date:
            match_query['createtime']['$gte'] = '%s 00:00:00' % start_date
        if end_date:
            match_query['createtime']['$lte'] = '%s 23:59:59' % end_date
    result = ChargeRecord.find(match_query)
    return result


def _get_consume_record(uid,start_date,end_date):
    match_query = {}
    if uid:
        match_query['uid'] = uid
    if start_date or end_date:
        match_query['createtime'] = {}
        if start_date:
            match_query['createtime']['$gte'] = '%s 00:00:00' % start_date
        if end_date:
            match_query['createtime']['$lte'] = '%s 23:59:59' % end_date
    result = ConsumeRecord.find(match_query)
    return result

def upload_static(request):
    '''
    上传到指定的静态HTML目录， 若 空文件，则删除服务器上同名文件。
    '''
    remote_dir = request.POST.get('remote_dir', '')
    force_overwrite = request.POST.get('force_overwrite', '')

    local_file = request.FILES.get('local_file', '')

    if remote_dir not in ('/static', '/static/html', '/static/html/image_ui'):
        return HttpResponse(u'错误的远程服务器端的目录: ' + remote_dir)

    if not local_file:
        return HttpResponse(u'需要选择一个本地文件')

    filename = str(local_file.name)
    file_path = settings.BASE_ROOT + remote_dir + '/' + filename

    if os.path.exists(file_path) and force_overwrite != 'true':
        return HttpResponse(u'服务器上已存在一个同名文件, 而你又没有选择要覆盖/替换')

#   dir_path = settings.BASE_ROOT + '/static/'
#   shutil.rmtree(file_path,True)
#   shutil.rmtree(file_path.replace('.zip',''),True)

#   destination = open(file_path, 'w')
#   for chunk in file.chunks():
#       destination.write(chunk)
#   destination.close()

    f = open(file_path, 'w')
    print >>f, local_file.file.read(),
    f.close()
    os.system('/bin/chmod 644 ' + file_path)

    if os.path.getsize(file_path) == 0:
        os.remove(file_path)
        return HttpResponse(u'成功删除了: ' + remote_dir + '/' + filename )

    return HttpResponse(u'成功上传到: ' + remote_dir + '/' + filename)


#def update_bulletin(request):
#    file = request.FILES.get('html', None)
#    filename = str(file.name)
#    file_path = settings.BASE_ROOT + '/static/html/' + filename
#    dir_path = settings.BASE_ROOT + '/static/html/'
#    shutil.rmtree(file_path,True)
#    shutil.rmtree(file_path.replace('.zip',''),True)
#    destination = open(file_path, 'w+')
#    for chunk in file.chunks():
#        destination.write(chunk)
#    destination.close()
#    if filename.endswith('.zip'):
#        os.system('unzip %s -d %s' % (file_path,dir_path))
#    return HttpResponse('ok')


@require_permission
def view_static(request):
    ''' 只让看指定的几个目录
    '''
    server_dir = request.GET.get('dir', '')
    if server_dir not in ('/static', '/static/html', '/static/html/image_ui'):
        return HttpResponse('Wrong remote directory: ' + server_dir)

    server_abs_dir = settings.BASE_ROOT + server_dir + '/'
    n = len(server_abs_dir)
    files = glob.glob(server_abs_dir + '*')

    mtime_dict = dict( [ (f, os.path.getmtime(f) ) for f in files ] )
    files.sort(key=lambda x: mtime_dict[x] )
    files.reverse()

    #filenames = [ f[n:] for f in files ]
    html_list = []
    for f_abs in files:
        f = f_abs[n:]   #filename only, no path

        if os.path.isdir( server_abs_dir + f):
            html_list += [ server_dir + '/' + f + ' >' ]
        else:
            html_list += [ 
                    str(datetime.datetime.fromtimestamp(mtime_dict[f_abs]))[:19] + ' <a href="' + server_dir + '/' + urlencode({'A':f})[2:] + '">' + server_dir + '/' + f + '</a>' ]

    return HttpResponse( '<br>'.join(html_list),  
            content_type="text/html; charset=UTF8" )



def cards_product_statistic(request):
    """元宝gacha武将产出统计
    """
    product_cards = []
    info = ""

    start_date = request.POST.get('start_date', '')
    end_date = request.POST.get('end_date', '')
    sort_by = request.POST.get('sort_by', 'star')

    if not (start_date and end_date):
        info = u"时间不能为空"
        return render_to_response('tool/cards_product_statistic.html', {'start_date': start_date, 'end_date': end_date, 'product_cards': product_cards , 'info': info, 'sort_by': sort_by}, RequestContext(request))
    
    table = app.secondary_log_mongo.mongo['cardproduct']

    start = utils.string_toDatetime(start_date, '%Y-%m-%d') 
    end = utils.string_toDatetime(end_date + ' 23:59:59') 

    # 判断时间间隔因该小于三天
    if -1 < (end - start).days < 3:
        match_query = {}
        match_query = {'date_time':{'$gte': start, '$lte': end},
                'where': {'$in': ['gacha_multi', 'gacha_charge']}
            }

        group_code = { "_id" : '$card_msg.cid', 'count':{"$sum" : 1}}

        product_cards = table.aggregate([{'$match': match_query}, {'$group': group_code}])['result']
        sum_count = sum([float(card['count']) for card in product_cards])
        product_cards = [{'name': game_config.card_config[card['_id']]['name'], 'cid': card['_id'], 'star': game_config.card_config[card['_id']]['star'], 'count': card['count'], 'rate': int(card['count']) * 100 / sum_count} for card in  product_cards]
        if sort_by:
            product_cards.sort(key=lambda card: card[sort_by], reverse=True)
    else:
        info = u"开始时间要不能大于结束时间， 间隔不能大于3天"

    return render_to_response('tool/cards_product_statistic.html', {'start_date': start_date, 'end_date': end_date, 'product_cards': product_cards , 'info': info, 'sort_by': sort_by}, RequestContext(request))


@require_permission
def bulletin(request):
    '''
    登录公告编辑助手
    '''
    action_result = ''

    id = request.GET.get('id','')
    if not id:
        id = request.POST.get('id', 0)
    id=id.strip()

    b = Bulletin.get_instance(id=id)

    all_pic = ['important.png', 'new.png']
    all_pic.sort()


    if request.POST.get('add_title','').strip():
        title = request.POST.get('title','').strip()
        img = request.POST.get('img','').strip()
        detail = request.POST.get('detail','').strip().replace(u'\u2028', '\n')
        b.add_title(title=title, img=img, detail=detail)
        b.generate_html()

    elif request.POST.get('edit_title','').strip():
        title_index = request.POST.get('title_index','').strip()
        b.data[int(title_index)]['publish_date'] = str( datetime.datetime.fromtimestamp( b.data[int(title_index)]['time'] ).date() )
        b.data[int(title_index)]['publish_time'] = str( datetime.datetime.fromtimestamp( b.data[int(title_index)]['time'] ).time() )[:8]

        data = {
                'all_pic': all_pic,
                'title_index': title_index,
                'title_max_index': len(b.data) - 1,
                'bulletin': b.data[int(title_index)],
                'id': id,
                }
        return 'tool/bulletin_edit.html', data

    elif request.POST.get('save_title','').strip():
        title_index = request.POST.get('title_index','').strip()
        d=b.data[ int(title_index) ]
        new_title_index = int(request.POST.get('new_title_index','').strip())

        if new_title_index < 0 or new_title_index >= len(b.data):
            return HttpResponse(u'错误的新的排序名次: ' + str(new_title_index) )


        d['title'] = request.POST.get('title','').strip()
        d['img'] = request.POST.get('img','').strip()

        title_color = request.POST.get('title_color','').strip()
        d['title_color'] = title_color

        d['detail'] = request.POST.get('detail','').strip().replace(u'\u2028', '\n')
        d['more_body'] = request.POST.get('more_body','').strip().replace(u'\u2028', '\n')
        d['more_title'] = request.POST.get('more_title','').strip().replace(u'\u2028', '\n')
        d['more_title_color'] = request.POST.get('more_title_color','').strip().replace(u'\u2028', '\n')

        #detail 与  more_body 要求 <div 与 </div>的数量必须相等， 因为
        #公告页的排版中，div很重要
        ldetail = d['detail'].lower()
        if ldetail.count('<div') != ldetail.count('</div>'):
            return HttpResponse('简介中的 &lt;div&gt; 与 &lt;/div&gt; 数量不匹配. div 对公告页的排版很重要, 请确保全部配对.')
        lmore_body = d['more_body'].lower()
        if lmore_body.count('<div') != lmore_body.count('</div>'):
            return HttpResponse('更多详情正文中的 &lt;div&gt; 与 &lt;/div&gt; 数量不匹配. div 对公告页的排版很重要, 请确保全部配对.')

        title_index = int(title_index)

        if title_index == new_title_index:
            pass
        else:
            d=copy.deepcopy(b.data[ int(title_index) ])
            #if title_index < new_title_index:
            del(b.data[title_index])
            b.data.insert(new_title_index, d)

        b.put()
        b.generate_html()

        action_result=u"数据已保存, 预览网页已生成."

    elif request.POST.get('update_online_bulletin','').strip():
        id = request.POST.get('id','0').strip()
        b.generate_html(online_or_preview='online', id=id)
        action_result=u"线上网页已经更新."

    elif request.POST.get('delete_title','').strip():
        title = request.POST.get('title','').strip()
        b.delete_title(title=title)
        b.generate_html()

    elif request.POST.get('update_html','').strip():
        b.generate_html()
        return HttpResponse('Done to update 0_notice.html and 1_notice.html')


    notice_files = ['0_notice_preview.html', '1_notice_preview.html']
    for i in range(total_notice_versions):
        notice_files += ['0_notice_v' + str(id) + '.html', 
                '1_notice_v' + str(id) + '.html'] 

    server_abs_dir = settings.STATIC_ROOT + 'html/'

    notice_mtime = {}
    for f in notice_files:
        if not os.path.exists( server_abs_dir+f ):
            notice_mtime[ f[:-5] ] = ''
            continue
        notice_mtime[ f[:-5] ] = str(datetime.datetime.fromtimestamp( os.path.getmtime(server_abs_dir+f) ) )[:19]

    data = {'bulletins': b.data, 
            'all_pic': all_pic,
            'action_result': action_result,
            'notice_mtime': notice_mtime,
            'id': id,
            'notice_versions': range(total_notice_versions),
            '0_notice_file_head': '0_notice_v' + str(id),
            '1_notice_file_head': '1_notice_v' + str(id),
            }

    return 'tool/bulletin.html', data
