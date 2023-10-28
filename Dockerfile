FROM python:3.9-alpine3.13
LABEL maintainer="darkinowls.web.app"

ENV pythonunbuffered 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv ./venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ] ; \
      then ./venv/bin/pip install -r /tmp/requirements.dev.txt ;  \
    fi && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django_user

ENV PATH="/app/.venv/bin:$PATH"

USER django_user
