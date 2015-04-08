#!/usr/bin/env python
#-*- coding: utf-8 -*-

import xlrd
import traceback
import sys
from apps.admin.decorators import require_permission
from apps.models.config import Config
from apps.config import config_list


canuse_config_list = [
    'system_config',
]

class XlsToDict(object):

    def __init__(self):
        self.str_cnames = []
        self.int_cnames = []
        self.dict_cnames = []
        self.list_cnames = []
        self.bool_cnames = []
        self.data_string = '{\n'
        self.indentation = 4

    def make_config(self, files, config_name):
        try:
            excel = xlrd.open_workbook(file_contents = files.read());
            sheet = excel.sheet_by_name(config_name)
            first_columu = sheet.col_values(0)
            first_row = sheet.row_values(0)
            self.data_string += self.indentation * ' '

            for i in range(1, len(first_columu)):
                keys        = sheet.cell(i,3).value
                keyorvalue_type    = sheet.cell(i,2).value
                description = sheet.cell(i,0).value
                values      = sheet.cell(i,1).value
                if keys in self.str_cnames:
                    self.make_type_str(keys, values, description)
                elif keys in self.int_cnames:
                    self.make_type_int(keys, values, description)
                elif keys.split('@')[0] in self.dict_cnames:
                    self.make_type_dict(keys, values, description, keyorvalue_type)
                elif keys in self.list_cnames:
                    self.make_type_list(keys, values, description)
                elif keys in self.bool_cnames:
                    self.make_type_bool(keys, values, description)
                else:
                    self.data_string += "Can not set " + keys
                    return self.data_string
            self.data_string += '\n}'
            return self.data_string
        except Exception,e:
            traceback.print_exc(file=sys.stderr)
            return traceback.format_exc()

    def make_type_str(self, keys, values, description=''):
        self.data_string += "'" + str(keys) + "': '" + str(values) + "',"
        if description:
            self.data_string += '#' + description 
        self.data_string += '\n'
        self.data_string += self.indentation * ' '
        return self.data_string

    def make_type_int(self, keys, values, description=''):
        if not values:
            values = '0'
        else:
            values = str(int(values))
        self.data_string += "'" + str(keys) + "': " + str(values) + ','
        if description:
            self.data_string += '#' + description
        self.data_string += '\n'
        self.data_string += self.indentation * ' '
        return self.data_string

    def make_type_dict(self, keys, values, description, keyorvalue_type):
        #属于哪个字典@key（如果不填，将往下第二格当做key）@{（在字符串的最后面添加一个‘{’）
        line_string = ''
        m, k, e = str(keys).split('@')
        if '{{' in e:
            self.data_string += "'" + m + "': {"
            if description:
                self.data_string += '#' + description
            self.data_string += '\n'
            self.indentation += 4
            line_string += self.indentation * ' '
        keyorvalue = keyorvalue_type.split('@')[0]
        kv_type    = keyorvalue_type.split('@')[1]
        #对上面k的操作
        if k:
            if '.' in k:
                ks = k.split('.')
                for _i, km in enumerate(ks):
                    line_string += km 
                    self.indentation += 4
                    if _i != (len(ks) - 1):
                        line_string += '{\n'
                        line_string += self.indentation * ' '
                    else:
                        self.indentation -= 4 * _i
            else:
                line_string += k
                if '{' in k:
                    line_string += '\n'
                    self.indentation += 4
                    line_string += self.indentation * ' '
        #对值的操作
        if keyorvalue in ['value']:
            end_values = self.makedicttype_tostring(values, kv_type)
            line_string += end_values + ',' 
            line_string = self.makedict_endstring(line_string, description, keyorvalue, e)
        #对key的操作
        elif keyorvalue in ['key:{']:
             line_string += self.makedicttype_tostring(values, kv_type) + ':{'
             line_string = self.makedict_endstring(line_string, description, keyorvalue, e)
        elif keyorvalue in ['key:']:
             line_string += self.makedicttype_tostring(values, kv_type) + ':'
             self.indentation -= 4
             line_string = self.makedict_endstring(line_string, description, keyorvalue, e)
        self.data_string += line_string
        return self.data_string

    def make_type_list(self, keys, values, description=''):
        spvalues = str(values).split(';')
        if description:
            self.data_string += '#' + description 
        self.data_string += '\n'
        list_values = "[\n"
        for sp in spvalues:
            if sp:
                list_values += self.indentation * ' ' + ' '*4 + "'" + sp + "', \n"
        list_values += self.indentation * ' ' + "]"
        self.data_string += self.indentation * ' ' + "'" + str(keys) + "': " + str(list_values) + ','
        self.data_string += '\n'
        self.data_string += self.indentation * ' '
        return self.data_string

    def make_type_bool(self, keys, values, description=''):
        if not values:
            values = 'False'
        if values == 1:
            values = 'True'
        self.data_string += "'" + str(keys) + "': " + str(values.lower().capitalize()) + ','
        if description:
            self.data_string += '#' + description 
        self.data_string += '\n'
        self.data_string += self.indentation * ' '
        return self.data_string

    def makedicttype_tostring(self, keyorvalue, type):
        if type in ['str']:
            if isinstance(keyorvalue, float):
                end_values = "'" + str(int(keyorvalue)) + "'"
            else:
                end_values = "'" + keyorvalue + "'"
        elif type in ['int']:
            end_values = keyorvalue
        elif type == 'unicode':
            end_values = "unicode('" + keyorvalue + "','utf-8')"
        elif type == 'tuple':
            end_values = "(" + keyorvalue + ")"
        else:
            end_values = "'" + 'Unknow type' + "'"
        return end_values

    def makedict_endstring(self, line_string, description, keyorvalue, e):
        if not keyorvalue in ['key:', ]:
            if description:
                line_string += '#' + description 
        if keyorvalue in ['key:{', ]:
            line_string += '\n'
            self.indentation += 4
            line_string += self.indentation * ' '
        elif keyorvalue in ['key:', ]:
            self.indentation += 4
        elif keyorvalue in ['value', ]:
            if e.count('}'):
                for i in range(0, e.count('}')):
                    self.indentation -= 4
                    line_string += '\n' + self.indentation * ' '+ '},\n'
                    line_string += self.indentation * ' ' 
            else:
                line_string += '\n'
                line_string += self.indentation * ' ' 
        return line_string

