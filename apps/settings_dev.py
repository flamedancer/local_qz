#-*- coding: utf-8 -*-

DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOCAL_DEBUG = False
ENVIRONMENT_TYPE = 'dev'

WALKER_POP_URL = ''
WALKER_KING_URL = ''
WALKER_APP_ID = ''

BASE_ROOT = '/alidata/sites/op/qz'
BASE_URL = 'http://sangoioscn.newsnsgame.com'

EMAIL_HOST = 'mail.touchgame.net'
EMAIL_PORT = 25
EMAIL_ACCOUNT = 'sgqz@touchgame.net'
EMAIL_PASSWORD = 'jnwUZV47i08S'
EMAIL_USE_TLS=False
EMAIL_TITLE = 'sqqz email'

ADMINS = (
    ('sgqz', EMAIL_ACCOUNT),
)
MANAGERS = ADMINS

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
)

AUTH_AGE = 16
SECRET_KEY = 'bdm@ktf0p7ee_sa7^mvg%i-d=b66jpd4qqomhb%upzg^s*05#v'
SIG_SECRET_KEY = 'e#!(MO4gfu!^392)_()rm3'
#tapjoy key
TAPJOY_KEY = 'jJw4Pw2ZEnECxiNKjpd1'

#platform infomation
QQ_APP_ID = '801446107'

SINA_APP_ID = '3236539424'#'1399456723'

FB_APP_ID = '294879773941101'
FB_SECRET_KEY = '8c7b1603dfc54c0938647d5f832f0bb2'

#PDC_SETTINGS
PDC_SERVER = "127.0.0.1:8008"
PDC_ID = "1"


CACHE_PRE = "qz_"

###############################################
#scribe config
###############################################
STATS_SWITCH = True
SCRIBE_SERVER='127.0.0.1'
SCRIBE_PORT=8250
CATEGORY_PREFIX='qz_gf'

#########################################

LV_TOP = "lv_top"
#storage config
STORAGE_INDEX = '1'
STORAGE_CONFIG = {
    "1":{
        'redis':[{'host':'10.200.55.32','port':6394,'db':'0'}],  #一组redis 用来存储游戏数据
        'realtime_pvp_redis':{'host':'10.200.55.32','port':6394,'db':'1'},  #一组redis 用来存储游戏数据
        'top_redis':{'host':'10.200.55.32','port':6394,'db':'15'},  #一个redis 用来做排行榜
        'mongodb':{'host':'10.200.55.32','port':27017,'db':'qz_op_db','username':'qzstgdyg','password':'w22cBor99yYh7E3F7'}, #一个mongodb 用来存储游戏数据
        'log_mongodb':{'host':'10.200.55.32','port':27017,'db':'qz_op_db','username':'qzstgdyg','password':'w22cBor99yYh7E3F7'},
    },
}

#AES KEY
AES_KEY = "e^qhim=ve^dw+gsz1^&5e(x#@uamq*-&"
APP_NAME = '三国Q传运营测试服务器'

#appid和平台id
OC_APP_ID = ''#逆转前线
OC_PLATFORM_ID = '61'#IOS平台

GAME_UID_KEY = 'oneclickgameuidkey'
GAME_UID_MIN = 100212343 
#首冲翻倍标志，港台版本是False，国内是True
FIRST_CHARGE = False
#########360app key###############
APP_KEY_360 = 'ef4c20607cff240d51d0b712109b4270'
APP_SECRET_KEY_360 = '98946959c9c124d7c74da1816ebc922e'

#updated on 2014/10/22 testing environment
APP_ID_91 = '100010'
APP_KEY_91 = 'C28454605B9312157C2F76F27A9BCA2349434E546A6E9C75'

#港台和国服标识
APP_SEVER_ID = 'cn'
#####android客户端类型####
ANDROID_CLIENT_TYPE = ['oc_android','xiaomi','gp','360','wandoujia','17173','91','pp']

# mycard settings
## 测试
#MYCARD_FACID = "GFD1410"
#MYCARD_KEY1 = "mycardwanco"
#MYCARD_KEY2 = "CE2b1zQL6"
#正式
MYCARD_FACID = "GFD01197"
MYCARD_KEY1 = "mycardwanco"
MYCARD_KEY2 = "CE2b1zQL6"

# 实时pvp分服配置
REAL_PVP_ALL_SERVERS = ["10.200.55.32:9041"]
REAL_PVP_SUBAREA_SERVER_CONF = {
    "1":  ["10.200.55.32:9041"],
    "2":  ["10.200.55.32:9041"],
    "3":  ["10.200.55.32:9041"],
    "4":  ["10.200.55.32:9041"],
    "5":  ["10.200.55.32:9041"],
}
