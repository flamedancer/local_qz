#-*- coding: utf-8 -*-

import time

from apps.models.config import Config
from apps.config import config_version
from apps.config import config_list

from apps.config.backup import generate_backup

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
        #print '#### self.configs.keys()=', self.configs.keys()
        #so only backup, when config changed, need reload. Backup only once 
        #a day.
        generate_backup()   #每天的第一次配置改动前，备份一次改动前的内容。
        if self.reload_time > config_version.get_config_version('1', config_name="ALL_config"):
            return
        for subarea_config_name in self.configs:
            if not subarea_config_name.startswith('ruby_skill_params_config'):
                conf_obj = Config.get(subarea_config_name)
                if conf_obj:
                    self.configs[subarea_config_name] = eval(conf_obj.data)
        self.reload_time = int(time.time())
 
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
        if not subarea:
            subarea = '1'
        subarea_config_name = self._get_subarea_config_name(config_name, subarea)        
        if subarea_config_name not in self.configs:
            config_obj = Config.get(subarea_config_name) or Config.create(subarea_config_name)
            config_dict = eval(config_obj.data)
            if not config_dict and subarea != '1':
                # 若此分区当前配置为空， 尝试读取 1 区 配置
                return self.get_game_config(config_name, '1')
            self.configs[subarea_config_name] = config_dict
        return self.configs[subarea_config_name]

    def __getattr__(self, config_name):
        return self.get_game_config(config_name, self.subarea_num)

game_config = GameConfig()
