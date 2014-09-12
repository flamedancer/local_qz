#-*- coding: utf8 -*-
from apps.oclib.utils.sequence import next_uid
from django.conf import settings

def generate():
    return next_uid(settings.OC_APP_ID,settings.OC_PLATFORM_ID)

