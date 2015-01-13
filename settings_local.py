#-*- coding: utf-8 -*-

DEBUG = True #False
ALLOWED_HOSTS = ['127.0.0.1']
TEMPLATE_DEBUG = DEBUG
LOCAL_DEBUG = False
ENVIRONMENT_TYPE = 'local'

WALKER_POP_URL = ''
WALKER_KING_URL = ''
WALKER_APP_ID = ''

BASE_ROOT = '/Users/gc/chen/mysite/local_qz'
BASE_URL = 'http://maxstrikecn.negaplay.com'
#BASE_ROOT = '/data/sites/MaxStriketw'
#BASE_URL = 'http://maxstrikecn.nega777.com'

ADMINS = (
    # ('lei.li', 'maxstrike_fdios_b121212k_error@touchgame.net'),
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
STORAGE_INDEX = '0'#国服
#STORAGE_INDEX = '4'#港台
#STORAGE_INDEX = '5'#pp91

STORAGE_CONFIG = {
    '0':{
            'redis':[{'host':'127.0.0.1','port':6379,'db':'0'}],  #一组redis 用来存储游戏数据
            'realtime_pvp_redis':{'host':'127.0.0.1','port':6379,'db':'3'},  #一redis 用来做实时pvp使用
            'mongodb':{'host':'127.0.0.1','port':27017,'db':'test','username':'','password':''}, #一个mongodb 用来存储游戏数据
            'top_redis':{'host':'127.0.0.1','port':6379,'db':'15'},  #一个redis 用来做排行榜
            'log_mongodb':{'host':'127.0.0.1','port':27017,'db':'test2','username':'','password':''},
            'secondary_log_mongodb':{'host':'127.0.0.1','port':27017,'db':'test','username':'','password':''}, 
        },
}

#AES KEY
AES_KEY = "e^qhim=ve^dw+gsz1^&5e(x#@uamq*-&"
APP_NAME = '本地测试'
#APP_NAME = '逆转前线港台正式服务器'

#appid和平台id
OC_APP_ID = ''#逆转前线
OC_PLATFORM_ID = '0'#平台id,1-ioscn,2-iostw
#OC_PLATFORM_ID = '2'#平台id,1-ioscn,2-iostw

LV_TOP = 'lv_top'
#首冲翻倍标志，港台版本是False，国内是True
FIRST_CHARGE = True

#港台和国服标识
APP_SEVER_ID = 'cn'

#########360app key###############
APP_KEY_360 = 'ef4c20607cff240d51d0b712109b4270'
APP_SECRET_KEY_360 = '98946959c9c124d7c74da1816ebc922e'

APP_ID_91 = '112053'
APP_KEY_91 = 'a1c38cb0fd0acdd4d954b5b7995ffcd20ea988d9c06e8a61'

#####android客户端类型####
ANDROID_CLIENT_TYPE = ['oc_android','xiaomi','gp','360','wandoujia','17173','91','pp']



# 实时pvp分服配置
REAL_PVP_ALL_SERVERS = ["127.0.0.1:9040"]
REAL_PVP_SUBAREA_SERVER_CONF = {
    "1":  ["127.0.0.1:9040"],
    "2":  ["127.0.0.1:9040"],
    "3":  ["127.0.0.1:9040"],
    "4":  ["127.0.0.1:9040"],
    "5":  ["127.0.0.1:9040"],
}
