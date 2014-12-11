#!/usr/bin/env python
# encoding: utf-8

from apps.config.game_config import game_config
from apps.oclib.model import UserModel


class GameModel(UserModel):
    """
    对UserModel 进一步封装一些通用 方法，便于应用的 user_model， 例如：
    game_model_obj.subarea       获得当前玩家的分区号
    game_model_obj.game_config        获得当前玩家所在分区配置  
    game_model_obj.other_game_model_name        获得此id的其他game_model
    """

    _ALL_USER_CLASSES = {}


    @property
    def subarea(self):
        return self.user_base.subarea

    @property
    def game_config(self):
        game_config.set_subarea(self.subarea)
        return game_config

    def __getattr__(self, model_name):
        if model_name in self._ALL_USER_CLASSES:
            return self._ALL_USER_CLASSES[model_name].get(self.uid) or self._ALL_USER_CLASSES[model_name].get_instance(self.uid) 
        class_name = "".join([name_str.capitalize() for name_str in model_name.split('_')]) 
        model_path = "apps.models." + model_name
        try:
            model = __import__(model_path, globals(), locals(), [class_name])
            model_class = getattr(model, class_name)
        except ImportError:
            raise AttributeError, "{} object has no attribute '{}'".format(self.__class__.__name__, model_name)
        # 只有继承自GameModel的类实例，才能相互调取
        if self.__class__.__bases__ != model_class.__bases__:
            raise AttributeError, "{} object is not a GameModel".format(model_name)
        self._ALL_USER_CLASSES[model_name] = model_class
        return model_class.get(self.uid) or model_class.get_instance(self.uid) 
