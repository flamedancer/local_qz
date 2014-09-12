#-*- coding: utf-8 -*-

DEBUG = False
TEMPLATE_DEBUG = DEBUG
LOCAL_DEBUG = False
ENVIRONMENT_TYPE = 'prd'

WALKER_POP_URL = ''
WALKER_KING_URL = ''
WALKER_APP_ID = ''

BASE_ROOT = '/data/sites/MaxStrikecn'
BASE_URL = 'http://maxstrikecn.negaplay.com'
#BASE_ROOT = '/data/sites/MaxStriketw'
#BASE_URL = 'http://maxstrikecn.nega777.com'

ADMINS = (
    ('lei.li', 'maxstrike_ios_bk_error@touchgame.net'),
)

MANAGERS = ADMINS

EMAIL_TITLE = 'MaxStrike-cn'
#EMAIL_TITLE = 'MaxStrike-tw'
EMAIL_HOST = 'mail.touchgame.net'
EMAIL_PORT = 25
EMAIL_USE_TLS=False

TIME_ZONE = 'Asia/Shanghai'
LANGUAGE_CODE = 'ja'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

MEDIA_ROOT = BASE_ROOT + '/static/images'
MEDIA_URL = BASE_URL + '/images'

STATIC_ROOT = BASE_ROOT + '/static/'



TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'apps.common.middlewares.simple.P3PMiddleware',
    'apps.common.middlewares.exception.ExceptionMiddleware',
    'apps.common.middlewares.storage.StorageMiddleware',
)

PIER_USE = True

ROOT_URLCONF = 'apps.urls'

TEMPLATE_DIRS = (
    BASE_ROOT + '/apps/templates',
)


INSTALLED_APPS = (
    'apps.admin',
    'apps.common',
    'apps.ocadmin',
)

AUTH_AGE = 12
SECRET_KEY = 'bdm@ktf0p7ee_sa7^mvg%i-d=b66jpd4qqomhb%upzg^s*05#v'
SIG_SECRET_KEY = 'e#!(MO4gfu!^392)_()rm3'
#tapjoy key
TAPJOY_KEY = 'jJw4Pw2ZEnECxiNKjpd1'

# mycard settings
## 测试
#MYCARD_FACID = "GFD1410"
#MYCARD_KEY1 = "mycardwanco"
#MYCARD_KEY2 = "CE2b1zQL6"
#正式
MYCARD_FACID = "GFD01197"
MYCARD_KEY1 = "mycardwanco"
MYCARD_KEY2 = "CE2b1zQL6"


#platform infomation
QQ_APP_ID = '801446107'

SINA_APP_ID = '3236539424'

FB_APP_ID = '185132175012480'
FB_SECRET_KEY = '8c7b1603dfc54c0938647d5f832f0bb2'

MI_APP_ID = '23031'
MI_SECRET_KEY = '8682dcff-5b45-5d58-fa3d-52d7a0903dcb'
#PDC_SETTINGS
PDC_SERVER = "127.0.0.1:8008"
PDC_ID = "1"


CACHE_PRE = "maxstrike_"

###############################################
#scribe config
###############################################
STATS_SWITCH = True
SCRIBE_SERVER='127.0.0.1'
SCRIBE_PORT=8250
CATEGORY_PREFIX='occard_mb'

#########################################   

#storage config
STORAGE_INDEX = '3'#国服
#STORAGE_INDEX = '4'#港台
#STORAGE_INDEX = '5'#pp91

