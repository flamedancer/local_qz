##-*- coding: utf8 -*-
#import time
#import datetime
#
#class TimeviewMiddleware(object):
#    def process_request(self, request):
#        self.start_time = time.time()
#
#    def process_response(self, request, response):
#        end_time = time.time()
#        path_name = request.path.strip('/').replace('/', '.')
#
#        if not hasattr(self, 'start_time'):
#            return response
#
#        exec_time = end_time - self.start_time
#        if exec_time != 0:
#            method = request.REQUEST.get('method')
#            if method is None:
#                print '%s timeit view: %s: %.3f' % (str(datetime.datetime.now()), path_name, exec_time)
#            else:
#                print '%s timeit view: %s.%s: %.3f' % (str(datetime.datetime.now()), path_name, method, exec_time)
#
#        return response