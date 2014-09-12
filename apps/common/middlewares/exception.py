#-*- coding: utf-8 -*-
import traceback
import datetime
from apps.common import utils

from django.http import HttpResponse
from django.conf import settings

from apps.views.defaults import server_error


class ExceptionMiddleware(object):

    def process_exception(self, request, exception):

        msg = '=='*30+'<br/>'
        msg += 'err time: '+str(datetime.datetime.now())+'<br/>'
        msg += '--'*30+'<br/>'
        msg += traceback.format_exc().replace('\n','<br/>')+'<br/>'
        msg += '--'*30+'<br/>'
        utils.print_err()
        return HttpResponse(msg)# if settings.DEBUG else server_error(request)
