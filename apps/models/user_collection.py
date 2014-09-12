# encoding: utf-8
""" collection.py
"""

from apps.oclib.model import UserModel

class UserCollection(UserModel):
    """
    用户的图鉴的信息记录
    """
    pk = 'uid'
    fields = ['uid','collection']

    def __init__(self):
        self.uid = None
        self.collection = {'cards':{},'equips':{},'items':{},'materials':{},'props':{}}

    @classmethod
    def get_instance(cls, uid):
        """ 获取一个当前的用户实例
        Args:
            uid: 用户游戏ID
        return:
            获取一个当前的用户实例
        """
        obj = cls.get(uid)
        if not obj:
            obj = cls.create(uid)
            obj.put()
        return obj

    @classmethod
    def create(cls,uid):
        user_collection = UserCollection()
        user_collection.uid = uid
        user_collection.collection = {
            'cards':{},
            'equips':{},
            'items':{},
            'materials':{},
            'props':{}
        }
        return user_collection

    def get_collected_cards(self,key='cards'):
        """ 根据收集物品的分类获取用户收集到的物品列表
        Args:
            category:图鑑类型(如：卡片，怪物等)
        return:
            返回数据列表，如果没有数据返回空列表
        """
        if key not in self.collection:
            #主要事为了防止不存在该key影响正常使用
            self.collection[key] = {}
            self.put()
        return self.collection.get(key,{})

    def get_collected_num(self, category, has_sub_key=False):
        """ 根据收集的物品的分类获取用户收集到的物品列表的数量
        Args:
            category:图鑑类型(如：卡片，怪物等)
        return:
            int
        """
        num = 0
        collection = self.collection

        if collection.has_key(category):
            if has_sub_key:
                for k, v in collection[category].items():
                    num += len(v)
            else:
                num = len(collection.get(category, []))

        return num

    def add_collected_card(self, item_id, key='cards'):
        """ 卡片收集
        Args:
            item_id: 卡片id
            key: 卡片收集数据字典的key
        """
        item_id = str(item_id)
        is_first = True
        if item_id in self.collection.get(key) and self.collection[key][item_id] == 2:
            is_first = False
        else:
            self.collection[key][item_id] = 2
            self.put()

        return is_first

    def add_collected_card_by_monster(self, item_id, key='cards'):
        """遇到怪物后增加到图鉴
        """
        item_id = str(item_id)
        if item_id not in self.collection.get(key,{}):
            self.collection[key][item_id] = 1
            self.put()
            return item_id
        else:
            return ''


    def is_first_card(self, item_id, key='cards'):
        """ 卡片收集
        Args:
            item_id: 卡片id
            key: 卡片收集数据字典的key
        """
        item_id = str(item_id)
        is_first = True
        if item_id in self.collection.get(key, []):
            is_first = False

        return is_first
