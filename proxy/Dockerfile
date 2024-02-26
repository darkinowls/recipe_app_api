FROM nginxinc/nginx-unprivileged:1.20-alpine
LABEL maintainer="darkinowls.web.app"

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV APP_HOST=app
ENV APP_PORT=9000

USER root

RUN mkdir -p /vol/static
RUN chmod -R 755 /vol
RUN touch /etc/nginx/conf.d/default.conf
RUN chown -R nginx:nginx /etc/nginx
RUN chmod +x /run.sh

VOLUME /vol/static

RUN mkdir /cert
RUN apk add --no-cache openssl
RUN openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout /cert/domain.key -out /cert/domain.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=example.com"
RUN chmod -R 755 /cert
RUN chown -R nginx:nginx /cert

COPY favicon.ico /vol/static/images/favicon.ico

USER nginx

CMD /run.sh

