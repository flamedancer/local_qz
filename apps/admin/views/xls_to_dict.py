#!/usr/bin/env python
#-*- coding: utf-8 -*-

import xlrd
import traceback
import sys
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from apps.admin.decorators import require_permission
from apps.models.config import Config
from apps.admin.auth import get_moderator_by_request
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
                            'max_gacha_point', 'login_record_length', 'deck_length', 'friend_help_user_num', 'friend_gacha_pt', 'other_help_user_num', 
                            'other_gacha_pt', 'revive_coin', 'recover_stamina_coin', 'dungeon_clear_coin', 'card_extend_num', 'max_card_num', 'card_extend_coin',
                            'free_stamina_cnt', 'tranform_divider', 'newbie_days', 'recover_copy_coin', 'bind_phone_cnt', 
                           ]
        self.dict_cnames = ['res_url_online', 'popularize', 'bind_mobile_conf', 'timing_notice_conf', 'push_info', 'you', 
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
    data['config_name'] = config_name
    if not config_name in canuse_config_list:
       data['config_value'] = 'developering...'
    else:
        x_func = eval(config_name.capitalize() +'()')
        files = request.FILES.get('xls', None)
        if not files:
            data['config_value'] = 'Nothing...'
        else:
            data['config_value'] = x_func.make_config(files, config_name)

        str_config_description = config_list.get_description(config_name)
        data['config_title'] = str_config_description
        data['config_title'] += '__%s' % config_name
        data['saved'] = False
    moderator = get_moderator_by_request(request)
    return render_to_response('admin/game_setting.html', data, context_instance = RequestContext(request))

def _make_configstring_by_excel(config_name, files):
    config_string = ''
    if not config_name in canuse_config_list:
        config_string = 'developering...'
    else:
        x_func = eval(config_name.capitalize() +'()')
        if not files:
            config_string = 'Nothing...'
        else:
            config_string = x_func.make_config(files, config_name)
    return config_string

def _verify_game_config(config_name, value):
    #用于验证配置是否正确
    verify_dict = {
        'system_config': ['maintenance'],#key为配置名称，value为该配置名称必须存在的key
        'loginbonus_config': ['bonus'],
        'shop_config': ['sale'],
        'user_level_config': ['1'],
        'gacha_config': ['free_rate', 'charge_rate',],
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
        for dungeon_floor in value:
            mdset = set(value[dungeon_floor]['monster_drop'].keys())
            mset = set(game_config.monster_config.keys())
            if mdset & mset != mdset:
                vdresult = mdset - (mdset & mset)
                if vdresult:
                    for mid in vdresult:
                        return "敌将配置__monster_config 缺少配置ID：" + str(mid)
    return ''

