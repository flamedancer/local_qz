#!/bin/bash
BASE_DIR=$(dirname $(readlink -f $0))
DIR=$BASE_DIR/client

PID=`ps aux |grep "$DIR/async_write.py" |grep -v grep |awk '{print $2}'`

echo "Processses to kill: $PID"

for i in $PID
do
        `/bin/kill -9 $i`
done

