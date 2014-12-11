#-*- coding: utf-8 -*-

import django
if django.get_version() <= '1.3.1': 
    from django.conf.urls.defaults import include, patterns, url
elif django.get_version() >= '1.6.0': 
    from django.conf.urls import include, patterns, url    #Django 1.6
from django.conf import settings

urlpatterns = patterns('',
    url(r'^admin/', include('apps.admin.urls'), name = "admin"),
)

#基础页面跳转配置
urlpatterns += patterns('apps.views.main',
    url(r'^subareas_conf/$', 'subareas_conf', name='subareas_conf'),
    url(r'^index/$', 'index', name='index'),
    url(r'^api/$', 'api', name='api'),
    url(r'^account_bind/$', 'account_bind', name='account_bind'),
    url(r'^get_access_token/$', 'get_access_token', name='get_access_token'),

    url(r'^info/$', 'info', name='info'),
    url(r'^language_version/$', 'language_version', name='language_version'),
    url(r'^tutorial/$', 'tutorial', name='tutorial'),

    url(r'^get_card_desc_config/$', 'get_card_desc_config', name='get_card_desc_config'),
    url(r'^get_equip_desc_config/$', 'get_equip_desc_config', name='get_equip_desc_config'),
    url(r'^get_skill_desc_config/$', 'get_skill_desc_config', name='get_skill_desc_config'),
    url(r'^get_dungeon_desc_config/$', 'get_dungeon_desc_config', name='get_dungeon_desc_config'),
    url(r'^get_material_item_desc_config/$', 'get_material_item_desc_config', name='get_material_item_desc_config'),

    url(r'^crossdomain.xml$', 'crossdomain', name='crossdomain'),
    
)


urlpatterns += patterns('apps.views.charge',
    url(r'^charge_result/$', 'charge_result', name='charge_result'),
    url(r'^new_charge_result/$', 'ali_charge_result', name='ali_charge_result'),
    url(r'^google_charge_result/$', 'google_charge_result', name='google_charge_result'),

    url(r'^charge_result_360/$', 'charge_result_360', name='charge_result_360'),
    
    url(r'^mycard_sync_report/$', 'mycard_sync_report', name='mycard_sync_report'),
    url(r'^mycard_return_charge_result/$', 'mycard_return_charge_result', name='mycard_return_charge_result'),
    url(r'^mycard_serve_side_charge/$', 'mycard_serve_side_charge', name='mycard_serve_side_charge'),
    url(r'^mycard_get_authcode/$', 'mycard_get_authcode', name='mycard_get_authcode'),
    url(r'^mi_create_orderid/$', 'mi_create_orderid', name='mi_create_orderid'),
    url(r'^mi_sync_report/$', 'mi_sync_report', name='mi_sync_report'),
    url(r'^charge_result_91/$', 'charge_result_91', name='charge_result_91'),
    url(r'^charge_result_pp/$', 'charge_result_pp', name='charge_result_pp'),
    url(r'^create_orderid_91/$', 'create_orderid_91', name='create_orderid_91'),
    url(r'^pp_create_orderid/$', 'pp_create_orderid', name='pp_create_orderid'),
)


urlpatterns += patterns('',
    (r'^images/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.MEDIA_ROOT}),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.STATIC_ROOT}),
)


urlpatterns += patterns('',
    url(r'^(?P<path>.*)$', 'apps.templates_handler', name='static_handler'),
)


handler404 = 'apps.views.defaults.page_not_found'
handler500 = 'apps.views.defaults.server_error'
