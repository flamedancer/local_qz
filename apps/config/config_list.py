#-*- coding: utf-8 -*-

#游戏设置的列表：
#Example:
#g_lconfig = [
#    {
#        'name': u'英文名称',
#        'description': u'中文名称',
#        'use_subarea': False,#是否使用分区，False（不使用分区，则所有的配置都默认为1区配置）, True(不同的分区找到不同的配置)
#        'belongs_menu': 'system_config_type'#归类
#    },
#]

g_lConfig = [
    {
        'name': 'subareas_conf',
        'description': u'分区配置',
        'use_subarea': False,
    },
    {
        'name': 'system_config',
        'description': u'系统配置',
        'use_subarea': True,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'loginbonus_config',
        'description': u'每日登录礼物',
        'use_subarea': True,
        'belongs_menu': 'operate_type'
    },
    {
        'name': 'shop_config',
        'description': u'商店配置',
        'use_subarea': False,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'explore_config',
        'description': u'探索配置',
        'use_subarea': False,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'user_level_config',
        'description': u'用户等级参数配置',
        'use_subarea': False,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'gacha_config',
        'description': u'招募求将配置',
        'use_subarea': True,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'gacha_timing_config',
        'description':  u'招募定时配置',
        'use_subarea': True,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'card_config',
        'description':  u'武将设置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'talent_skill_config',
        'description':  u'武将天赋技能配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'talent_value_config',
        'description':  u'武将天赋数值配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'card_level_config',
        'description':  u'武将等级配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'card_update_config',
        'description':  u'武将强化配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'skill_config',
        'description':  u'武将技配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'leader_skill_config',
        'description': u'主将技配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'monster_config',
        'description': u'敌将配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'monster_group_config',
        'description': u'敌将分组配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'dungeon_world_config',
        'description': u'战场世界配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'normal_dungeon_config',
        'description': u'普通战场配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
	{
        'name': 'drop_info_config',
        'description': u'战场掉落配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'box_config',
        'description': u'宝箱配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'normal_dungeon_effect_config',
        'description': u'普通战场效果配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'special_dungeon_config',
        'description': u'限时活动战场配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'weekly_dungeon_config',
        'description': u'每周活动战场配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'daily_dungeon_config',
        'description': u'每日活动战场配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'msg_config',
        'description': u'提示语配置',
        'use_subarea': False,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'language_config',
        'description': u'语言包配置',
        'use_subarea': False,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'weibo_config',
        'description': u'微博相关配置',
        'use_subarea': False,
        'belongs_menu': 'operate_type'
    },
    {
        'name': 'invite_config',
        'description': u'邀请相关配置',
        'use_subarea': False,
        'belongs_menu': 'operate_type'
    },
    {
        'name': 'user_init_config',
        'description': u'用户初始配置',
        'use_subarea': False,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'maskword_config',
        'description': u'屏蔽字配置',
        'use_subarea': False,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'equip_config',
        'description': u'装备配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'item_config',
        'description': u'药品配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'props_config',
        'description': u'道具配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'material_config',
        'description': u'材料配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'pvp_config',
        'description': u'pvp竞技场配置',
        'use_subarea': True,
        'belongs_menu': 'operate_type'
    },
    {
        'name': 'material_desc_config',
        'description': u'材料描述配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'item_desc_config',
        'description': u'药品描述配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'props_desc_config',
        'description': u'道具描述配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'card_desc_config',
        'description': u'武将描述配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'equip_desc_config',
        'description': u'装备描述配置',
        'use_subarea': True,
        'belongs_menu': 'equip_type'
    },
    {
        'name': 'skill_desc_config',
        'description': u'技能描述配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'dungeon_desc_config',
        'description': u'战场描述配置',
        'use_subarea': True,
        'belongs_menu': 'battleground_type'
    },
    {
        'name': 'gift_config',
        'description': u'礼品码配置',
        'use_subarea': True,
        'belongs_menu': 'operate_type'
    },
    {
        'name': 'android_config',
        'description': u'安卓配置',
        'use_subarea': True,
    },
    {
        'name': 'operat_config',
        'description': u'运营活动配置',
        'use_subarea': True,
        'belongs_menu': 'operate_type'
    },
    {
        'name': 'mystery_store',
        'description': u'神秘商店',
        'use_subarea': True,
        'belongs_menu': 'operate_type'
    },
    {
        'name': 'skill_params_config',
        'description': u'技能数值配置',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'ruby_skill_params_config',
        'description': u'ruby技能数值配置(提交此配置将改变 技能数值配置！)',
        'use_subarea': True,
        'belongs_menu': 'general_type'
    },
    {
        'name': 'marquee_config',
        'description': u'跑马灯配置',
        'use_subarea': True,
        'belongs_menu': 'system_config_type'
    },
    {
        'name': 'equip_exp_conf',
        'description': u'装备等级',
        'use_subarea': True,
    },
    {
        'name': 'equip_update_config',
        'description': u'装备强化配置',
        'use_subarea': True,
    },
    {
        'name': 'suit_type_conf',
        'description': u'套装配置',
        'use_subarea': True,
    },
    {
        'name': 'user_vip_conf',
        'description': u'Vip配置',
        'use_subarea': True,
    },
    {
        'name': 'fate_conf',
        'description': u'缘分配置',
        'use_subarea': True,
    },
    {
        'name': 'rob_config',
        'description': u'掠夺配置',
        'use_subarea': True,
    },
    {
        'name': 'pack_config',
        'description': u'背包配置',
        'use_subarea': True,
    },
    {
        'name': 'pk_config',
        'description': u'pk配置',
        'use_subarea': True,
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
    l_config = []
    if subarea:
        for g_dConfigKey in g_lConfig:
            if subarea == '1':
                str_name = g_dConfigKey['name']
                l_config.append(g_dConfigKey)
            else:
                use_subarea = g_dConfigKey['use_subarea']
                if use_subarea is True:
                    l_config.append(g_dConfigKey)
    return l_config

