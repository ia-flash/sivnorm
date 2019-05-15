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

exec:
	$(COMPOSE) exec sivnorme bash
