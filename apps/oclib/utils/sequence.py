#-*- coding: utf-8 -*-
from apps.oclib import app
#from django.conf import settings

def next_uid(app_id='', plat_id=''):
    num = app.mongo_store.mongo['sequence'].find_and_modify(query={'_id': 'userid'},update={'$inc': { 'seq': 1 }},new=True)['seq']
#    num = app.redis_store.redis_list[0].incr(settings.GAME_UID_KEY) + settings.GAME_UID_MIN
    seq = str(int(num))

    uid = '%s%s%s' % (app_id, plat_id, seq)
    return uid
