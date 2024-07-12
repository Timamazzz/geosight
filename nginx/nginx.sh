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

# Запуск nginx
exec nginx -g 'daemon off;'
