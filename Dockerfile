#######################
# Step 1: Base target #
#######################
FROM python:3.7 as dev

WORKDIR /app

COPY requirements.txt /app
COPY setup.py /app
COPY sivnorm /app/sivnorm
COPY aws_lambda /app/aws_lambda
COPY tests /app/tests
COPY docs /app/docs
COPY dss /app/dss

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

LABEL traefik.enable="true"
LABEL traefik.http.routers.sivnorm.entrypoints="http"
LABEL traefik.http.routers.sivnorm.rule="PathPrefix(`/sivnorm`) || PathPrefix(`/swaggerui`)"
LABEL traefik.http.services.sivnorm.loadbalancer.server.port="5000"

################################
# Step 2: "production" target #
################################
