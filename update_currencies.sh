#!/bin/bash
cd /home/bvermeulen/Python/Django/howdimain-localhost
source ./venv/bin/activate
python update_currencies.py
deactivate
