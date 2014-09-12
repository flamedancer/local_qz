user_ls=[
'1042121004',
'2536121003',
'3553121009',
'0742121004',
'6840121004',
]
from apps.models.user_gift import UserGift
for uid in user_ls:
    user_gift_obj = UserGift.get(uid)
    if not user_gift_obj:
        print 'uid:%s not exist' % uid
        continue
    user_gift_obj.add_gift({'coin':100},content=u'提bug奖励:')
    user_gift_obj.do_put()
    

############mongo导出config配置################
/opt/mongodb/bin/mongoexport -h 10.200.55.32 -d maxstrike_appstore -c config -o appstore_config_20131108.dat
###########mongo导入配置###############
/usr/bin/mongoimport -h 54.238.211.123 -u awsmaxstrikeuser1a -pawsmaxstrikeuPwD1ao% -d awsmaxstrikedb1a -c config appstore_config_20131108.dat

##########################清除config####################
all_config_name_list = [
    'system_config',
    'gacha_config',
    'gacha_timing_config',
    'loginbonus_config',
    'card_config',
    'shop_config',
    'msg_config',
    'language_config',
    'user_level_config',
    'dungeon_world_config',
    'dungeon_config',
    'normal_dungeon_effect_config',
    'special_dungeon_config',#限时战场配置
    'dungeon_effect_config',
    'card_level_config',
    'card_update_config',
    'skill_config',
    'leader_skill_config',
    'monster_config',
    'weibo_config',#微博相关配置,
    'invite_config',#邀请相关配置,
    'user_init_config',#用户初始配置,
    "maskword_config",   #屏蔽字配置
    'city_config',#城镇配置
    'equip_config',#装备配置
    'item_config',#道具配置
    'material_config',#材料配置
    'pvp_config',#pvp
    'monster_group_config',#怪物分组配置
    'box_config',#宝箱配置
    'material_desc_config',#'材料描述配置'
    'item_desc_config',#'道具描述配置'
    'card_desc_config',#'武将描述配置'
    'equip_desc_config',#'装备描述配置'
    'skill_desc_config',#'技能描述配置'
    'dungeon_desc_config',#'普通战场描述配置'
    'weekly_dungeon_config',#每周战场配置
    'gift_config',#

]
from apps.models.config import Config
for config_name in all_config_name_list:
    config = Config.get(config_name)
    if config:
        config.delete()
        
        
        
        
user_ls=[
'1100259738',
'1100234519',
'1100244733',
'1100245792',
'1100279807',
'1100213359',
'1100256411',
'1100347808',
'1100251969',
]
award={
'card':{'169_card':{'category':'4','lv':1}},
'coin':3000,
'item':{'3_item':10,'22_item':10},
}
from apps.models.user_gift import UserGift
for uid in user_ls:
    user_gift_obj = UserGift.get(uid)
    if not user_gift_obj:
        print 'uid:%s not exist' % uid
        continue
    user_gift_obj.add_gift(award,content=u'风林火山感谢您的支持:')

    user_gift_obj.do_put()
    


award={
'card':{'170_card':{'category':'2','lv':1}},
'coin':5000,
}
from apps.models.user_gift import UserGift
for uid in ['1100213700','1100216783']:
    user_gift_obj = UserGift.get(uid)
    if not user_gift_obj:
        print 'uid:%s not exist' % uid
        continue
    user_gift_obj.add_gift(award,content=u'风林火山qa:')
    user_gift_obj.do_put()


