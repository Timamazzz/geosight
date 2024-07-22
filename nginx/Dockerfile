FROM nginx:latest

# Установка необходимых пакетов
RUN apt-get update && \
    apt-get install -y certbot python3-certbot-nginx wget lsof dnsutils

# Копирование конфигурационных файлов и скриптов
COPY ./nginx.conf /etc/nginx/nginx.conf

# Копирование скрипта для получения сертификатов
COPY ./init-letsencrypt.sh /init-letsencrypt.sh
RUN chmod +x /init-letsencrypt.sh

# Установка переменных окружения для Certbot
ENV EMAIL=geosight@email.com
ENV DOMAIN=app.geosight.ru

# Запуск скрипта и nginx
CMD ["/bin/bash", "-c", "/init-letsencrypt.sh && nginx -g 'daemon off;'"]
