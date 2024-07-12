#!/bin/sh
# Установка сертификата
apt-get update
apt-get install -y certbot python3-certbot-nginx

# Остановка текущего процесса nginx, если он запущен
nginx -s stop

# Запуск временного nginx для проверки сертификата
nginx

# Получение сертификата
certbot certonly --nginx --agree-tos --email ваш@адрес.почты -d app.geosight.ru

# Остановка временного nginx
nginx -s stop

# Отображение содержимого файла конфигурации
cat /etc/nginx/nginx.conf

apt-get install -y lsof
apt-get install -y dnsutils

# Создаем директорию для объединенной статики
mkdir -p /var/www/geosight/static

# Копируем статику Django
cp -r /var/www/geosight/django_static/* /var/www/geosight/static/

# Копируем статику React, заменяя файлы, если они уже существуют
cp -r /var/www/geosight/front/static/* /var/www/geosight/static/

# Запуск nginx
exec nginx -g 'daemon off;'
