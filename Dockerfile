#######################
# Step 1: Base target #
#######################
FROM python:3.7 as dev

ARG APP_PATH
ARG APP_PORT

WORKDIR /${APP_PATH}

COPY LICENSE.md ./
COPY README.md ./
COPY requirements.txt ./
COPY setup.py ./
COPY config.ini ./

VOLUME /${APP_PATH}/sivnorm
VOLUME /${APP_PATH}/aws_lambda
VOLUME /${APP_PATH}/tests
VOLUME /${APP_PATH}/dss
VOLUME /${APP_PATH}/docs

RUN pip install --no-cache-dir -r requirements.txt

# Expose the listening port of your app
EXPOSE ${APP_PORT}

LABEL traefik.enable="true"
LABEL traefik.http.routers.sivnorm.entrypoints="http"
LABEL traefik.http.routers.sivnorm.rule="PathPrefix(`/sivnorm`) || PathPrefix(`/swaggerui`)"
LABEL traefik.http.services.sivnorm.loadbalancer.server.port=${APP_PORT}

CMD ["python","sivnorm/app.py"]

################################
# Step 2: "production" target #
################################
FROM dev as prod

ADD aws_lambda ./aws_lambda
ADD docs ./docs
ADD dss ./dss
ADD sivnorm ./sivnorm
ADD tests ./tests
COPY LICENSE.md ./
COPY README.md ./
COPY requirements.txt ./
COPY setup.py ./
COPY config.ini ./

CMD ["python","sivnorm/app.py"]
