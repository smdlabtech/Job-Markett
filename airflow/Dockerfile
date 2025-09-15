ARG AIRFLOW_BASE_IMAGE=apache/airflow:3.0.2-python3.12
FROM ${AIRFLOW_BASE_IMAGE}
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         openjdk-17-jre-headless \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install psycopg==3.2.9