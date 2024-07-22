FROM nginx:latest

RUN apt-get update && \
    apt-get install -y certbot python3-certbot-nginx wget lsof dnsutils

#RUN mkdir -p /etc/letsencrypt
#
#RUN wget https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf -O /etc/letsencrypt/options-ssl-nginx.conf && \
#    wget https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem -O /etc/letsencrypt/ssl-dhparams.pem

COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./nginx.sh /nginx.sh

RUN chmod +x /nginx.sh

ENTRYPOINT ["/nginx.sh"]