class System_config(XlsToDict):

    def __init__(self):
        XlsToDict.__init__(self)
        self.str_cnames  = ['version', 'review_version', 'app_url', 'bbs_url', 'notice', 'agreement', 'help', 'aboutus', 'app_comment_url', 'notice_in_review',
                            'gacha_notice_in_review', 'free_gacha_notice_in_review', 'free_gacha_notice', 
                           ]
        self.int_cnames  = ['oc_freeze_time', 'oc_freeze_num', 'tapjoy_max_coins', 'tapjoy_points_per_coin', 'stamina_recover_time', 'max_friend_request',
                            'login_record_length', 'deck_length', 'friend_help_user_num', 'friend_gacha_pt', 'other_help_user_num', 
                            'other_gacha_pt', 'revive_coin', 'dungeon_clear_coin', 'card_extend_num',
                            'free_stamina_cnt', 'tranform_divider', 'newbie_days', 'recover_copy_coin', 'bind_phone_cnt', 
                           ]
        self.dict_cnames = ['res_url_online', 'popularize', 'timing_notice_conf', 'push_info', 'you', 
                           ]
        self.list_cnames = ['allow_uids', 'help_links', 
                           ]
        self.bool_cnames = ['in_review', 'maintenance', 'server_close', 'fb_account', 'qq_account', 'sina_account', 'account_assign_switch', 'server_sig',
                            'tapjoy_fg', 'log_control', 'bind_phone_is_open', 'auto_fight_is_open', 'auto_fight_no_charge','popen', 'push_open', 'push_open_1', 
                           ]

@require_permission
def submit_game_settings_by_excel(request):
    data = {}
    config_name = str(request.GET.get('config_name'))
    subarea_default = request.POST.get('subarea_default')
    data['config_name'] = config_name

    str_subareas_confname = config_list.get_configname_by_subarea('subareas_conf', '1')
    subareas_conf = Config.get(str_subareas_confname)
    if not subareas_conf:
        subareas_conf = Config.create(str_subareas_confname)
    subareas_conf_dict = eval(subareas_conf.data)
    return_subareas_conf = []
    for key in sorted(subareas_conf_dict.keys()):
        return_subareas_conf.append((key, subareas_conf_dict[key]))

    if not config_name in canuse_config_list:
        data['config_value'] = make_config(request, config_name)
    else:
        x_func = eval(config_name.capitalize() +'()')
        files = request.FILES.get('xls', None)
        if not files:
            data['config_value'] = 'Miss files!'
        else:
            data['config_value'] = x_func.make_config(files, config_name)
    str_config_description = config_list.get_description(config_name)
    data['config_title'] = str_config_description
    data['subareas_conf'] = return_subareas_conf
    data['saved'] = False
    data['submit_game_settings_by_excel'] = True
    data['subarea_default'] = subarea_default

    return 'admin/game_setting.html', data

