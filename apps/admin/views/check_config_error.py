#!/usr/bin/python
#coding:utf-8

# 这一步， 在 32-bit Ubuntu 12.04上 (同时装了 mongodb 与 redis)， 页面容易卡死。
# 手动删除 python function 中的大list, 好像略有帮助， 但仍有卡死的情况。
# nginx已开了8个process, Django/uWsgi 也开了8个process. 原因待查。
# 直到redis-server restart后，才好。
# 在 aliyun 的 64-bit CentOS 5.7 上， 基本没出现页面卡死的问题。

#from apps.config.game_config import game_config
from apps.models.config import Config
from pprint import pformat

def check_config_error():
    # on my 32-bit Unbuntu 12.04, redis often problem, stop to response.
    # Is it redis problem, or python didn't delete some large-memory variable?
    # Let me try to delete variables manually -- helps a little
    # Or due to Redis put some config on disk, need upload from Mongo ?

    result = ''

    d = check_missing_card()
    for conf_name in d:
        d[conf_name] = [ s+'_card' for s in d[conf_name] ]
    if d:
        result += '<p>card_config 缺少武将编号: <pre>' + pformat(d) + '</pre>'

    d = check_missing_monster()
    for conf_name in d:
        d[conf_name] = [ s+'_monster' for s in d[conf_name] ]
    if d:
        result += '<p>monster_config 缺少敌将编号: <pre>' + pformat(d) + '</pre>'
    if result:
        result = '<br><p><span style="color:red">配置错误</span> (暂时只检查了1分区的武将与敌将的缺失):' + result 
        result += '''</p> <p style="color:gray"><br> * 只查了缺失, 未查逻辑错误， 详见: admin/views/check_config_error.py .</p>'''

    return  result




def check_missing_card():
    ''' Check various config, to see, if there is any card_id,
        not in card_config

        ####_card
        'drop_card_lv'

    '''
    #check '1' for now, do other subarea later


    card_related_configs = ['gacha_config', \
         'monster_config', 'user_init_config', 
         ] 

    good_card_numbers = [cid[:-5] for cid in eval(Config.get('card_config_1').data)]

    #something wrong
    if good_card_numbers == []:
        return {}    

    wrong_dict = {}

    for config_name in card_related_configs:
        #print '#### missing_card: config_name=', config_name
        config_obj = Config.get(config_name + '_1')
        if not config_obj:
            continue

        tmp = config_obj.data.split('_card')
        if len(tmp) <= 1:
            continue


        #print '#### total _card=', len(tmp)-1

        #special python technique to speed up, 
        #since now slow on 32-bit ubuntu 12.04
        #list(set(list)) to get unique, C is faster then Python

        unique_card_num = []
        for i in range(len(tmp)-1):
            if tmp[i+1][0] not in ('"', "'"):
                continue
            iQuote = tmp[i].rfind( tmp[i+1][0] )
            if iQuote >= 0:
                card_num = tmp[i][iQuote+1:]
                unique_card_num += [card_num]

        del tmp #free large memory ?
        unique_card_num = set(unique_card_num)  #unique
        #print '#### unique _card=', len(unique_card_num)

        wrong_card_numbers = [ c_num for c_num in unique_card_num 
                if c_num not in good_card_numbers 
                    and c_num.isdigit() ]

        if wrong_card_numbers:
            wrong_dict[config_name] = wrong_card_numbers

    return wrong_dict



def check_missing_monster():
    ''' Check various config, to see, if there is any monster_id,
        not in monster_config

        ##_##_##_monster
    '''

    #check '1' for now, do other subarea later

    monster_related_configs = [ 'normal_dungeon_config', 
            ]

    good_monster_numbers = [mid[:-8] for mid in eval(Config.get('monster_config_1').data)]
    if not good_monster_numbers:
        return {}

    wrong_dict = {}

    for config_name in monster_related_configs:
        #print '#### missing_monster: config_name=', config_name

        #config = eval('game_config.' + config_name )
        config_obj = Config.get(config_name + '_1' )
        if not config_obj:
            continue

        tmp = config_obj.data.split('_monster')
        if len(tmp) <= 1:
            continue

        #print '#### total _monster=', len(tmp)-1

        #special python technique to speed up, 
        #since now slow on 32-bit ubuntu 12.04
        #list(set(list)) to get unique, C is faster then Python

        unique_monster_num = []
        for i in range(len(tmp)-1):
            if tmp[i+1][0] not in ('"', "'"):
                continue
            iQuote = tmp[i].rfind( tmp[i+1][0] )
            if iQuote >= 0:
                monster_num = tmp[i][iQuote+1:]
                unique_monster_num += [monster_num]

        del tmp #free large memory ?

        unique_monster_num = set(unique_monster_num)  #unique
        #print '#### unique _monster=', len(unique_monster_num)

        wrong_monster_numbers = [ m_num for m_num in unique_monster_num 
                if m_num not in good_monster_numbers 
                    and m_num.replace('_', '').isdigit() ]


        if wrong_monster_numbers:
            wrong_dict[config_name] = wrong_monster_numbers

    return wrong_dict

