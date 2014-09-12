#!/bin/bash
BASEDIR=/alidata/sites/stg/MaxStrike/async_write
DIR=$BASEDIR/client
LOGDIR=$BASEDIR/logs
mkdir -p $LOGDIR
REDIS_LIST="0"
PROCESS_NUM=1
export PYTHONPATH=$BASEDIR
for index in $REDIS_LIST;do
    for((i=0;i<$PROCESS_NUM;i++));do 
        nohup python $DIR/async_write.py $index &
    done
done


