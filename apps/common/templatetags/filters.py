#-*- coding: utf-8 -*-
from django import template

register = template.Library()

def star(para):
    para = int(para)
    return '★' * para
register.filter('star', star)
