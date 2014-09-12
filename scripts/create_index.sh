#!/bin/bash
DIR=/alidata/sites/stg/MaxStrike/apps/oclib/scripts
export PYTHONPATH=/alidata/sites/stg/MaxStrike
export DJANGO_SETTINGS_MODULE=apps.settings_stg
python $DIR/indexer.py qa -f $DIR/maxstrike.py
