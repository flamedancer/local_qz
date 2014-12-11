#-*- coding: utf-8 -*-

from apps.oclib import app


class BaseModel(object):
    """
    一般model都要继承BaseModel, 存储在redis和mongodb中。
    pk定义主键
    fields定义需要持久化的字段
    """

    pk = 'uid'
    fields = []

    @classmethod
    def get(cls, pk):
        pk = str(pk)
        obj = app.redis_store.get(cls, pk)
        if not obj:
            obj = app.mongo_store.get(cls, pk)
            if obj:
                obj.put()
        return obj

    def put(self):
        return app.redis_store.set(self)

    #创建一个新的model 请在子类中实现
    @classmethod
    def create(cls):
        return None

    def delete(self):
        app.redis_store.delete(self)
        app.mongo_store.delete(self)

    @classmethod
    def load(cls, data):
        if not data:
            data = {}

        obj = cls()
        [setattr(obj, k, data.get(k)) for k in data]
        return obj

    def to_dict(self):
        obj_dict = {}
        for field in self.fields:
            obj_dict[field] = getattr(self,field)
        return obj_dict


class UserModel(BaseModel):
    """用户个人的数据 一般只允许自己读写自己的 pk都是uid"""

    pk = 'uid'
    fields = []

    @classmethod
    def get(cls, uid):
        uid = str(uid)
        obj = app.pier.get(cls, uid)
        if not obj:
            obj = app.redis_store.get_user_model(cls, uid)
        if not obj:
            obj = app.mongo_store.get(cls, uid)
            if obj:
                obj.do_put()
        if obj and app.pier.use:
            app.pier.add_get_data(obj)
        return obj

    def do_put(self):
        return app.redis_store.set_user_model(self)

    def delete(self):
        app.redis_store.delete_user_model(self)
        app.mongo_store.delete(self)

    def put(self):
        if app.pier.use:
            app.pier.add(self)
        else:
            self.do_put()

    @classmethod
    def mongo_find(cls, query, **kargs):
        '''
        UserModel doesn't have .find(), due to it relates to both redis & mongo.
        Now for statistics (count how many user logged in everyday etc.) 
        purpose, we just interested in MongoStorage.find()
        '''
        return app.mongo_store.find(cls, query, **kargs)
#       return app.bk_mongo.find(cls, query, **kargs)

    @classmethod
    def aggregate(cls, statement):
        #due to backup mongo, old, no aggregate as of 2014/8/8
        #return app.bk_mongo.aggregate(cls,statement)
        return app.mongo_store.aggregate(cls,statement)


class TmpModel(BaseModel):
    """
    存储临时数据
    """

    ex = 3600  #定义过期时间 单位秒

    @classmethod
    def get(cls, pk):
        pk = str(pk)
        return app.redis_store.get(cls, pk)

    def put(self, ex=None):
        if not ex:
            ex = self.ex
        return app.redis_store.set(self, ex, False)

    def delete(self):
        return app.redis_store.delete(self)

class HashModel(object):

    pk = 'uid'
    opk = 'ouid'
    fields = []

    @classmethod
    def hget(cls,key,field):
        key = str(key)
        obj = app.redis_store.hget_user_model(cls,key,field)
        return obj

    def delete(self):
        app.redis_store.hdelete_user_model(self)

    @classmethod
    def load(cls, data):
        obj = cls()
        [setattr(obj, k, data.get(k)) for k in data]
        return obj

    def to_dict(self):
        obj_dict = {}
        for field in self.fields:
            obj_dict[field] = getattr(self,field)
        return obj_dict

    def hput(self):
        return app.redis_store.hset_user_model(self)

    @classmethod
    def hgetall(cls, key):
        key = str(key)
        return app.redis_store.hgetall(cls, key)

class MongoModel(BaseModel):
    """
    只存储在mongo中 有查询需求
    """

    @classmethod
    def get(cls, pk):
        return app.mongo_store.get(cls, pk)

    def put(self):
        return app.mongo_store.set(self)

    def delete(self):
        return app.mongo_store.delete(self)

    @classmethod
    def find(cls, query,**kwargs):
        return app.mongo_store.find(cls,query,**kwargs)

#   @classmethod
#   def find_and_sort(cls, query, sort_by=''):
#       '''sort_by = [ ('field1', 1), ('field2', -1) ]
#       or sort_by = ('field1', 1) ??
#       or sort_by = 'field1' ??
#       '''
#       collection = cls.__name__.lower()
#       return app.mongo_store.mongo[collection].find(cls,query).sort(sort_by)
    
    def insert(self):
        return app.mongo_store.insert(self)

    @classmethod
    def orderby(cls, query, sort):
        """
        Example:
            orderby( {"status": "active"}, [("uid", -1), ("name", 1)] )
        """
        return app.mongo_store.orderby(cls,query,sort)

