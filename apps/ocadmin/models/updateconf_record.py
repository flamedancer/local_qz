#-*- coding: utf-8 -*-

from apps.oclib.model import MongoModel
from apps.common.utils import create_gen_id
import datetime
import math

class UpdateConfRecord(MongoModel):
    pk = 'rid'
    fields = ['rid','username', 'date','subarea', 'configname', 'REMOTE_ADDR']
    def __init__(self):
        pass

    @classmethod
    def record(cls, username, date, subarea, configname, REMOTE_ADDR):
        obj = cls()
        obj.rid = create_gen_id()
        obj.username = username
        obj.date = str(date)
        obj.subarea = str(subarea)
        obj.configname = configname
        obj.REMOTE_ADDR = REMOTE_ADDR
        obj.put()
        return obj

    @classmethod
    def infos(cls, page=1):
        data = {}
        infos_list = []
        infos = cls.orderby({},[('date', -1)])
        clear_date = str(datetime.datetime.now() - datetime.timedelta(days=30))

        for info in infos[(page - 1) * 10:page * 10]:
            idict = {}
            idict['username']    = info.username
            idict['date']        = str(info.date)[:19]
            idict['subarea']     = info.subarea
            idict['configname']  = info.configname
            idict['REMOTE_ADDR'] = info.REMOTE_ADDR
            if clear_date > info.date:
                info.delete()
            else:
                infos_list.append(idict)
        data['infos_list'] = infos_list
        pages = int(math.ceil(len(infos) / 10.0))
        data['pages'] = range(1, pages + 1)
        return data
