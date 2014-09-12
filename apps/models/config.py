#!/usr/bin/env python
# encoding: utf-8
"""
config.py

"""
from apps.oclib.model import BaseModel

class Config(BaseModel):
    """游戏配置信息

    Attributes:
        config_name: 配置名称 str
        data: 配置信息 dict
    """
    pk = 'config_name'
    fields = ['config_name','data']
    def __init__(self):
        """初始化游戏配置信息

        Args:
            config_name: 配置名称
        """
        self.config_name = None
        self.data = '{}'

    @classmethod
    def create(cls, config_name, config_value="{}"):
        conf = Config()
        conf.config_name = config_name
        conf.data = config_value
        return conf

