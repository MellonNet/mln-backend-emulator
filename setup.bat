@echo off
set -e exit
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py import_mln_xml static/editorial-redux-v6.xml
python manage.py createsuperuser
python manage.py runserver
