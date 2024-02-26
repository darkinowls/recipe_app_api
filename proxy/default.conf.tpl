
    server {
        listen 80;
        listen [::]:80;

        rewrite ^ https://${host}$request_uri permanent;
    }

    # HTTPS server block
    server {
        listen 443 default_server ssl http2;
        listen [::]:443 ssl http2;

        ssl_certificate /cert/domain.crt;
        ssl_certificate_key /cert/domain.key;

        location /static/ {
            alias /vol/static/;
        }

        location / {
            uwsgi_pass ${APP_HOST}:${APP_PORT};
            include /etc/nginx/uwsgi_params;
            client_max_body_size 10M;
        }
    }

