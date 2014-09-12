#-*- coding: utf-8 -*-

DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOCAL_DEBUG = False
ENVIRONMENT_TYPE = 'stg'

WALKER_POP_URL = ''
WALKER_KING_URL = ''
WALKER_APP_ID = ''

BASE_ROOT = '/alidata/sites/stg/MaxStrike'
BASE_URL = 'http://sangoioscn.newsnsgame.com'

ADMINS = (
    #('jinming.zhang', 'sg_error@touchgame.net'),
)

MANAGERS = ADMINS

EMAIL_HOST = 'mail.touchgame.net'
EMAIL_PORT = 25
EMAIL_USE_TLS=False

TIME_ZONE = 'Asia/Shanghai'
LANGUAGE_CODE = 'ja'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

MEDIA_ROOT = BASE_ROOT + '/static/images'
MEDIA_URL = BASE_URL + '/images/'

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
)

AUTH_AGE = 12
SECRET_KEY = 'bdm@ktf0p7ee_sa7^mvg%i-d=b66jpd4qqomhb%upzg^s*05#v'
SIG_SECRET_KEY = 'e#!(MO4gfu!^392)_()rm3'
#tapjoy key
TAPJOY_KEY = 'jJw4Pw2ZEnECxiNKjpd1'

#platform infomation
QQ_APP_ID = '801214469'
QQ_APP_NAME = '逆转三国'
QQ_APP_KEY = ''
QQ_SECRET_KEY = '82dfd0d2f2f8d38ddcf62f2758fca956'

SINA_APP_ID = '1399456723'
SINA_APP_NAME = '逆转三国'
SINA_APP_KEY = ''
SINA_SECRET_KEY = 'aa0f120ce951b7c8bb3dc8ab5598d3f0'

FB_APP_ID = '294879773941101'
FB_SECRET_KEY = '8c7b1603dfc54c0938647d5f832f0bb2'

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
STORAGE_CONFIG = {
    'redis':[{'host':'localhost','port':6379,'db':'0'},
             {'host':'localhost','port':6379,'db':'1'},
             {'host':'localhost','port':6379,'db':'2'}],  #一组redis 用来存储游戏数据
    'mongodb':{'host':'localhost','port':27017,'db':'maxstrike','username':'','password':''}, #一个mongodb 用来存储游戏数据
    'top_redis':{'host':'localhost','port':6379,'db':'15'},  #一个redis 用来做排行榜
    'log_mongodb':{'host':'localhost','port':27017,'db':'maxstrike_log','username':'','password':''},  #一个momgodb 用来存储log数据
}

#AES KEY
AES_KEY = "e^qhim=ve^dw+gsz1^&5e(x#@uamq*-&"
APP_NAME = '逆转前线测试服务器'


TOPMODELNAME = 'pvp_all_people_dev'
