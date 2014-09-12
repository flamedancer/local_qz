# -*- coding: utf-8 -*-
from django.template import RequestContext
from django.template.loader import get_template
from django.http import HttpResponse

def templates_handler(request, path):
    '''
    '''
    try:
        template = get_template(path)
        context = RequestContext(request)
        html = template.render(context)
        return HttpResponse(html)
    except:
        return HttpResponse('')
