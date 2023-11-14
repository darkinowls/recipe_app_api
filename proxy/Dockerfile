FROM nginxinc/nginx-unprivileged:1.20-alpine
LABEL maintainer="darkinowls.web.app"

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000

USER root

RUN mkdir -p /vol/static
RUN chmod -R 755 /vol
RUN touch /etc/nginx/conf.d/default.conf
RUN chown -R nginx:nginx /etc/nginx
RUN chmod +x /run.sh

VOLUME /vol/static

USER nginx

CMD /run.sh

