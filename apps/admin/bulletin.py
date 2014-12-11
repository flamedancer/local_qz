#!/usr/bin/env python
#coding=utf8
"""
login_bulletin, 登录公告, 类似Brave Frontier格式，需要存27条信息

Trying to make Brave Frontier style login bulleting: 7 msg titles in first page,
20 msg titles on "more/history" page. Each title will link to a "detail" page.

"""
from apps.oclib.model import MongoModel
import time, datetime
from django.conf import settings


class Bulletin(MongoModel):
    """
    Attributes:
        id: 0   #1: 初始公告;

        data:   [ {'time': int,  'title':'', 'img':'', 'detail':'', 
                  'detail_head_img':'', }, {}, ... ]
    """
    pk = 'id'
    fields = ['id', 'data', ]


    def __init__(self):
        self.data = []

    @classmethod
    def create(cls, id=0):
        bulletin = Bulletin()
        bulletin.id = id
        bulletin.data = []
        bulletin.put()
        return bulletin


    @classmethod
    def get_instance(cls, id=0):
        obj = super(Bulletin, cls).get(id)
        if obj is None:
            obj = cls.create(id=id)
        return obj


    def add_title(self, title='', img='', detail=''):
        
        for i in range(len(self.data)):
            if self.data[i]['title'] == title: 
                #delete old title, add new, i.e., update
                #also prevent duplicated title / duplicated mouse clicks
                del(self.data[i])
                break

        timeNow = int(time.time())
        self.data.insert(0, { 'time': timeNow, 'title':title, 'img':img,
                              'detail':detail, 'more':'' } )
        self.data = self.data[:27]

        self.put()

    def delete_title(self, title=''):
        for i in range(len(self.data)):
            if self.data[i]['title'] == title:
                del(self.data[i])
                self.put()
                return True
        return False


    def generate_html(self, online_or_preview='', id=0):
        ''' Under /static/html, make 0_notice.html, 1_notice.html .
        '''
        py_template_dir = settings.BASE_ROOT + '/apps/admin/templates/tool/py_template/'
        html_dir = settings.STATIC_ROOT + 'html/'

        display_medias = { '0': 'ipad', '1':'iphone' }
        css_file = {'0': 'ipad.css', '1': 'iphone.css'}

        f=open( py_template_dir + 'bulletin_template.htm')
        bulletin_template=f.read()
        f.close()

        f=open( py_template_dir + 'bulletin_detail_template.htm')
        detail_template = f.read()
        f.close()

        f=open( py_template_dir + 'bulletin_more_template.htm')
        more_template = f.read()
        more_template = more_template.decode('utf8')
        f.close()

        details_list = []
        for i in range( len(self.data) ):
            more_link = ''
            if self.data[i].get('more_body'):
                more_link = '<p style="text-align:right;"> <a href="#" onclick="show_div(' + str(i+1) + ');" class=bulletin_button>&lt;' + u'更多详情' + '&gt;</a> </p>'

            data = { 'img': self.data[i]['img'],
                     'title': self.data[i]['title'],
                     'title_color': self.data[i].get('title_color', 'rgb(147,54,47)'),
                     'detail': self.data[i]['detail'].replace(u'\u2028', '\n'),

                     'more_link': more_link,
                    }
            details_list +=  [ '\n<!-- 第' + str(i) + '块 开始 -->\n' + (detail_template % data).encode('utf8') + '\n<!-- 第' + str(i) + '块 结束 -->\n']


        mores_list = []
        for i in range( len(self.data) ):
            data = { 
                     'more_title': self.data[i].get('more_title', ''),
                     'more_title_color': self.data[i].get('more_title_color', ''),
                     'more_body': self.data[i].get('more_body', ''),
                     'i_div': i+1,
                    }
            mores_list +=  [ '\n<!-- 第' + str(i) + '块 更多详情 开始 -->\n' + (more_template % data).encode('utf8') + '\n<!-- 第' + str(i) + '块 更多详情 结束 -->\n']


        for dm in display_medias:
            if online_or_preview == 'online':
                f=open(html_dir + dm + '_notice_v' + str(id) + '.html', 'w')
            else:
                f=open(html_dir + dm + '_notice_preview.html', 'w')

            print >>f, ( bulletin_template % { 
                    'dm': dm,
                    'css_file': css_file[dm],
                    'display_media': display_medias[dm],
                    'display_media_index': dm,
                    'all_details': '\n\n'.join(details_list),
                    'all_mores': '\n\n'.join(mores_list),
                    'total_more_div': len(self.data),
                    } ).replace('\r\n', '\n').replace('\n', '\r\n')   
                    #Windows users only know notepad++, which merges \n to one line
            f.close()

