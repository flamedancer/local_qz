#-*- coding: utf-8 -*-

DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOCAL_DEBUG = False
ENVIRONMENT_TYPE = 'dev'
# 服务器标示符 港台和国服标识
APP_SEVER_ID = 'cn'
# admin页面显示主题
APP_NAME = '幻世神姬开发服务器'
# android客户端类型   不在此列的都极为ios客户端
ANDROID_CLIENT_TYPE = ['oc_android','xiaomi','gp','360','wandoujia','17173','91','pp']



WALKER_POP_URL = ''
WALKER_KING_URL = ''
WALKER_APP_ID = ''

BASE_ROOT = '/home/hvgc/new_qz'
BASE_URL = 'http://139.196.31.214:8003'

#  报错邮件配置
EMAIL_HOST = 'honvue.com'
# 多少封邮件后， 发送短信提醒
MOBILE_ERROR_NUM = 30
EMAIL_PORT = 25
EMAIL_ACCOUNT = 'chen.guo@honvue.com'
EMAIL_PASSWORD = 'flamedancer070613'
EMAIL_USE_TLS=False
EMAIL_TITLE = 'ACG ERROR email'
ADMINS = (
    ('chen.guo', EMAIL_ACCOUNT),
)
MANAGERS = ADMINS

# 通用配置
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

ROOT_URLCONF = 'apps.urls'
TEMPLATE_DIRS = (
    BASE_ROOT + '/apps/templates',
)

INSTALLED_APPS = (
    'apps.admin',
    'apps.common',
    'django.contrib.humanize', #to use intcomma, show integer with ","
)


# **重要 使用app.pier 缓存models
PIER_USE = True

# **重要  appid和平台id
OC_APP_ID = ''  #  生成uid的前缀
OC_PLATFORM_ID = '1' #  生成uid的前缀

# **重要 redis缓存字段前缀
CACHE_PRE = "qzper_"

# **重要 请求的时间戳超过30秒  不处理
AUTH_AGE = 30
# **重要
SECRET_KEY = 'bdm@ktf0p7ee_sa7^mvg%i-d=b66jpd4qqomhb%upzg^s*05#v'
# **重要
SIG_SECRET_KEY = 'e#!(MO4gfu!^392)_()rm3'
# **重要 使用的等级排行榜 名字
LV_TOP = "lv_top"
# **重要 storage config 此服 使用的数据库配置 index
STORAGE_INDEX = '1'
# **重要 所有服 数据库配置
STORAGE_CONFIG = {
    '1':{
            'redis':[{'host':'127.0.0.1','port':6379,'db':'0'}],  #一组redis 用来存储游戏数据
            'realtime_pvp_redis':{'host':'127.0.0.1','port':6379,'db':'1'},  #一redis 用来做实时pvp使用
            'top_redis':{'host':'127.0.0.1','port':6379,'db':'3'},  #一个redis 用来做排行榜
            'mongodb':{'host':'127.0.0.1','port':27017,'db':'acg','username':'','password':''}, #一个mongodb 用来存储游戏数据
            'log_mongodb':{'host':'127.0.0.1','port':27017,'db':'acglog','username':'','password':''},
            'secondary_log_mongodb':{'host':'127.0.0.1','port':27017,'db':'acglog','username':'','password':''}, 
        },
}

# 实时pvp分服配置
REAL_PVP_ALL_SERVERS = ["139.196.31.214:9040"]
REAL_PVP_SUBAREA_SERVER_CONF = {
    "1":  ["139.196.31.214:9040"],
}

"""  暂时不用的配置

#tapjoy key  (未知配置)
# TAPJOY_KEY = 'jJw4Pw2ZEnECxiNKjpd1'

#platform infomation
# QQ_APP_ID = '801446107'

# SINA_APP_ID = '3236539424'#'1399456723'

# FB_APP_ID = '294879773941101'
# FB_SECRET_KEY = '8c7b1603dfc54c0938647d5f832f0bb2'

#PDC_SETTINGS
# PDC_SERVER = "127.0.0.1:8008"
# PDC_ID = "1"


###############################################
#scribe config
###############################################
# STATS_SWITCH = True
# SCRIBE_SERVER='127.0.0.1'
# SCRIBE_PORT=8250
# CATEGORY_PREFIX='qz_gf'

#########################################


#AES KEY
# AES_KEY = "e^qhim=ve^dw+gsz1^&5e(x#@uamq*-&"

#########360app key###############
APP_KEY_360 = 'ef4c20607cff240d51d0b712109b4270'
APP_SECRET_KEY_360 = '98946959c9c124d7c74da1816ebc922e'

#updated on 2014/10/22 testing environment
APP_ID_91 = '100010'
APP_KEY_91 = 'C28454605B9312157C2F76F27A9BCA2349434E546A6E9C75'


#正式
MYCARD_FACID = "GFD01197"
MYCARD_KEY1 = "mycardwanco"
MYCARD_KEY2 = "CE2b1zQL6"


"""