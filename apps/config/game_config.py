#-*- coding: utf-8 -*-

import time

from apps.models.config import Config
from apps.config import config_list

class GameConfig(object):
    subarea_num = ''            #   当前请求玩家的 分区号
    configs = {}                #   所有的配置信息，key的形式为 配置名:分区号
    reload_time = int(time.time())

    def __init__(self):
        str_subareas_confname = config_list.get_configname_by_subarea('subareas_conf', '1')
        subareas_conf = Config.get(str_subareas_confname)
        if not subareas_conf:
            subareas_conf = Config.create(subareas_conf)
        self.configs[str_subareas_confname] = eval(subareas_conf.data)
        self.subareas_confname = str_subareas_confname

    def _get_subarea_config_name(self, config_name, subarea):
        str_config_name_by_subarea = config_list.get_configname_by_subarea(config_name, subarea)
        if not str_config_name_by_subarea:
            raise KeyError, 'Has no this config name:| ' + config_name + ' |subarea is:' + subarea
        if subarea not in self.subareas_conf():
            raise Exception, 'Has no this subarea:' + subarea
        return str_config_name_by_subarea

    def reload_config(self):
        for subarea_config_name in self.configs:
            self.configs[subarea_config_name] = eval(Config.get(subarea_config_name).data)
        self.reload_time =  int(time.time())
 
    def subareas_conf(self):
        """获取 分区配置
        """
        return self.configs[self.subareas_confname]

    def set_subarea(self, subarea):
        # 设置此次请求分区号
        if subarea in self.subareas_conf():
            self.subarea_num = subarea

    def get_game_config(self, config_name, subarea):
        #config_name, 配置名; subarea, 分区号
        subarea_config_name = self._get_subarea_config_name(config_name, subarea)        
        if subarea_config_name not in self.configs:
            config_obj = Config.get(subarea_config_name)
            if not config_obj:
                raise Exception, "config name '{}' is empty in subarea '{}'".format(config_name, subarea)
            self.configs[subarea_config_name] = eval(config_obj.data)
        return self.configs[subarea_config_name]

    def __getattr__(self, config_name):
        return self.get_game_config(config_name, self.subarea_num)

game_config = GameConfig()
