#!/usr/bin/env python
#-*- coding: utf-8 -*-

import traceback
import sys
try:
    import xlrd
except:
    pass

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse


game_config_name_list = [
#('system_config',u'系统配置'),
#('loginbonus_config',u'每日登录礼物'),
#('shop_config',u'商店配置'),
#('tutorial_config',u'新手引导配置'),
('user_level_config',u'用户等级参数配置'),
('gacha_config',u'gacha求将配置'),
('card_config',u'武将设置'),
('card_level_config',u'武将等级配置'),
('gift_config',u'礼品码配置'),
#('card_update_config',u'武将强化配置'),
('skill_config',u'武将技配置'),
('leader_skill_config',u'主将技配置'),
('monster_config',u'敌将配置'),
('monster_group_config',u'敌将分组配置'),
('normal_dungeon_config',u'普通战场配置'),
('box_config',u'宝箱配置'),
('normal_dungeon_effect_config',u'普通战场效果配置'),
('special_dungeon_config',u'限时活动战场配置'),
('weekly_dungeon_config',u'每周活动战场配置'),
('pvp_config',u'pvp竞技场配置'),
#('msg_config',u'提示语配置'),
#('language_config',u'语言包配置'),
#('compgacha_config',u'集卡换将配置'),
('equip_config',u'装备配置'),
('city_config',u'城镇配置'),
('item_config',u'药品配置'),
('props_config',u'道具配置'),
('material_config',u'材料配置'),
('material_desc_config',u'材料描述配置'),
('item_desc_config',u'药品描述配置'),
('props_desc_config',u'道具描述配置'),
('card_desc_config',u'武将描述配置'),
('equip_desc_config',u'装备描述配置'),
('skill_desc_config',u'技能描述配置'),
('dungeon_desc_config',u'战场描述配置'),
('fate_conf',u'缘分配置'),
('user_vip_conf',u'VIP参数配置'),
('equip_exp_conf',u'装备等级'),
]

config_list = [
'normal_dungeon_config',
'box_config',
'card_config',
'special_dungeon_config',
'monster_config',
'user_level_config',
'compgacha_config',
'equip_config',
'item_config',
'city_config',
'material_config',
'material_desc_config',
'item_desc_config',
'card_desc_config',
'equip_desc_config',
'skill_desc_config',
'dungeon_desc_config',
'monster_group_config',
'pvp_config',
'gacha_config',
'card_level_config',
'weekly_dungeon_config',
'skill_config',
'leader_skill_config',
'gift_config',
'fate_conf',
'user_vip_conf',
'props_config',
'equip_exp_conf',
]

def makegameconfig(request):
    """
    自动生成配置
    """
    data = {}
    config_name = request.GET.get('config_name')
    data['config_name'] = config_name
    data['game_config_name_list'] = game_config_name_list
    return render_to_response('admin/makegameconfig.html', data, context_instance = RequestContext(request))

def is_dict(request):
    if request.method == 'POST':
        dict_value = request.POST['dict_value'].encode('utf-8').replace('\r','').strip()
        try:
            dict_config = eval(dict_value)
            data_dict = print_dict(dict_config, '')
            config_name = request.GET.get('config_name')
            data = {}
            data['config_name'] = 'system_config'
            data['game_config_name_list'] = game_config_name_list
            data['data'] = data_dict
            return render_to_response('admin/makegameconfig.html', data, context_instance = RequestContext(request))
        except Exception,e:
            traceback.print_exc(file=sys.stderr)
            return HttpResponse(traceback.format_exc())

def make_single_config_old(request):
    from apps.admin.views.makegameconfig_old import make_config as make_config_old
    data = {}
    config_name = request.GET.get('config_name')
    data['config_name'] = config_name
    data['game_config_name_list'] = game_config_name_list
    if not config_name in config_list:
        data['data'] = 'developering...'
    else:
        data['data'] = make_config_old(request, config_name)

    return render_to_response('admin/makegameconfig.html', data, context_instance = RequestContext(request))

def make_single_config(request):
    data = {}
    config_name = request.GET.get('config_name')
    data['config_name'] = config_name
    data['game_config_name_list'] = game_config_name_list
    if not config_name in config_list:
        data['data'] = 'developering...'
    else:
        data['data'] = make_config(request, config_name)
    return render_to_response('admin/makegameconfig.html', data, context_instance = RequestContext(request))