def _verify_game_config(config_name, value):
    #用于验证配置是否正确
    verify_dict = {
        'system_config': ['maintenance'],#key为配置名称，value为该配置名称必须存在的key
        'loginbonus_config': ['bonus'],
        'shop_config': ['sale'],
        'user_level_config': ['1'],
        'gacha_config': ['gold_rate', 'charge_rate',],
        'card_config': ['1_card', ],
        'card_level_config': ['exp_type', ],
        'card_update_config': ['cost_gold', ],
        'monster_config': [],
        'dungeon_config': ['1', ],
        'normal_dungeon_effect_config': ['rule', ],
    }

    verify_info = ''

    if config_name in verify_dict:
        for verify_value in verify_dict[config_name]:
            if not verify_value in value:
                verify_info = config_name + " miss '" + verify_value + "'"

    #战场掉落敌将，而在敌将配置中未配置的验证
    dcverify = _verify_dungeon_config(config_name, value)
    if dcverify:
        return dcverify

    return verify_info

def _verify_dungeon_config(config_name, value):
    """战场掉落敌将，而在敌将配置中未配置的验证"""
    if config_name == 'normal_dungeon_config':
        pass
        # for dungeon_floor in value:
        #     mdset = set(value[dungeon_floor]['monster_drop'].keys())
        #     mset = set(game_config.monster_config.keys())
        #     if mdset & mset != mdset:
        #         vdresult = mdset - (mdset & mset)
        #         if vdresult:
        #             for mid in vdresult:
        #                 return "敌将配置__monster_config 缺少配置ID：" + str(mid)
    return ''

def make_config(request, config_name):
    try:
        if config_name.endswith('_conf'):
            config_name = config_name + 'ig'
        data_string = ''
        filename = request.FILES.get('xls', None)
        excel = xlrd.open_workbook(file_contents = filename.read());
        sheet = excel.sheet_by_name(config_name)
        data_string = globals().get(config_name, defuault_excel_explain)(sheet)
        return str(data_string)
    except Exception,e:
        traceback.print_exc(file=sys.stderr)
        return traceback.format_exc()

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

def set_key_value(keys_list, values, make_dict, type_value):
    walk_dict = make_dict
    count = 0
    try:
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
                    elif type_value == 'tuple':
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
    except Exception, e:
        print e
        reload(sys)
        sys.setdefaultencoding( "utf-8" )
        error_msg = u"THE ERROR LINE IS:     {}, {}, {}".format(unicode(key), unicode(values), unicode(type_value))
        print error_msg, type_value
        raise ValueError(error_msg)

def print_dict(values, indented,sort_keys = None):
    dict_string = ''
    indented += '    '
    for keys in sort_keys if sort_keys else values:
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
                try:
                    next_sort_keys = [str(i) for i in sorted([ i for i in walk_values.keys()])]
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
        elif isinstance(walk_values, tuple):
            dict_string += indented + keys_extend + ":" + str(walk_values) + ",\n"

    return dict_string


def defuault_excel_explain(sheet):
    indented = '\t'
    config = make_dict(sheet)
    config_string = "{\n" + print_dict(config, indented) + "\n}"
    return config_string


def fate_config(sheet):
    #缘分配置的上传函数
    indented = ''
    fate_config = make_dict(sheet)
    sort_keys = [ 'ch_%s' % tag for tag in sorted([int(i.split('_')[1]) for i in fate_config])]
    fate_config_string = "{\n" + print_dict(fate_config, indented,sort_keys) + "\n}"
    return fate_config_string

def props_config(sheet):
    #道具配置的上传函数
    indented = ''
    props_config = make_dict(sheet)
    sort_keys = [ '%s_props' % tag for tag in sorted([int(i.split('_')[0]) for i in props_config])]
    props_config_string = "{\n" + print_dict(props_config, indented,sort_keys) + "\n}"
    return props_config_string

