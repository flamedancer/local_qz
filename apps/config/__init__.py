#-*- coding: utf-8 -*-

from django.conf import settings
import time
from apps.models.redis_tool import RedisTool
from apps.models import redis_tool
from apps.config import game_config

def config_update(subarea, config_name):
    RedisTool.set(settings.CACHE_PRE+'config_update_time', time.time(), 72*60*60)

    redis_tool.set_config_version(subarea, config_name)
    if config_name in ["card_config",]:
        RedisTool.set(settings.CACHE_PRE+'card_config_update_time', time.time(), 72*60*60)
    elif config_name in ["monster_config",]:
        RedisTool.set(settings.CACHE_PRE+'monster_config_update_time', time.time(), 72*60*60)
    elif config_name in ["pack_config",]:
        RedisTool.set(settings.CACHE_PRE+'pack_config_update_time', time.time(), 72*60*60)
    elif config_name in ["equip_config",]:
        RedisTool.set(settings.CACHE_PRE+'equip_config_update_time', time.time(), 72*60*60)
    elif config_name in ["item_config",]:
        RedisTool.set(settings.CACHE_PRE+'item_config_update_time', time.time(), 72*60*60)
    elif config_name in ["material_config",]:
        RedisTool.set(settings.CACHE_PRE+'material_config_update_time', time.time(), 72*60*60)
    else:
        RedisTool.set(settings.CACHE_PRE+'system_config_update_time', time.time(), 72*60*60)

def reload_all():
    try:
        reload_time = RedisTool.get(settings.CACHE_PRE+'config_update_time')
        if not reload_time or (reload_time and game_config.game_config.reload_time < reload_time):
            game_config.game_config.reload_config()
            print 'game_config reloaded......'
    except:
        from apps.common import utils
        utils.print_err()
