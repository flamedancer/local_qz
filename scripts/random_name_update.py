#-*- coding: utf-8 -*-
import sys, os, time, traceback, datetime,random
from pymongo import MongoClient
cur_dir = os.path.dirname(os.path.abspath(__file__))
#sys.path.insert(0, os.path.join(cur_dir, ".."))
sys.path.insert(0, cur_dir)

today = datetime.date.today()
today_str = str(today)

MONGO_CONF = {
    'host': '10.200.55.32',
    'port': 27017,
    'db': 'maxstrike',
    'username': '',
    'password': ''
}

if MONGO_CONF['username'] and MONGO_CONF['password']:
    auth = "%(username)s:%(password)s@" % dict(username=MONGO_CONF['username'],
                                           password=MONGO_CONF['password'])
else:
    auth = ''

host = "mongodb://%(auth)s%(host)s:%(port)s/%(db)s" % \
    dict(auth=auth,
        host=MONGO_CONF['host'],
        port=MONGO_CONF['port'],
        db=MONGO_CONF['db'])
    
max_pool_size = 10
document_class = dict
tz_aware = True

conn = MongoClient(host=host,port=MONGO_CONF['port'],max_pool_size=max_pool_size,\
                          document_class=document_class,tz_aware=tz_aware)

db = conn[MONGO_CONF['db']]
collect_random_names = db['random_names']
collect_random_names.ensure_index('name')
collect_random_names.ensure_index('random')
collect_random_code = db['random_code']
#-------------------------------------------------------------------------------
def main():
    f = open(cur_dir+'/%s.log' % today_str,'w')
    #while True:
    try:
        update_random_names(f)
    except:
        f.write('=='*30+os.linesep)
        f.write('err time: '+str(datetime.datetime.now())+os.linesep)
        f.write('--'*30+os.linesep)
        traceback.print_exc(file=f)
        f.write('=='*30+os.linesep)
    f.close()
    
def update_random_names(f):
    count = collect_random_names.count()
    print 'collect_random_names',count
    conf_file = open(cur_dir+'/random_name_conf.py','r')
    random_name_config = eval(conf_file.read())
    total_count = 20000000
    #少于1000万时，补充名字
    if count < total_count:
        will_insert_cnt = total_count-count
        insert_cnt = 0
        insert_values = []
        if collect_random_code.count()<=0:
            collect_random_code.insert({'part1':'001','part2':'001','part3':'000'})
        random_code = collect_random_code.find()[0]
        print 'random_code',random_code
        part1 = int(random_code['part1'])
        part1_idx = random_code['part1']
        part2 = int(random_code['part2'])
        part3 = int(random_code['part3'])
        part1_ls = map(lambda x:int(x),random_name_config['1'])
        part2_ls = map(lambda x:int(x),random_name_config['2'])
        part3_ls = map(lambda x:int(x),random_name_config['3'])
        str_p_1 = ''
        str_p_2 = ''
        str_p_3 = ''
        first_loop1 = True
        first_loop2 = True
        for p_1 in range(part1, max(part1_ls)+1):
            if insert_cnt >= will_insert_cnt:
                break
            if first_loop1:
                p2_start_index = part2
                first_loop1 = False
            else:
                p2_start_index = 1
            for p_2 in range(p2_start_index, max(part2_ls)+1):
                if insert_cnt >= will_insert_cnt:
                    break
                if first_loop2:
                    p1_start_index = part3+1
                    first_loop2 = False
                else:
                    p1_start_index = 1
                for p_3 in range(p1_start_index, max(part3_ls)+1):
                    str_p_1 = str(p_1).rjust(3,'0')
                    str_p_2 = str(p_2).rjust(3,'0')
                    str_p_3 = str(p_3).rjust(3,'0')
                    str_name = random_name_config['1'][str_p_1]+random_name_config['2'][str_p_2]+random_name_config['3'][str_p_3]
                    insert_values.append({'name':str_name,'random':random.random()})
                    insert_cnt += 1
                    if len(insert_values)>=100000:
                        #random.shuffle(insert_values)
                        collect_random_names.insert(insert_values)
                        insert_values = []
                    if insert_cnt >= will_insert_cnt:
                        break
        if insert_values:
            #random.shuffle(insert_values)
            collect_random_names.insert(insert_values)
        if str_p_1 and str_p_2 and str_p_3:
            collect_random_code.update({'part1':part1_idx},{'part1':str_p_1,'part2':str_p_2,'part3':str_p_3})       

if __name__ == "__main__":
    main()