def make_config(request, config_name):
    try:
        data_string = ''
        filename = request.FILES.get('xls', None)
        excel = xlrd.open_workbook(file_contents = filename.read());
        sheet = excel.sheet_by_name(config_name)
        data_string = globals()[config_name](sheet)
        # data_string += {
        #     'special_dungeon_config': lambda: special_dungeon_config(sheet),
        #     'dungeon_config': lambda: dungeon_config(sheet),
        #     'card_config': lambda: card_config(sheet),
        #     'monster_config': lambda: monster_config(sheet),
        #     'user_level_config': lambda: user_level_config(sheet),
        #     'compgacha_config': lambda: compgacha_config(sheet),
        #     'equip_config': lambda: equip_config(sheet),
        #     'item_config': lambda: item_config(sheet),
        #     'city_config': lambda: city_config(sheet),
        #     'material_config': lambda: material_config(sheet),
        #     'material_desc_config': lambda: material_desc_config(sheet),
        #     'item_desc_config': lambda: item_desc_config(sheet),
        #     'card_desc_config': lambda: card_desc_config(sheet),
        #     'equip_desc_config': lambda: equip_desc_config(sheet),
        #     'skill_desc_config': lambda: skill_desc_config(sheet),
        #     'dungeon_desc_config': lambda: dungeon_desc_config(sheet),
        #     'box_config': lambda: box_config(sheet),
        #     'monster_group_config':lambda: monster_group_config(sheet),
        #     'pvp_config':lambda: pvp_config(sheet),
        #     'gacha_config':lambda: gacha_config(sheet),
        #     'card_level_config':lambda: card_level_config(sheet),
        #     'weekly_dungeon_config':lambda: weekly_dungeon_config(sheet),
        #     'skill_config':lambda: skill_config(sheet),
        #     'leader_skill_config':lambda: leader_skill_config(sheet),
        #     'fate_conf': lambda: fate_config(sheet),
        #     'props_config':lambda: props_config(sheet),
        #     'props_desc_config':lambda: props_desc_config(sheet),
        #     'user_vip_conf': lambda: user_vip_config(sheet),
        #     'equip_exp_conf': lambda: equip_exp_config(sheet),
        # }[config_name]()
        return str(data_string)
    except Exception,e:
        traceback.print_exc(file=sys.stderr)
        return traceback.format_exc()

def fate_config(sheet):
    indented = ''
    fate_config = make_dict(sheet)
    sort_keys = [ 'ch_%s' % tag for tag in sorted([int(i.split('_')[1]) for i in fate_config])]
    fate_config_string = "{\n" + print_dict(fate_config, indented,sort_keys) + "\n}"
    return fate_config_string

def props_config(sheet):
    indented = ''
    props_config = make_dict(sheet)
    props_config_string = "{\n" + print_dict(props_config, indented) + "\n}"
    return props_config_string

def props_desc_config(sheet):
    indented = ''
    props_desc_config = make_dict(sheet)
    props_desc_config_string = "{\n" + print_dict(props_desc_config, indented) + "\n}"
    return props_desc_config_string

def user_vip_config(sheet):
    indented = ''
    user_vip_config = make_dict(sheet)
    user_vip_config_string = "{\n" + print_dict(user_vip_config, indented) + "\n}"
    return user_vip_config_string

def equip_exp_config(sheet):
    indented = ''
    equip_exp_config = make_dict(sheet)
    equip_exp_config_string = "{\n" + print_dict(equip_exp_config, indented) + "\n}"
    return equip_exp_config_string

def skill_config(sheet):
    indented = ''
    skill_config = make_dict(sheet)
    sort_keys = [ '%s_skill' % tag for tag in sorted([int(i.split('_')[0]) for i in skill_config])]
    skill_config_string = "{\n" + print_dict(skill_config, indented,sort_keys) + "\n}"
    return skill_config_string

def leader_skill_config(sheet):
    indented = ''
    leader_skill_config = make_dict(sheet)
    leader_skill_config_string = "{\n" + print_dict(leader_skill_config, indented) + "\n}"
    return leader_skill_config_string

def item_config(sheet):
    indented = ''
    item_config = make_dict(sheet)
    sort_keys = [ '%s_item' % tag for tag in sorted([int(i.split('_')[0]) for i in item_config])]
    item_config_string = "{\n" + print_dict(item_config, indented,sort_keys) + "\n}"
    return item_config_string

def city_config(sheet):
    indented = ''
    city_config = make_dict(sheet)
    city_config_string = "{\n" + print_dict(city_config, indented) + "\n}"
    return city_config_string

def material_config(sheet):
    indented = ''
    material_config = make_dict(sheet)
    sort_keys = [ '%s_mat' % tag for tag in sorted([int(i.split('_')[0]) for i in material_config])]
    material_config_string = "{\n" + print_dict(material_config, indented,sort_keys) + "\n}"
    return material_config_string

