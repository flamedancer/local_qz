# -*- encoding: utf-8 -*-  

def process_response(response):
    #"""支持ajax跨站访问
    #"""
    response['Access-Control-Allow-Origin'] = '*' 
    response['Access-Control-Allow-Methods'] = 'POST, GET, '
    response['Access-Control-Allow-Headers'] = '*, X-Requested-With, X-Prototype-Version, X-CSRF-Token, Content-Type' 
    response['Access-Control-Max-Age'] = '1728000'
    
    return response