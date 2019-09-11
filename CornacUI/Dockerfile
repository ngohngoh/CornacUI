FROM python:3.6-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
 gfortran \
 nginx \
 supervisor \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd -r app && useradd -r -g app -M app \
 && rm /etc/nginx/sites-enabled/default \
 && touch /var/run/nginx.pid \
 && chown app:app /var/run/nginx.pid \
 && chown -R app:app /var/lib/nginx/ \
 && chown -R app:app /var/log/nginx \
 && chown -R app:app /var/log/supervisor

RUN pip install uwsgi

COPY docker/nginx.conf /etc/nginx/
COPY docker/app.conf /etc/nginx/conf.d/
COPY docker/uwsgi.ini /etc/uwsgi/
COPY docker/supervisord.conf /etc/

COPY --chown=app:app . /project
RUN rm -rf /project/docker

RUN pip install -r /project/requirements.txt \
 && rm -r /root/.cache

COPY docker/shutdown.sh /

RUN chmod +x /shutdown.sh

USER app
WORKDIR /project

ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