def material_desc_config(sheet):
    indented = ''
    material_config = make_dict(sheet)
    sort_keys = [ '%s_mat' % tag for tag in sorted([int(i.split('_')[0]) for i in material_config])]
    material_config_string = "{\n" + print_dict(material_config, indented,sort_keys) + "\n}"
    return material_config_string

def card_desc_config(sheet):
    indented = ''
    card_desc_config = make_dict(sheet)
    sort_keys = [ '%s_card' % tag for tag in sorted([int(i.split('_')[0]) for i in card_desc_config])]
    card_config_string = "{\n" + print_dict(card_desc_config, indented,sort_keys) + "\n}"
    return card_config_string

def equip_desc_config(sheet):
    indented = ''
    equip_desc_config = make_dict(sheet)
    sort_keys = [ '%s_equip' % tag for tag in sorted([int(i.split('_')[0]) for i in equip_desc_config])]
    equip_config_string = "{\n" + print_dict(equip_desc_config, indented,sort_keys) + "\n}"
    return equip_config_string

def item_desc_config(sheet):
    indented = ''
    item_desc_config = make_dict(sheet)
    sort_keys = [ '%s_item' % tag for tag in sorted([int(i.split('_')[0]) for i in item_desc_config])]
    item_config_string = "{\n" + print_dict(item_desc_config, indented,sort_keys) + "\n}"
    return item_config_string

def skill_desc_config(sheet):
    indented = ''
    skill_desc_config = make_dict(sheet)
    sort_keys_skill = [ '%s_skill' % tag for tag in sorted([int(i.split('_')[0]) for i in skill_desc_config if 'skill' in i])]
    sort_keys_leader = [ '%s_leader' % tag for tag in sorted([int(i.split('_')[0]) for i in skill_desc_config if 'leader' in i])]
    sort_keys_skill.extend(sort_keys_leader)
    skill_config_string = "{\n" + print_dict(skill_desc_config, indented,sort_keys_skill) + "\n}"
    return skill_config_string

def dungeon_desc_config(sheet):
    indented = ''
    dungeon_desc_config = make_dict(sheet)
    #sort_keys = [ '%s' % tag for tag in sorted([int(i) for i in dungeon_desc_config])]
    dun_config_string = "{\n" + print_dict(dungeon_desc_config, indented) + "\n}"
    return dun_config_string

def box_config(sheet):
    indented = ''
    box_config = make_dict(sheet)
    key_sum = {}
    no_sort_keys=[]
    for i in box_config:
        tmp = 0
        length = len(i.split('_'))
        try:
            for position,j in enumerate(i.split('_')):
                tmp += int(j) * 100**(length-position)
            key_sum[tmp] = i
        except:
            no_sort_keys.append(i)
        
    sort_keys = [ key_sum[i] for i in sorted(key_sum.keys())]
    sort_keys = sort_keys + sorted(no_sort_keys)
    box_config_string = "{\n" + print_dict(box_config, indented,sort_keys) + "\n}"
    return box_config_string

def special_dungeon_config(sheet):
    indented = ''
    special_dungeon_config = make_dict(sheet)
    sort_keys = [ '%s' % tag for tag in sorted([int(i) for i in special_dungeon_config])]
    special_dungeon_config_string = "{\n" + print_dict(special_dungeon_config, indented,sort_keys) + "\n}"
    return special_dungeon_config_string

def weekly_dungeon_config(sheet):
    indented = ''
    weekly_dungeon_config = make_dict(sheet)
    sort_keys = [ '%s' % tag for tag in sorted([int(i) for i in weekly_dungeon_config])]
    weekly_dungeon_config_string = "{\n" + print_dict(weekly_dungeon_config, indented,sort_keys) + "\n}"
    return weekly_dungeon_config_string

def dungeon_config(sheet):
    indented = ''
    dungeon_config = make_dict(sheet)
    sort_keys = [ '%s' % tag for tag in sorted([int(i) for i in dungeon_config])]
    dungeon_config_string = "{\n" + print_dict(dungeon_config, indented,sort_keys) + "\n}"
    return dungeon_config_string

def card_config(sheet):
    indented = ''
    card_config = make_dict(sheet)
    sort_keys = [ '%s_card' % tag for tag in sorted([int(i.split('_')[0]) for i in card_config])]
    card_config_string = "{\n" + print_dict(card_config, indented,sort_keys) + "\n}"
    return card_config_string

def monster_group_config(sheet):
    indented = ''
    monster_group_config = make_dict(sheet)
    key_sum = {}
    no_sort_keys = []
    for i in monster_group_config:
        tmp = 0
        length = len(i.split('_'))
        try:
            for position,j in enumerate(i.split('_')):
                tmp += int(j) * 100**(length-position)
            key_sum[tmp] = i
        except:
            no_sort_keys.append(i)
    sort_keys = [ key_sum[i] for i in sorted(key_sum.keys())]
    sort_keys = sort_keys + sorted(no_sort_keys)
    monster_config_string = "{\n" + print_dict(monster_group_config, indented,sort_keys) + "\n}"
    return monster_config_string

