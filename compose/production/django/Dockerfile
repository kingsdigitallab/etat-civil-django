
FROM python:3.7-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  # LDAP dependencies
  && apt-get install -y libldap2-dev libsasl2-dev ldap-utils \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN groupadd -r django && useradd --no-log-init -r -g django django

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/production.txt \
  && rm -rf /requirements

COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint
RUN chown django /entrypoint

COPY ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start
RUN chown django /start
COPY . /app

RUN chown -R django /app

USER django

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
