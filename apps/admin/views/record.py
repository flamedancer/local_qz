#-*- coding:utf-8 -*-
import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext

from apps.common import record
from apps.config.game_config import game_config
from apps.admin.decorators import require_permission


@require_permission
def index(request):
    """
    查询首页
    """
    view_type = request.GET.get("type",'')
    if view_type == 'charge':
        item_info = game_config.shop_config['sale'].items()
        item_info.sort(key = lambda x:x[1]['num'])
        return 'record/index.html', {"view_type":view_type,"item_info":item_info}

    return 'record/index.html', {"view_type":view_type}


@require_permission
def consume(request):
    """
    查询消费记录
    """
    data = consume_data(request)
    return 'record/result.html' ,data


@require_permission
def charge(request):
    """
    查询充值记录
    """
    uid = request.POST.get('uid','').strip()
    start_date = request.POST.get('start_date','')
    end_date = request.POST.get('end_date','')
    platform = request.POST.get('platform','')
    item_id = request.POST.get('item_id','')
    charge_way = request.POST.get('charge_way','all')
    item_info = game_config.shop_config['sale'].items()
    item_info.sort(key = lambda x:x[1]['num'])
    result = record.get_charge_record(uid,start_date,end_date,platform,item_id,charge_way)
    result_by_date = {}
    total_price = 0
    total_count = 0
    for row in result:
        date_str = row['_id'].split(' ')[0]
        row['_id'] += ':00'
        row['charge_time'] = row['_id']
        if date_str not in result_by_date:
            result_by_date[date_str] = {
                'record':[],
                'total_price':0,
                'total_count':0,
            }
        result_by_date[date_str]['record'].append(row)
        result_by_date[date_str]['total_count'] += row['charge_count']
        result_by_date[date_str]['total_price'] += row['charge_sum']
        total_count += row['charge_count']
        total_price += row['charge_sum']
    data = {
        'item_info':item_info,
        'uid':uid,
        'start_date':start_date,
        'end_date':end_date,
        'item_id':item_id,
        'platform':platform,
        'result':sorted([(k,v) for k,v in result_by_date.items()]),
        'view_type':'charge',
        'total_price':total_price,
        'total_count':total_count,
        "charge_way":charge_way,
    }
    return 'record/result.html', data


@require_permission
def consume_contrast(request):
    """
    对比消费记录
    """
    data = consume_data(request)

    second_start = request.POST.get('second_start','')
    f_start_obj = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d")
    f_end_obj = datetime.datetime.strptime(data['end_date'], "%Y-%m-%d")
    s_start_obj = datetime.datetime.strptime(second_start, "%Y-%m-%d")
    s_end_obj = s_start_obj + (f_end_obj - f_start_obj)
    second_end = s_end_obj.strftime("%Y-%m-%d")
    second_data = consume_data(request, second_start, second_end)
    second_dict = {}
    count_contrast_result = 0
    sum_contrast_result = 0

    for date_l in range(len(second_data['result'])):
        second_infos = second_data['result'][date_l]
        total_count = second_infos[1]['total_count']
        total_sum = second_infos[1]['total_sum']
        second_dict[second_infos[0]] = {'total_count':total_count,'total_sum':total_sum,}

    for date in range(len(data['result'])):
        infos = data['result'][date]
        date_str = infos[0]
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        date_contrast_obj = date_obj + (s_start_obj - f_start_obj)

        date_contrast_str = date_contrast_obj.strftime("%Y-%m-%d")
        if not date_contrast_str in second_dict:
            infos[1]['total_count_contrast'] = infos[1]['total_count']
            infos[1]['total_sum_contrast'] = infos[1]['total_sum']
            infos[1]['second_total_sum'] = 0
            infos[1]['second_total_count'] = 0
            count_contrast_result += infos[1]['total_count_contrast']
            sum_contrast_result += infos[1]['total_sum_contrast']
        else:
            infos[1]['total_count_contrast'] = infos[1]['total_count'] - second_dict[date_contrast_str]['total_count']
            infos[1]['total_sum_contrast'] = infos[1]['total_sum'] - second_dict[date_contrast_str]['total_sum']
            infos[1]['second_total_sum'] = second_dict[date_contrast_str]['total_sum']
            infos[1]['second_total_count'] = second_dict[date_contrast_str]['total_count']
            count_contrast_result += infos[1]['total_count_contrast']
            sum_contrast_result += infos[1]['total_sum_contrast']

        infos[1]['data_contrast'] = date_contrast_str
    data['view_type'] = 'consume_contrast'
    data['second_total_sum'] = second_data['total_sum']
    data['second_total_count'] = second_data['total_count']
    data['count_contrast_result'] = count_contrast_result
    data['sum_contrast_result'] = sum_contrast_result
    return 'record/result.html', data


def consume_data(request, start_date = '', end_date = ''):
    """消费记录数据返回
    """
    uid = request.POST.get('uid','').strip()
    if not start_date:
        start_date = request.POST.get('start_date','')
    if not end_date:
        end_date = request.POST.get('end_date','')
    consume_type = request.POST.get('consume_type','')
    result = record.get_consume_record(uid,start_date,end_date,consume_type)
    result_by_date = {}
    total_sum = 0
    total_count = 0
    for row in result:
        date_str = row['_id'].split(' ')[0]
        row['_id'] += ':00'
        row['item_time'] = row['_id']
        if date_str not in result_by_date:
            result_by_date[date_str] = {
                'record':[],
                'total_count':0,
                'total_sum':0,
            }
        result_by_date[date_str]['record'].append(row)
        result_by_date[date_str]['total_count'] += row['item_count']
        result_by_date[date_str]['total_sum'] += row['item_sum']
        total_count += row['item_count']
        total_sum += row['item_sum']
    data = {
        'uid':uid,
        'start_date':start_date,
        'end_date':end_date,
        'consume_type':consume_type,
        'result':sorted([(k,v) for k,v in result_by_date.items()]),
        'view_type':'consume',
        'total_sum':total_sum,
        'total_count':total_count,
    }
    return data