def pvp_config(sheet):
    indented = ''
    pvp_config = make_dict(sheet)
    pvp_config_string = "{\n" + print_dict(pvp_config, indented) + "\n}"
    return pvp_config_string

def has_cell2(cell2):
    if cell2 == '':
        return False
    else:
        return True

def monster_config(sheet):
    indented = ''
    monster_config = make_dict(sheet)
    sort_keys = sorted(monster_config.keys())
    monster_config_string = "{\n" + print_dict(monster_config, indented,sort_keys) + "\n}"
    return monster_config_string

def user_level_config(sheet):
    indented = ''
    user_level_config = make_dict(sheet)
    sort_keys = [ '%s' % tag for tag in sorted([int(i) for i in user_level_config])]
    user_level_config_string = "{\n" + print_dict(user_level_config, indented,sort_keys) + "\n}"
    return user_level_config_string

def gacha_config(sheet):
    indented = '\t'
    gacha_config = make_dict(sheet)
    gacha_config_string = "{\n" + print_dict(gacha_config, indented) + "\n}"
    return gacha_config_string

def card_level_config(sheet):
    indented = '\t'
    card_level_config = make_dict(sheet)
    card_level_config_string = "{\n" + print_dict(card_level_config, indented) + "\n}"
    return card_level_config_string

def compgacha_config(sheet):
    indented = '\t'
    compgacha_config = make_dict(sheet)
    compgacha_config_string = "{\n" + print_dict(compgacha_config, indented) + "\n}"
    return compgacha_config_string

def equip_config(sheet):
    indented = ''
    equip_config = make_dict(sheet)
    sort_keys = [ '%s_equip' % tag for tag in sorted([int(i.split('_')[0]) for i in equip_config])]
    equip_config_string = "{\n" + print_dict(equip_config, indented,sort_keys) + "\n}"
    return equip_config_string


def make_dict(sheet):
    make_dict = {}
    first_columu = sheet.col_values(0)
    first_row = sheet.row_values(0)
    for j in range(1, len(first_columu)):
        keys = sheet.cell(j,0).value
        values = sheet.cell(j,1).value
        type_cell = sheet.cell(j,2).value
        keys_list = keys.split('>')
        set_key_value(keys_list, values, make_dict, type_cell)
    return make_dict

def print_dict(values, indented,sort_keys = None):
    dict_string = ''
    indented += '    '
    # key = max([i.split('_')[0] for i in values.keys()])
    for keys in sort_keys if sort_keys else values:
#        if isinstance(keys, str):
        walk_values = values[keys]
        if isinstance(keys, str):
            keys_extend = "'" + keys + "'"
        else:
            keys_extend = str(keys)

        if isinstance(walk_values, dict):
            dict_string += indented + keys_extend  + ":{\n"
            try:
                next_sort_keys = [str(i) for i in sorted([ int(i) for i in walk_values.keys()])]
            except:
                next_sort_keys = None
            dict_string += print_dict(walk_values, indented,next_sort_keys)
            dict_string += indented + "},\n"
        elif isinstance(walk_values, str):
            dict_string += indented + keys_extend + ":'" + walk_values + "',\n"
        elif isinstance(walk_values, (int, float)):
            dict_string += indented + keys_extend + ":" + str(walk_values) + ",\n"
        elif isinstance(walk_values, unicode):
            walk_values = walk_values.encode('utf-8')
            dict_string += indented + keys_extend + ":unicode('" + walk_values + "','utf-8'),\n"
        elif isinstance(walk_values, list):
            dict_string += indented + keys_extend + ":" + str(walk_values) + ",\n"

    return dict_string

def set_key_value(keys_list, values, make_dict, type_value):
    walk_dict = make_dict
    count = 0
    for key in keys_list:
        key = str(key)
        count += 1
        if not key in walk_dict:
            walk_dict[key] = {}
            if count == len(keys_list):
                if type_value == 'bool':
                    if values == 1:
                        walk_dict[key] = True
                    else:
                        walk_dict[key] = False
                elif type_value == 'list':
                    walk_dict[key] = eval(values)
                elif type_value == 'str':
                    walk_dict[key] = str(values)
                elif type_value == 'float':
                    values = str(values).replace("'", "")
                    walk_dict[key] = float(values)
                elif type_value == 'int':
                    walk_dict[key] = int(values)
                elif type_value == 'unicode':
                    walk_dict[key] = values
        walk_dict = walk_dict[key]
