#!/bin/bash
echo "Creating Migrations..."
python manage.py makemigrations --noinput
echo ====================================

echo "Starting Migrations..."
python manage.py migrate --noinput
echo ====================================

echo "Collecting Static files..."
python manage.py collectstatic --noinput
echo ====================================

echo "Starting Server..."
gunicorn geosight.wsgi:application --bind 0.0.0.0:8000