BASE_DIR=/alidata/sites/stg/MaxStrike/async_write
DIR=$BASE_DIR/client
PID=`ps aux |grep $DIR |grep $DIR/async_write.py |grep -v grep |awk '{print $2}'`
for i in $PID
do
        `/bin/kill -9 $i`
done

