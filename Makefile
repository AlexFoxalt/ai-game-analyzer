COMPOSE := docker compose
SERVICE := app

.PHONY: build up down restart logs ps pull update redeploy

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart $(SERVICE)

logs:
	$(COMPOSE) logs -f --tail=200 $(SERVICE)

ps:
	$(COMPOSE) ps

pull:
	$(COMPOSE) pull

update: pull build up

redeploy:
	git pull
	$(COMPOSE) up -d --build
