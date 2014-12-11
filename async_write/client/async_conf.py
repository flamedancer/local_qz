import sys
import os

sys.path.append( os.path.dirname( os.path.realpath(__file__) ) + '/../..' )
from apps.settings import STORAGE_INDEX, STORAGE_CONFIG

redis_host = STORAGE_CONFIG[STORAGE_INDEX]['redis'][0]['host']
redis_port = STORAGE_CONFIG[STORAGE_INDEX]['redis'][0]['port']

MONGO_CONF = STORAGE_CONFIG[STORAGE_INDEX]['mongodb']

REDIS_CONF = {
     '0':{
            'rmaster': {
                'host': redis_host,
                'port': redis_port,
                'db': 0
            },
            'rslave': {
                'host': redis_host,
                'port': redis_port,
                'db': 0
            }
      },
#    '1':{
#           'rmaster': {
#               'host': redis_host,
#               'port': redis_port,
#               'db': 1
#           },
#           'rslave': {
#               'host': redis_host,
#               'port': redis_port,
#               'db': 1
#           }
#     }

}
