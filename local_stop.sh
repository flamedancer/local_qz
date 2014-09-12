#!/bin/bash
DIR=`pwd`
PID=`ps aux |grep $DIR |grep uwsgi |grep -v grep |awk '{print $2}'`
for i in $PID
do
        rm -f $DIR/logs/uwsgi.pid
        `/bin/kill -9 $i`
done
echo "uwSGI stop done!"