def drop_info_config(sheet):
    #战场掉落的上传函数
    indented = ''
    drop_info_config = make_dict(sheet)
    drop_info_config_string = "{\n" + print_dict(drop_info_config, indented) + "\n}"
    return drop_info_config_string

def dungeon_world_config(sheet):
    #战场世界的上传函数
    indented = ''
    dungeon_world_config = make_dict(sheet)
    dungeon_world_config_string = "{\n" + print_dict(dungeon_world_config, indented) + "\n}"
    return dungeon_world_config_string

def daily_dungeon_config(sheet):
    #每日战场的上传函数
    indented = ''
    daily_dungeon_config = make_dict(sheet)
    daily_dungeon_config_string = "{\n" + print_dict(daily_dungeon_config, indented) + "\n}"
    return daily_dungeon_config_string

def explore_config(sheet):
    #探索配置的上传函数
    indented = ''
    explore_config = make_dict(sheet)
    explore_config_string = "{\n" + print_dict(explore_config, indented) + "\n}"
    return explore_config_string

def talent_skill_config(sheet):
    #天赋技能配置的上传函数
    indented = ''
    talent_skill_config = make_dict(sheet)
    talent_skill_config_string = "{\n" + print_dict(talent_skill_config, indented) + "\n}"
    return talent_skill_config_string

def talent_value_config(sheet):
    #天赋配置的上传函数
    indented = ''
    talent_value_config = make_dict(sheet)
    talent_value_config_string = "{\n" + print_dict(talent_value_config, indented) + "\n}"
    return talent_value_config_string

def props_desc_config(sheet):
    #道具描述的上传配置
    indented = ''
    props_desc_config = make_dict(sheet)
    sort_keys = [ '%s_props' % tag for tag in sorted([int(i.split('_')[0]) for i in props_desc_config])]
    props_desc_config_string = "{\n" + print_dict(props_desc_config, indented,sort_keys) + "\n}"
    return props_desc_config_string

def user_vip_config(sheet):
    #vip 配置的上传函数
    indented = ''
    user_vip_config = make_dict(sheet)
    user_vip_config_string = "{\n" + print_dict(user_vip_config, indented) + "\n}"
    return user_vip_config_string

def equip_exp_config(sheet):
    #装备经验配置的上传配置
    indented = ''
    equip_exp_config = make_dict(sheet)
    equip_exp_config_string = "{\n" + print_dict(equip_exp_config, indented) + "\n}"
    return equip_exp_config_string

def skill_config(sheet):
    #技能配置的上传函数
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
    #药品配置的上传函数
    indented = ''
    item_config = make_dict(sheet)
    sort_keys = [ '%s_item' % tag for tag in sorted([int(i.split('_')[0]) for i in item_config])]
    item_config_string = "{\n" + print_dict(item_config, indented,sort_keys) + "\n}"
    return item_config_string

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
    sort_keys_talent = [ '%s_talent' % tag for tag in sorted([int(i.split('_')[0]) for i in skill_desc_config if 'talent' in i])]
    sort_keys_skill.extend(sort_keys_leader)
    sort_keys_skill.extend(sort_keys_talent)
    skill_config_string = "{\n" + print_dict(skill_desc_config, indented,sort_keys_skill) + "\n}"
    return skill_config_string

def dungeon_desc_config(sheet):
    indented = ''
    dungeon_desc_config = make_dict(sheet)
    #sort_keys = [ '%s' % tag for tag in sorted([int(i) for i in dungeon_desc_config])]
    dun_config_string = "{\n" + print_dict(dungeon_desc_config, indented) + "\n}"
    return dun_config_string

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

def normal_dungeon_config(sheet):
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

def pk_config(sheet):
    indented = '\t'
    config = make_dict(sheet)
    config_string = "{\n" + print_dict(config, indented) + "\n}"
    return config_string

def equip_upgrade_config(sheet):
    indented = '\t'
    config = make_dict(sheet)
    config_string = "{\n" + print_dict(config, indented) + "\n}"
    return config_string

def suit_type_config(sheet):
    indented = '\t'
    config = make_dict(sheet)
    config_string = "{\n" + print_dict(config, indented) + "\n}"
    return config_string

def bead_config(sheet):
    indented = ''
    config = make_dict(sheet)
    sort_keys = [ '%s' % tag for tag in sorted([int(i) for i in config])]
    config_string = "{\n" + print_dict(config, indented,sort_keys) + "\n}"
    return config_string



