#!/bin/bash
DIR=$(dirname $(readlink -f $0))
/bin/rm $DIR/apps/settings.py
ln -s $DIR/apps/settings_dev.py $DIR/apps/settings.py

PSID=`ps aux|grep $DIR|grep uwsgi |grep -v grep|wc -l`
/usr/local/bin/python $DIR/import_test.py
if [ $PSID -gt 0 ]; then
    kill -HUP `cat $DIR/logs/uwsgi.pid`
    echo "uwSGI restart done!"
else
    /usr/local/bin/uwsgi --ini $DIR/uwsgi.ini
    echo "uwSGI start done!"
fi