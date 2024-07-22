#!/bin/bash

# Проверка наличия сертификатов
if [ ! -f /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ]; then
    echo "Сертификаты не найдены, получение новых..."
    certbot certonly --nginx --agree-tos --email ${EMAIL} -d ${DOMAIN}
else
    echo "Сертификаты уже существуют."
fi

# Обновление сертификатов при необходимости
certbot renew --quiet
