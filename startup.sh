#!/bin/sh

python manage.py migrate
python manage.py runsslserver 0.0.0.0:8000