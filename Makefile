# The Makefile defines all builds/tests steps

# include .env file
include docker/conf.list

# compose command to merge production file and and dev/tools overrides
COMPOSE?=docker-compose -p $(PROJECT_NAME) -f docker-compose.yml

export COMPOSE
export APP_PORT
export no_proxy
export http_proxy
export DSS_PATH
# this is usefull with most python apps in dev mode because if stdout is
# buffered logs do not shows in realtime
PYTHONUNBUFFERED=1
export PYTHONUNBUFFERED

dev:
	$(COMPOSE) up

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) stop

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs --tail 50 -f

nohup:
	nohup python3 sivnorm/app.py > output.log &

docs/html:
	$(COMPOSE) exec sivnorme make -C /app/docs html

docs: docs/html
	echo "Docs"

exec:
	$(COMPOSE) exec sivnorme bash

test:
	$(COMPOSE) exec sivnorme pytest tests/check.py

layer_clean:
	sudo rm -rf ./layers

layer_dir: layer_clean
	mkdir -p layers/levenshtein/python

layer_build: layer_dir
	$(COMPOSE) exec sivnorme pip3 install python-Levenshtein==0.12.0 vertica-python==0.9.0 Unidecode==1.0.23 fuzzywuzzy==0.17.0 -t layers/levenshtein/python
	cd layers/levenshtein; zip -r levenshtein.zip python; cd ../..;

layer_publish: layer_build
	aws lambda publish-layer-version --layer-name levenshtein --zip-file fileb://layers/levenshtein/levenshtein.zip --compatible-runtimes python3.7

sam_build:
	sam build

sam_local:
	sam local start-api

sam_package:
	sam package --template-file template.yaml --s3-bucket iaflash --output-template-file packaged.yaml

sam_deploy:
	aws cloudformation deploy --template-file packaged.yaml --stack-name aws-sivnorm

sam_event_generate:
	sam local generate-event apigateway aws-proxy --body "" --path "clean" --method GET > api-event.json

sam_event_invoke:
	sam local invoke -e api-event.json CleanFunction
