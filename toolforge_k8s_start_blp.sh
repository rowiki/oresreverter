#!/bin/bash

set -x

#python3 -m pip install --upgrade pip "setuptools>=49.4.0, !=50.0.0, <50.2.0" wheel requests
python3 -m pip install -r /data/project/.shared/pywikibot/core_stable/requirements.txt

cd /data/project/patrocle/oresreverter
export PYTHONPATH=/data/project/.shared/pywikibot/core_stable:$PYTHOPATH
ls -l /data/project/.shared/pywikibot/core_stable

python3 talkpage/blp.py
