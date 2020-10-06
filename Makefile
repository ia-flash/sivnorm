export no_proxy
export http_proxy
export PROJECT_NAME=iaflash
export APP = sivnorm
export APP_PATH := $(shell pwd)
export APP_PORT=5000
export APP_VERSION	:= $(shell git rev-parse HEAD | cut -c1-8)
# For local dev: BASE_MODEL_PATH=/app/dss
# For AWS lambda: BASE_MODEL_PATH=/tmp
export BASE_MODEL_PATH=/${APP}/dss
# this is usefull with most python apps in dev mode because if stdout is
# buffered logs do not shows in realtime
export PYTHONUNBUFFERED=1

dummy               := $(shell touch artifacts)
include ./artifacts

# compose command to merge production file and and dev/tools overrides
COMPOSE?=docker-compose -p $(PROJECT_NAME) -f docker-compose.yml

network:
	docker network create isolated_nw 2> /dev/null; true

dss:
	aws s3 cp s3://dss ./dss --recursive 

dev: network dss
	export EXEC_ENV=dev; $(COMPOSE) -f docker-compose-dev.yml up --build 

build: dss
	export EXEC_ENV=prod; $(COMPOSE) build

up: network dss
	export EXEC_ENV=prod; $(COMPOSE) up -d

stop:
	$(COMPOSE) stop

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs --tail 50 -f

nohup:
	nohup python3 sivnorm/app.py > output.log &

docs/html:
	$(COMPOSE) exec sivnorme python sivnorm/export_swagger.py
	$(COMPOSE) exec sivnorme make -C /${APP}/docs html

docs: docs/html
	echo "Docs"

exec:
	$(COMPOSE) exec sivnorme bash

test:
	#$(COMPOSE) exec sivnorme pytest tests/check.py
	$(COMPOSE) exec sivnorme pytest tests/

layer_clean:
	sudo rm -rf ./layers

layer_dir: layer_clean
	mkdir -p layers/levenshtein/python

layer_build: layer_dir
	$(COMPOSE) exec sivnorme pip3 install python-Levenshtein==0.12.0 requests-toolbelt==0.9.1 vertica-python==0.9.0 Unidecode==1.0.23 fuzzywuzzy==0.17.0 -t layers/levenshtein/python
	cd layers/levenshtein; zip -r levenshtein.zip python; cd ../..;

layer_publish: layer_build
	aws lambda publish-layer-version --layer-name levenshtein --zip-file fileb://layers/levenshtein/levenshtein.zip --compatible-runtimes python3.7

sam_build:
	rm -rf aws_lambda/sivnorm
	cp sivnorm aws_lambda -r;cd aws_lambda;sam build

sam_local:
	sam local start-api

sam_package:
	sam package --template-file aws_lambda/template.yaml --s3-bucket iaflash --output-template-file aws_lambda/packaged.yaml

sam_deploy:
	aws cloudformation delete-stack --stack-name sivnorm;sleep 15;\
	aws cloudformation deploy --template-file aws_lambda/packaged.yaml --stack-name sivnorm
	aws apigateway get-rest-apis

sam_event_generate:
	sam local generate-event apigateway aws-proxy --body "" --path "clean" --method GET > api-event.json

sam_event_invoke:
	sam local invoke -e api-event.json CleanFunction
