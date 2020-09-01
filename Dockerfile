#######################
# Step 1: Base target #
#######################
FROM python:3.7 as dev

ARG APP_PORT

WORKDIR /app

COPY requirements.txt /app
COPY setup.py /app
COPY sivnorm /app/sivnorm
COPY aws_lambda /app/aws_lambda
COPY tests /app/tests
COPY docs /app/docs
COPY dss /app/dss

RUN pip install --no-cache-dir -r requirements.txt

# Expose the listening port of your app
EXPOSE ${APP_PORT}

LABEL traefik.enable="true"
LABEL traefik.http.routers.sivnorm.entrypoints="http"
LABEL traefik.http.routers.sivnorm.rule="PathPrefix(`/sivnorm`) || PathPrefix(`/swaggerui`)"
LABEL traefik.http.services.sivnorm.loadbalancer.server.port=${APP_PORT}

################################
# Step 2: "production" target #
################################
