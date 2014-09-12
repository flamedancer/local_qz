# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse
def page_not_found(request):
    """404 Not Found handler.
    """
    return HttpResponse(json.dumps({'rc': 404, 'msg':'服务器繁忙'}), content_type='application/json')

def server_error(request):
    """500 Internal Server Error handler.
    """
    return HttpResponse(json.dumps({'rc': 500, 'msg':'服务器繁忙'},indent=1), content_type='application/x-javascript')
