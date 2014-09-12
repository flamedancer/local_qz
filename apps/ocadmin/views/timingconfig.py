# -*- encoding: utf-8 -*-  

from django.http import HttpResponse
from apps.oclib.utils import rkjson as json
from apps.ocadmin.models.mongoconfig import MongoTimingConfig
from apps.ocadmin.views import process_response


server_names = ['A','B','C']


def get_system_config(request):
    #""" 得到系统设置定时界面的内容
    #"""
    data = {}
    #得到维护开关
    system_maintance_obj = MongoTimingConfig.get('system_maintance_config')
    if system_maintance_obj is None:
        system_maintance_obj = MongoTimingConfig.create('system_maintance_config')
    system_maintance_flag = False
    data['system_maintance'] = {}
    for server_name in server_names:
        if server_name not in system_maintance_obj.data:
            system_maintance_obj.data[server_name] = False
            system_maintance_flag = True
        data['system_maintance'][server_name] = system_maintance_obj.data[server_name]
    
    #得到维护白名单
    system_white_flag = False
    data['system_white'] = {}
    system_white_obj = MongoTimingConfig.get('system_white_config')
    if system_white_obj is None:
        system_white_obj = MongoTimingConfig.create('system_white_config')
    for server_name in server_names:
        if server_name not in system_white_obj.data:
            system_white_obj.data[server_name] = []
            system_white_flag = True
        data['system_white'][server_name] = system_white_obj.data[server_name]
    
    #公告
    #定时公告
    #跑马灯内容设定
    #游戏设定
    system_configs = [('stamina_recover_time', u"设定体力恢复时间："),
                      ('friend_help_user_num', u"援军数量上限设置："),
                      ('friend_gacha_pt', u"好友援军点设置："),
                      ('other_help_user_num', u"义军数量上限设置："),
                      ('other_gacha_pt', u"义军援军点设置："),
                      ('revive_coin', u"复活需要的元宝数量："),
                      ('recover_stamina_coin', u"回复体力需要的元宝数量："),
                      ('dungeon_clear_coin', u"首次通关元宝奖励："),
                      ('card_extend_num', u"扩充军营设置："),
                      ('card_extend_coin', u"扩展军营消耗的元宝数量："),
                      ('max_card_num', u"军营武将上限设置："),
                      ('free_stamina_cnt', u"失败免体力次数设置："),
                      ('bg_change', u"场景切换："),
                      ('tranform_divider', u"英雄军魂设置："),
                      ('newbie_days', u"新手失败体力设置："),
                      ]
    data['system_configs'] = {}
    system_configs_flag = False
    system_configs_obj = MongoTimingConfig.get('system_configs')
    if system_configs_obj is None:
        system_configs_obj = MongoTimingConfig.create('system_configs')
    for tup_config in system_configs:
        config_en = tup_config[0]
        config_cn = tup_config[1]
        if tup_config not in system_configs_obj.data:
            system_configs_obj.data[config_en] = {}
            system_configs_flag = True
        for server_name in server_names:
            if server_name not in system_configs_obj.data[config_en]:
                system_configs_obj.data[config_en][server_name] = {}
                system_configs_obj.data[config_en][server_name]['value'] = ''
                system_configs_obj.data[config_en][server_name]['start_time'] = ''
                system_configs_obj.data[config_en][server_name]['end_time'] = ''
                system_configs_obj.data[config_en][server_name]['config_cn'] = config_cn
                system_configs_flag = True
    data['system_configs'] = system_configs_obj.data
                
    #托管战斗开关
    data['system_auto_fight'] = {}
    system_fight_flag = False
    system_fight_obj = MongoTimingConfig.get('system_auto_fight')
    if system_fight_obj is None:
        system_fight_obj = MongoTimingConfig.create('system_auto_fight')
    for server_name in server_names:
        if server_name not in system_fight_obj.data:
            system_fight_obj.data[server_name] = {}
            system_fight_obj.data[server_name]['auto_fight_is_open'] = True
            system_fight_obj.data[server_name]['start_time'] = ''
            system_fight_obj.data[server_name]['end_time'] = ''
            system_fight_obj.data[server_name]['auto_fight_no_charge'] = True
            system_fight_flag = True
    data['system_auto_fight'] = system_fight_obj.data
    
    #推送信息
    data['system_push'] = {}
    system_push_flag = False
    system_push_obj = MongoTimingConfig.get('system_push_config')
    if system_push_obj is None:
        system_push_obj = MongoTimingConfig.create('system_push_config')
    for server_name in server_names:
        if server_name not in system_push_obj.data:
            system_push_obj.data[server_name]= {}
            system_push_flag = True
    data['system_push'] = system_push_obj.data
    
    if system_maintance_flag is True:
        system_maintance_obj.put()
    if system_white_flag is True:
        system_white_obj.put()
    if system_configs_flag is True:
        system_configs_obj.put()
    if system_fight_flag is True:
        system_fight_obj.put()
    if system_push_flag is True:
        system_push_obj.put()
        
        
    return process_response(HttpResponse(
        json.dumps(data, indent=1),
        content_type='application/x-javascript',
    ))
    