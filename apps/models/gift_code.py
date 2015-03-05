#!/usr/bin/env python
# encoding: utf-8
"""
config.py

"""
from apps.oclib.model import BaseModel

class GiftCode(BaseModel):
    """游戏配置信息

    Attributes:
        config_name: 配置名称 str
        data: 配置信息 dict
    """
    pk = 'gift_id'
    fields = ['gift_id','codes']
    def __init__(self):
        """初始化游戏配置信息

        Args:
            config_name: 配置名称
        """
        self.gift_id = ''
        self.codes = {}

    @classmethod
    def get(cls,gift_id):
        obj = super(GiftCode,cls).get(gift_id)
        return obj
    @classmethod
    def get_instance(cls,gift_id):
        obj = super(GiftCode,cls).get(gift_id)
        if not obj:
            obj = GiftCode()
            obj.gift_id = gift_id
            obj.codes = {}
            obj.put()
        return obj

    def give_codes(self,add_codes):
        self.codes.update(add_codes)
        self.put()
