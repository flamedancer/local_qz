#-*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

def msg_back(msg):
  return HttpResponse(msg)

def render_back(request,url):
  return render_to_response(url, {}, context_instance = RequestContext(request))

def alert_back(msg,url):
  strv = '<script>alert("'+ msg +'");window.location="'+ url +'";</script>'
  return HttpResponse(strv)

def go_back(msg):
  return HttpResponse('<script>alert("' + msg + '");window.history.go(-1);</script>')

def parent_back(msg,url):
  strv = '<script>alert("'+ msg +'");window.parent.location="'+ url +'";</script>'
  return HttpResponse(strv)