STORAGE_CONFIG = {
    '0':{#越狱测试版
            'redis':[{'host':'10.200.55.32','port':6379,'db':'0'},{'host':'10.200.55.32','port':6379,'db':'1'}],  #一组redis 用来存储游戏数据
            'mongodb':{'host':'10.200.55.32','port':27017,'db':'maxstrike','username':'maxstrikeuser1a','password':'maxstrikeuPwd1a1zo'}, #一个mongodb 用来存储游戏数据
            'top_redis':{'host':'10.200.55.32','port':6379,'db':'15'},  #一个redis 用来做排行榜
            'log_mongodb':{'host':'10.200.55.32','port':27017,'db':'maxstrike_log','username':'maxstrikeuser1a','password':'maxstrikeuPwd1a1zo'},
         },
    '1':{#越狱正式版
        'redis':[{'host':'10.6.4.186','port':6379,'db':'0'}],  #一组redis 用来存储游戏数据
        'top_redis':{'host':'10.6.4.186','port':6379,'db':'1'},  #一个redis 用来做排行榜
        'mongodb':{'host':'10.6.2.9','port':27017,'db':'cnmaxstrikedb1a','username':'cnmaxstrikeuser1a','password':'cnmaxstrikeuPwD1a0%'}, #一个mongodb 用来存储游戏数据
        'log_mongodb':{'host':'10.6.2.9','port':27017,'db':'logcnmaxstrikedb1a','username':'logcnmaxstrikeuser1a','password':'logcnmaxstrikeuPWd10a%'},  #一个momgodb 用来存储log数据
        },
    '2':{#appstore测试版
         'redis':[{'host':'10.200.55.32','port':6379,'db':'2'}],  #一组redis 用来存储游戏数据
         'mongodb':{'host':'10.200.55.32','port':27017,'db':'maxstrike_appstore','username':'maxstrikeappstoreuser1a','password':'maxstrikeappstorePwd1ao'}, #一个mongodb 用来存储游戏数据
         'top_redis':{'host':'10.200.55.32','port':6379,'db':'3'},  #一个redis 用来做排行榜
         'log_mongodb':{'host':'10.200.55.32','port':27017,'db':'maxstrike_appstore_log','username':'maxstrikeappstoreuser1a','password':'maxstrikeappstorePwd1ao'},
         'secondary_log_mongodb':{'host':'10.200.55.32','port':27017,'db':'maxstrike_appstore_log','username':'maxstrikeappstoreuser1a','password':'maxstrikeappstorePwd1ao'},
        },
    '3':{#ios国内正式版
        'redis':[{'host':'10.161.135.142','port':6379,'db':'0'}],  #一组redis 用来存储游戏数据
        'top_redis':{'host':'10.161.135.142','port':6379,'db':'1'},  #一个redis 用来做排行榜
        'mongodb':{'host':'10.161.177.70','port':27017,'db':'cnmaxstrikedb1a','username':'cnmaxstrikeuser1a','password':'cnmaxstrikeuPwd1a&o'},
        'log_mongodb':{'host':'10.161.177.70','port':27017,'db':'logcnmaxstrikedb1a','username':'logcnmaxstrikeuser1a','password':'logcnmaxstrikeuPW&1oa'}, 
        'secondary_log_mongodb':{'host':'10.161.177.73','port':27017,'db':'logcnmaxstrikedb1a','username':'logcnmaxstrikeuser1aocdata','password':'logcnmaxstrikeuPW1oa&oCdata'}, 
        },
     '4':{#ios港台正式版
        'redis':[{'host':'negaredis1a.xeldps.0001.apne1.cache.amazonaws.com','port':6379,'db':'0'}],  #一组redis 用来存储游戏数据
        'top_redis':{'host':'negaredis1a.xeldps.0001.apne1.cache.amazonaws.com','port':6379,'db':'1'},  #一个redis 用来做排行榜
        'mongodb':{'host':'172.31.18.30','port':27017,'db':'awsmaxstrikedb1a','username':'awsmaxstrikeuser1a','password':'awsmaxstrikeuPwD1ao%'}, #一个mongodb 用来存储游戏数据
        'log_mongodb':{'host':'172.31.18.30','port':27017,'db':'logawsmaxstrikedb1a','username':'logawsmaxstrikeuser1a','password':'logawsmaxstrikeuPWd1oa%'},
        'secondary_log_mongodb':{'host':'172.31.25.7','port':27017,'db':'logawsmaxstrikedb1a','username':'logawsmaxstrikeuser1aOcdata','password':'logawsmaxstrikeuPw2oa&oCdata'},
        },
     '5':{#ios国内pp91正式版
        'redis':[{'host':'10.160.19.253','port':6379,'db':'0'}],  #一组redis 用来存储游戏数据
        'top_redis':{'host':'10.160.19.253','port':6379,'db':'1'},  #一个redis 用来做排行榜
        'mongodb':{'host':'10.161.146.34','port':27017,'db':'maxstrikepp91db1a','username':'maxstrikepp91userdb1a','password':'MaxStRikePp91PwD1ao1a'},
        'log_mongodb':{'host':'10.161.146.34','port':27017,'db':'logmaxstrikepp91db','username':'logmaxstrikepp91user1a','password':'MaxStKePp91PwD1o1a'}, 
        'secondary_log_mongodb':{'host':'10.161.191.54','port':27017,'db':'logmaxstrikepp91db','username':'logmaxstrikepp91ocdata1a','password':'MaxStiKepP91d1o1a'}, 
        },
}

#AES KEY
AES_KEY = "e^qhim=ve^dw+gsz1^&5e(x#@uamq*-&"
APP_NAME = '风林火山国内正式服务器'
#APP_NAME = '逆转前线港台正式服务器'

#appid和平台id
OC_APP_ID = ''#逆转前线
OC_PLATFORM_ID = '1'#平台id,1-ioscn,2-iostw
#OC_PLATFORM_ID = '2'#平台id,1-ioscn,2-iostw

TOPMODELNAME = 'pvp_all_people'
LV_TOP = 'lv_top'


#港台和国服标识
APP_SEVER_ID = 'cn'

#########360app key###############
APP_KEY_360 = 'ef4c20607cff240d51d0b712109b4270'
APP_SECRET_KEY_360 = '98946959c9c124d7c74da1816ebc922e'

APP_ID_91 = '112053'
APP_KEY_91 = 'a1c38cb0fd0acdd4d954b5b7995ffcd20ea988d9c06e8a61'

BIND_MOBILE_CONF = {
    'url': 'http://si.800617.com:4400/SendSms.aspx?',
    'user': 'ctyswse-10',
    'password': '4e5951',
}

#####android客户端类型####
ANDROID_CLIENT_TYPE = ['oc_android','xiaomi','gp','360','wandoujia','17173','91','pp']
