#-*- coding: utf-8 -*-

from apps.oclib import app
from apps.config.game_config import game_config
from apps.common.utils import send_exception_mail,print_err

class StorageMiddleware(object):
    def process_request(self, request):
        try:
            subarea = request.REQUEST.get('subarea', '1') or '1'
            game_config.set_subarea(subarea)
            game_config.reload_config()
            app.pier.clear()
        except:
            print_err()
            send_exception_mail(request)

    def process_response(self, request, response):
        try:
            app.pier.save()
        except:
            print_err()
            send_exception_mail(request)
        return response
