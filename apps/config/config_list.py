#-*- coding: utf-8 -*-

#游戏设置的列表：
#Example:
#g_lconfig = [
#    {
#        'name': u'英文名称',
#        'description': u'中文名称',
#        'use_subarea': False,#是否使用分区，False（不使用分区，则所有的配置都默认为1区配置）, True(不同的分区找到不同的配置)
#        'category': u'系统/用户'#归类
#    },
#]

g_lConfig = [
    {
        'name': 'subareas_conf',
        'description': u'分区',
        'use_subarea': False,
        'category': u'系统/用户',
    },
    {
        'name': 'system_config',
        'description': u'系统',
        'use_subarea': False,
        'category': u'系统/用户',
    },

    {
        'name': 'subarea_notice_config',
        'description': u'分区的登录公告',
        'use_subarea': False,
        'category': u'系统/用户',
    },

    {
        'name': 'user_level_config',
        'description': u'用户等级参数',
        'use_subarea': False,
        'category': u'系统/用户'
    },
    {
        'name': 'user_init_config',
        'description': u'用户初始化',
        'use_subarea': False,
        'category': u'系统/用户'
    },
    {
        'name': 'user_vip_config',
        'description': u'VIP用户',
        'use_subarea': False,
        'category': u'系统/用户'
    },
    {
        'name': 'explore_config',
        'description': u'探索',
        'use_subarea': False,
        'category': u'系统/用户'
    },
    {
        'name': 'gacha_config',
        'description': u'招募求将',
        'use_subarea': True,
        'category': u'武将/敌将'
    },
    # {
    #     'name': 'gacha_timing_config',
    #     'description':  u'招募定时',
    #     'use_subarea': True,
    #     'category': u'武将/敌将'
    # },
    {
        'name': 'card_config',
        'description':  u'武将设置',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    {
        'name': 'card_desc_config',
        'description': u'武将描述',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    {
        'name': 'talent_skill_config',
        'description':  u'武将天赋技能',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    {
        'name': 'talent_value_config',
        'description':  u'武将天赋数值',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    {
        'name': 'card_level_config',
        'description':  u'武将等级',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    {
        'name': 'card_update_config',
        'description':  u'武将强化',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    # {
    #     'name': 'skill_config',
    #     'description':  u'武将技',
    #     'use_subarea': False,
    #     'category': u'武将/敌将'
    # },
    # {
    #     'name': 'leader_skill_config',
    #     'description': u'主将技',
    #     'use_subarea': False,
    #     'category': u'武将/敌将'
    # },
    {
        'name': 'dungeon_world_config',
        'description': u'战场世界',
        'use_subarea': True,
        'category': u'战场'
    },
    {
        'name': 'normal_dungeon_config',
        'description': u'普通战场',
        'use_subarea': True,
        'category': u'战场'
    },
    {
        'name': 'drop_info_config',
        'description': u'战场掉落',
        'use_subarea': False,
        'category': u'战场'
    },
    {
        'name': 'normal_dungeon_effect_config',
        'description': u'普通战场效果',
        'use_subarea': False,
        'category': u'战场'
    },
    # {
    #     'name': 'special_dungeon_config',
    #     'description': u'限时活动战场',
    #     'use_subarea': False,
    #     'category': u'战场'
    # },
    # {
    #     'name': 'weekly_dungeon_config',
    #     'description': u'每周活动战场',
    #     'use_subarea': False,
    #     'category': u'战场'
    # },
    {
        'name': 'daily_dungeon_config',
        'description': u'每日试炼战场',
        'use_subarea': False,
        'category': u'战场'
    },
    # {
    #     'name': 'dungeon_desc_config',
    #     'description': u'战场描述',
    #     'use_subarea': False,
    #     'category': u'战场'
    # },
    {
        'name': 'pk_config',
        'description': u'PK(实时PvP)配置',
        'use_subarea': False,
        'category': u'战场'
    },
    {
        'name': 'bead_config',
        'description': u'珠盘配置',
        'use_subarea': False,
        'category': u'战场'
    },
    {
        'name': 'msg_config',
        'description': u'提示语',
        'use_subarea': False,
        'category': u'系统/用户'
    },
    {
        'name': 'language_config',
        'description': u'语言包',
        'use_subarea': False,
        'category': u'系统/用户'
    },
    {
        'name': 'loginbonus_config',
        'description': u'每日登录礼物',
        'use_subarea': True,
        'category': u'运营',
    },

    {
        'name': 'weibo_config',
        'description': u'微博相关',
        'use_subarea': False,
        'category': u'运营'
    },
    {
        'name': 'invite_config',
        'description': u'邀请相关',
        'use_subarea': False,
        'category': u'运营'
    },
    {
        'name': 'maskword_config',
        'description': u'屏蔽字',
        'use_subarea': False,
        'category': u'系统/用户'
    },
    {
        'name': 'equip_config',
        'description': u'装备',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'equip_desc_config',
        'description': u'装备描述',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'equip_exp_config',
        'description': u'装备等级',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    # {
    #     'name': 'equip_update_config',
    #     'description': u'装备强化',
    #     'use_subarea': False,
    #     'category': u'装备/技能'
    # },
    {
        'name': 'equip_upgrade_config',
        'description': u'装备升品',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'suit_type_config',
        'description': u'装备套装',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    # {
    #     'name': 'item_config',
    #     'description': u'药品',
    #     'use_subarea': False,
    #     'category': u'装备/技能'
    # },
    # {
    #     'name': 'item_desc_config',
    #     'description': u'药品描述',
    #     'use_subarea': False,
    #     'category': u'装备/技能'
    # },
    {
        'name': 'props_config',
        'description': u'道具',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'props_desc_config',
        'description': u'道具描述',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'material_config',
        'description': u'材料',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'material_desc_config',
        'description': u'材料描述',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'skill_desc_config',
        'description': u'技能描述',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'gift_config',
        'description': u'礼品码',
        'use_subarea': True,
        'category': u'运营'
    },
    {
        'name': 'operat_config',
        'description': u'运营活动',
        'use_subarea': True,
        'category': u'运营'
    },
    {
        'name': 'mail_config',
        'description': u'邮件',
        'use_subarea': True,
        'category': u'运营'
    },
    {
        'name': 'skill_params_config',
        'description': u'技能数值',
        'use_subarea': False,
        'category': u'装备/技能'
    },
    {
        'name': 'ruby_skill_params_config',
        'description': u'ruby技能数值(会改变技能数值!)',
        'use_subarea': False,
        'category': u'装备/技能'
    },

    {
        'name': 'marquee_config',
        'description': u'跑马灯',
        'use_subarea': True,
        'category': u'系统/用户'
    },
    {
        'name': 'task_config',
        'description': u'任务',
        'use_subarea': True,
        'category': u'系统/用户'
    },
    {
        'name': 'fate_config',
        'description': u'缘分',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    {
        'name': 'monster_config',
        'description': u'敌将',
        'use_subarea': False,
        'category': u'武将/敌将'
    },
    {
        'name': 'android_config',
        'description': u'安卓-待开发',
        'use_subarea': False,
    },
    {
        'name': 'vip_store_config',
        'description': u'vip商店',
        'use_subarea': False,
        'category': u'商店/充值',
    },
    {
        'name': 'mystery_store_config',
        'description': u'神秘商店',
        'use_subarea': True,
        'category': u'商店/充值',
    },
    {
        'name': 'pk_store_config',
        'description': u'PK商店',
        'use_subarea': True,
        'category': u'商店/充值',
    },
    {
        'name': 'props_store_config',
        'description': u'道具商店',
        'use_subarea': True,
        'category': u'商店/充值',
    },
    {
        'name': 'shop_config',
        'description': u'元宝充值',
        'use_subarea': False,
        'category': u'商店/充值',
    },
]


def get_description(config_name):
    """通过配置的英文名称获得中文名称
    """
    str_description = ''
    for g_dConfigKey in g_lConfig:
        str_name = g_dConfigKey['name']
        if str_name == config_name:
            str_description = g_dConfigKey['description']
            break
    return str_description



def get_configname_by_subarea(config_name, subarea):
    """通过分区获得配置名称，config_name + '_' + subarea，如果配置在g_lConfig中的use_subarea为false，则subarea始终为'1'
    """
    subarea = str(subarea)
    str_configsubareaname = ''
    for g_dConfigKey in g_lConfig:
        str_name = g_dConfigKey['name']
        if str_name == config_name:
            b_use_subarea = g_dConfigKey['use_subarea']
            if b_use_subarea:
                if subarea:
                    str_configsubareaname = config_name + '_' + subarea
            else:
                str_configsubareaname = config_name + '_1' 
            break
    return str_configsubareaname




def get_conflist_by_subarea(subarea):
    """通过分区号来获得配置列表，如果'use_subarea': True,加入列表。如果'use_subarea': False,则只有在subarea1区的情况下加入列表中
    """
    subarea = str(subarea)
#   l_config = []

    categories =  {'other': []}

    if subarea:
        for g_dConfigKey in g_lConfig:
            if subarea == '1':
                #str_name = g_dConfigKey['name']
#               l_config.append(g_dConfigKey)
                if g_dConfigKey.has_key('category'):
                    if g_dConfigKey['category'] in categories:
                        categories[ g_dConfigKey['category'] ] += [ g_dConfigKey]
                    else:
                        categories[ g_dConfigKey['category'] ] = [ g_dConfigKey ]
                else:
                    categories['other'] += [g_dConfigKey]

            else:
                use_subarea = g_dConfigKey['use_subarea']
                if use_subarea is True:
#                   l_config.append(g_dConfigKey)
                    if g_dConfigKey.has_key('category'):
                        if g_dConfigKey['category'] in categories:
                            categories[ g_dConfigKey['category'] ] += [ g_dConfigKey ]
                        else:
                            categories[ g_dConfigKey['category'] ] = [ g_dConfigKey ]
                    else:
                        categories['other'] += [g_dConfigKey]

    return categories



def get_game_config_name_dict(subarea='1'):
    ''' return { category:['card_config'], ... }
    '''
    gc_dict = {}
    for gc in g_lConfig:
        if subarea != '1' and not gc['use_subarea']:
            continue

        if gc['category']  not in gc_dict:
            gc_dict[ gc['category'] ]  = [ gc['name'] ]
        else:
            gc_dict[ gc['category'] ]  += [ gc['name'] ]

    return gc_dict  


def get_game_config_name_list(subarea='1'):
    ''' return [, 'card_config', ... ]
    '''
    gc_list = []
    for gc in g_lConfig:
        if subarea != '1' and not gc['use_subarea']:
            continue

        gc_list += [ gc['name'] ]

    return gc_list  
