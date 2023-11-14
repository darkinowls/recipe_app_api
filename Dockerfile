# Stage 1: Building the application
FROM python:3.9-alpine3.13 AS builder
LABEL maintainer="darkinowls.web.app"
ENV pythonunbuffered 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./scripts /scripts
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false

RUN python -m venv /.venv && \
    /.venv/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib-dev zlib linux-headers && \
    /.venv/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ] ; \
      then /.venv/bin/pip install -r /tmp/requirements.dev.txt ;  \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django_user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django_user:django_user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

ENV PATH="/.venv/bin:$PATH"
ENV PATH="/scripts:$PATH"

USER django_user

CMD run.sh

