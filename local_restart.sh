#!/bin/bash
DIR=`pwd`
PSID=`ps aux|grep $DIR|grep uwsgi |grep -v grep|wc -l`
which python
python $DIR/import_test.py
python -c "import sys; sys.path"
if [ $PSID -gt 0 ]; then
    kill -HUP `cat $DIR/logs/uwsgi.pid`
    echo "uwSGI restart done!"
else
    uwsgi --ini $DIR/local_uwsgi.ini
    echo "uwSGI start done!"
fi

