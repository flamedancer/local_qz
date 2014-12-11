"""
Django 1.2 template tag that supports {% elif %} branches.

Usage:

    {% if user.nick == "guest" %}
      Hello guest!
    {% elif user.nick == "admin" or user.is_admin %}
      Hello admin!
    {% elif user %}
      You are registered user
    {% else %}
      Login to site
    {% endif %}

Use it without any change in the django template!

Register new template tag:

 # in Django:
     from django.template import Library
     register = Library()
     do_if = register.tag("if", do_if)

 # in Google App Engine:
     from google.appengine.ext.webapp.template import create_template_register
     register = create_template_register()
     register.tag("if", do_if)

@author: Anton Danilchenko (http://gaeframework.com)
"""

from django.template import Library
from django.template import Node, VariableDoesNotExist
from django.template.defaulttags import TemplateIfParser
import datetime

register = Library()


class IfBranch(object):
    def __init__(self, var, node_list):
        self.var = var
        self.node_list = node_list


class IfNode(Node):
    def __init__(self, branches):
        self.branches = branches

    def __repr__(self):
        return "<If node>"

    def __iter__(self):
        for n in self.branches:
            for node in n:
                yield node

    def render(self, context):
        for n in self.branches:
            var = n.var
            if var != True:
                try:
                    var = var.eval(context)
                except VariableDoesNotExist:
                    var = None
            if var:
                return n.node_list.render(context)
                break
        return ""


@register.tag(name='if')
def do_if(parser, token):
    class Enders(list):
        def __contains__(self, val):
            return val.startswith('elif') or val in ('else', 'endif')
    
    enders = Enders()
    branches = []
    
    while True:
        contents = token.split_contents()
        bits = contents[1:]
        if contents[0] in ("if", "elif"):
            var = TemplateIfParser(parser, bits).parse()
            nodelist = parser.parse(enders)
            next_token = parser.next_token()
            branches.append(IfBranch(var, nodelist))
            token = next_token
        elif token.contents == 'else':
            nodelist = parser.parse(('endif',))
            parser.delete_first_token()
            branches.append(IfBranch(True, nodelist))
            break
        elif token.contents == 'endif':
            break

    return IfNode(branches)

#do_if = register.tag("if", do_if)


#@register.filter
#def is_in(var, obj):
#        return var in obj


#this is to sort dictionary keys: some_dic.items|sort
@register.filter(name='sort')
def listsort(value):
  if isinstance(value,dict):
    new_dict = SortedDict()
    key_list = value.keys()
    key_list.sort()
    for key in key_list:
      new_dict[key] = value[key]
    return new_dict
  elif isinstance(value, list):
    new_list = list(value)
    new_list.sort()
    return new_list
  else:
    return value
listsort.is_safe = True



#get dictionary key's value -- Django's template doesn't support by default now
@register.filter
def dictValue(a_dict, key):    
    return a_dict.get(key)  #use get, if no key, return None, not raise error


@register.filter
def print_timestamp(timestamp):
    try:
        #assume, that timestamp is given in seconds with decimal point
        ts = float(timestamp)
    except ValueError:
        return None
    return datetime.datetime.fromtimestamp(ts)