class LogModel(object):
    """
    存储log数据 写一次后基本不修改 有查询需求
    """

    #创建一个新的model 请在子类中实现
    @classmethod
    def create(cls):
        return None

    def put(self):
        return app.log_mongo.insert(self)

#   @classmethod
#   def find(cls, query):
#       return app.log_mongo.find(cls,query)
    
    @classmethod
    def find(cls, query, reverse_query=[]):
        # reverse_query [[key1,-1],[key2,1]] 优先按照 key1 倒序 再 kye2 正序
        if not reverse_query:
            return app.log_mongo.find(cls,query)
        else:
            return app.log_mongo.orderby(cls,query,reverse_query)


    @classmethod
    def mongo_find(cls, query, **kargs):
        '''
        A more detailed model method then above .find.
        '''
        return app.log_mongo.find(cls, query, **kargs)


    @classmethod
    def aggregate(cls, statement):
        return app.log_mongo.aggregate(cls,statement)

    @classmethod
    def load(cls, data):
        obj = cls()
        [setattr(obj, k, data.get(k)) for k in data]
        return obj


class TopModel(object):
    """
    排行榜
    """

    @classmethod
    def create(cls, top_name):
        """创建一个排行榜 """
        tm = cls()
        tm.top_name = 'top:%s' % top_name
        return tm

    def get(self, count=10, desc=True):
        """取前多少名，count为数量，desc=True从大到小 desc=False从小到大,返回一个list, count<1取所有的"""
        return app.top_redis.zrange(self.top_name, 0, count-1, desc=desc, withscores=True)
    
    def get_score(self, rank, desc=True):
        """取前排名对应的分数，rank从0开始，desc=True从大到小 desc=False从小到大,返回一个list"""
        res = app.top_redis.zrange(self.top_name, rank, rank, desc=desc, withscores=True)
        if res:
            return res[0][1]
        else:
            return None

    def get_name_by_rank(self, rank, desc=True):
        """取前排名对应的名字，rank从0开始，desc=True从大到小 desc=False从小到大,返回一个list"""
        res = app.top_redis.zrange(self.top_name, rank, rank, desc=desc, withscores=True)
        if res:
            return res[0][0]
        else:
            return None

    def set(self, name, score):
        """加一个人 正确返回1，更新返回0"""
        return app.top_redis.zadd(self.top_name, score, name)

    def remove(self, *names):
        """踢出去一部分人 返回被踢出人数 names=[name1,name2 ...]"""
        return app.top_redis.zrem(self.top_name, *names)

    def remove_by_score(self, min_score, max_score):
        """踢出去一部分人 分数在min,max之间的(包括min,max) 返回个数"""
        return app.top_redis.zremrangebyscore(self.top_name, min_score, max_score)

    def remove_last(self, count, desc=True):
        """踢出最后若干个 desc=True从大到小 desc=False从小到大 返回个数"""
        if desc:
            return app.top_redis.zremrangebyrank(self.top_name, 0, count-1)
        cnt = self.count()
        return app.top_redis.zremrangebyrank(self.top_name, cnt-count, cnt-1)

    def rank(self, name, desc=True):
        """取名次 返回一个int型，desc=True从大到小 desc=False从小到大 """
        if desc:
            return app.top_redis.zrevrank(self.top_name, name)
        return app.top_redis.zrank(self.top_name, name)

    def count(self):
        """返回排行榜总数"""
        return app.top_redis.zcard(self.top_name)
    
    def score(self, name):
        """取某人对应的分数 """
        return app.top_redis.zscore(self.top_name, name)

    def zremrangeallrank(self):
        """删除该排行榜所有的排名"""
        cnt = self.count()
        return app.top_redis.zremrangebyrank(self.top_name, 0, cnt-1)

    def exchange(self, name1, score1, name2, score2):
        """交换两个key的值, 如果不存在这两个key返回False，分数发生变化也返回False,成功返回True"""
        name1, score1, name2, score2 = str(name1), str(score1), str(name2), str(score2)
        top_name = self.top_name
        script = """
            local score1 = redis.call('ZSCORE', '%s', '%s')
            local score2 = redis.call('ZSCORE', '%s', '%s')
            --如果redis中name1和name2的排名已变化，返回0
            if score1 =='%s' and score2 =='%s' then
                redis.call('ZADD', '%s', '%s', '%s', '%s', '%s')
                return 1
            else
                return 0
            end
        """ % (top_name, name1, top_name, name2, score1, score2, top_name, score2, name1, score1, name2)
        ztop = self.register_script(script)
        return ztop(keys=['zset'])

    def register_script(self, script):
        """执行lua脚本
           script = 'print(1)'
        """
        return app.top_redis.register_script(script)
