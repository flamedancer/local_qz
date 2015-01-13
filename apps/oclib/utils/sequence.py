#-*- coding: utf-8 -*-
from apps.oclib import app
#from django.conf import settings

def next_uid(app_id='', plat_id=''):
    num = app.mongo_store.mongo['sequence'].find_and_modify(query={'_id': 'userid'},update={'$inc': { 'seq': 1 }},new=True)['seq']
    seq = str(int(num))

    uid = '%s%s%s' % (app_id, plat_id, seq)
    return uid
