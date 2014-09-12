# -*- encoding: utf-8 -*-  
import copy
from apps.oclib.model import MongoModel


class MongoConfig(MongoModel):
    #"""游戏配置信息
    #
    #Attributes:
    #    config_name: 配置名称 str
    #    data: 配置信息 dict
    #"""
    pk = 'config_name'
    fields = ['config_name','data']
    def __init__(self):
        #"""初始化游戏配置信息
        #
        #Args:
        #    config_name: 配置名称
        #"""
        self.config_name = None
        self.data = '{}'

    @classmethod
    def create(cls, config_name, config_value="{}"):
        conf = MongoConfig()
        conf.config_name = config_name
        conf.data = config_value
        return conf
    
    
class MongoTimingConfig(MongoModel):
    #"""保存定时设置的内容
    #"""
    pk = 'config_name'
    fields = ['config_name','data']
    def __init__(self):
        #"""
        #"""
        self.config_name = None
        self.data = {}

    @classmethod
    def create(cls, config_name, config_value={}):
        conf = MongoTimingConfig()
        conf.config_name = config_name
        conf.data = copy.deepcopy(config_value)
        return conf

    
    


