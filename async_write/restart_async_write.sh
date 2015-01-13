#!/bin/bash
BASEDIR=$(dirname $(readlink -f $0))
$BASEDIR/stop_async_write.sh && $BASEDIR/start_async_write.sh

